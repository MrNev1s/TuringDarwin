#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = [ROOT / "kext", ROOT / "include"]
MMIO_CPP = Path("kext/TuringProbe/MMIOReadOnly.cpp")
MMIO_HPP = Path("kext/TuringProbe/MMIOReadOnly.hpp")
TOP_CPP = Path("kext/TuringProbe/TopInventory.cpp")
TOP_HPP = Path("kext/TuringProbe/TopInventory.hpp")
FB_CPP = Path("kext/TuringProbe/FbMmuInventory.cpp")
FB_HPP = Path("kext/TuringProbe/FbMmuInventory.hpp")
HOST_CPP = Path("kext/TuringProbe/HostMemorySelfTest.cpp")
HOST_HPP = Path("kext/TuringProbe/HostMemorySelfTest.hpp")
MMIO_ALLOWED_FILES = {MMIO_CPP, MMIO_HPP, TOP_CPP, TOP_HPP, FB_CPP, FB_HPP}
HOST_MEMORY_ALLOWED_FILES = {HOST_CPP, HOST_HPP}

GLOBALLY_FORBIDDEN = {
    r"\bconfigWrite(?:8|16|32)\b": "PCI configuration write",
    r"\bextendedConfigWrite(?:8|16|32)\b": "extended PCI configuration write",
    r"\bsetConfigBits\b": "masked PCI configuration write",
    r"\bsetBusMasterEnable\b": "bus-master state change",
    r"\bsetMemoryEnable\b": "PCI memory-enable state change",
    r"\bsetIOEnable\b": "PCI I/O-enable state change",
    r"\benablePCIPowerManagement\b": "PCI power-management state change",
    r"\bmapDeviceMemory(?:WithIndex|WithRegister)?\b": "provider BAR mapping helper",
    r"\bIOInterruptEventSource\b": "interrupt source",
    r"\bIOFilterInterruptEventSource\b": "filtered interrupt source",
    r"\bregisterInterrupt\b": "interrupt registration",
    r"\bIODMACommand\b": "DMA command",
    r"\bIOBufferMemoryDescriptor\b": "buffer suitable for later DMA",
    r"\bIOUserClient\b": "user client surface",
    r"\bIOCommandGate\b": "command gate not authorised in v0.6.0",
    r"\bIOWorkLoop\b": "work loop not authorised in v0.6.0",
    r"\bioWrite(?:8|16|32)\b": "I/O-space write",
    r"\bIOMappedWrite(?:8|16|32|64)\b": "mapped MMIO write",
    r"\bOSWrite(?:Little|Big)Int(?:8|16|32|64)\b": "memory write primitive",
    r"\bml_phys_write\b": "physical-memory write primitive",
    r"\bsetPowerState\b": "power-state change",
    r"\bchangePowerStateTo\b": "power-state change",
    r"\brequestPowerDomainState\b": "power-domain state request",
    r"\bwriteBytes\b": "memory descriptor write",
    r"\bprepare\s*\(": "memory preparation/DMA-facing operation",
    r"\bcomplete\s*\(": "memory completion/DMA-facing operation",
}

MMIO_ONLY_TOKENS = {
    r"\bIOMemoryMap\b": "mapping object",
    r"\bgetVirtualAddress\b": "mapped virtual address",
    r"\bkIOMapReadOnly\b": "read-only mapping option",
    r"\bOSReadLittleInt32\b": "MMIO read primitive",
    r"->map\s*\(": "IOMemoryDescriptor mapping",
}

ALLOWED_PCI_METHODS = {
    "configRead8", "configRead16", "configRead32", "extendedConfigRead32",
    "getBusNumber", "getDeviceNumber", "getFunctionNumber",
    "getDeviceMemoryWithRegister", "getDeviceMemoryCount",
    "getDeviceMemoryWithIndex", "getPath", "getRegistryEntryID",
    "getName", "getLocation", "retain", "release",
}

errors = []
texts = {}

for base in SOURCE_DIRS:
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix not in {".cpp", ".hpp", ".h", ".c"}:
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        texts[rel] = text

        for pattern, reason in GLOBALLY_FORBIDDEN.items():
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: {reason}: {match.group(0)}")

        for pattern, reason in MMIO_ONLY_TOKENS.items():
            if rel in MMIO_ALLOWED_FILES:
                continue
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: MMIO token outside dedicated modules ({reason})")

        for match in re.finditer(r"\b(?:device|pciDevice_|candidate)->([A-Za-z_][A-Za-z0-9_]*)\s*\(", text):
            method = match.group(1)
            if method not in ALLOWED_PCI_METHODS:
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: unapproved IOPCIDevice method: {method}")

mmio = texts.get(MMIO_CPP, "")
if not mmio:
    errors.append(f"{MMIO_CPP}: missing dedicated MMIO module")
else:
    if len(re.findall(r"\bOSReadLittleInt32\s*\(", mmio)) != 1:
        errors.append(f"{MMIO_CPP}: exactly one identity OSReadLittleInt32 accessor is required")
    if len(re.findall(r"\breadWhitelisted32\s*\(", mmio)) != 4:
        errors.append(f"{MMIO_CPP}: identity accessor must have one definition and three call sites")
    if re.search(r"\b(?:for|while|do)\s*(?:\(|\{)", mmio):
        errors.append(f"{MMIO_CPP}: identity/mapping module must contain no loops")
    if re.search(r"\bvolatile\b", mmio):
        errors.append(f"{MMIO_CPP}: no direct volatile pointer is allowed")
    if "descriptor->map(kIOMapReadOnly)" not in mmio:
        errors.append(f"{MMIO_CPP}: mapping must explicitly request kIOMapReadOnly")
    if "IOMemoryMap *mapping = descriptor->map(kIOMapReadOnly);" not in mmio:
        errors.append(f"{MMIO_CPP}: mapping ownership must be explicit raw-pointer ownership")
    if len(re.findall(r"\bmapping->release\s*\(\s*\)\s*;", mmio)) != 1:
        errors.append(f"{MMIO_CPP}: exactly one explicit mapping->release() is required")
    if "mapping = nullptr;" not in mmio:
        errors.append(f"{MMIO_CPP}: mapping pointer must be cleared after release")
    if "auto mapping =" in mmio or "OSPtr<IOMemoryMap>" in mmio:
        errors.append(f"{MMIO_CPP}: implicit OSPtr lifetime is forbidden")
    if 'TPBAR0MappingReleased", mappingReleased' not in mmio:
        errors.append(f"{MMIO_CPP}: release telemetry must report real state")
    if "TURINGPROBE_ENABLE_MMIO_READ" not in mmio:
        errors.append(f"{MMIO_CPP}: compile-time MMIO gate missing")


top = texts.get(TOP_CPP, "")
if not top:
    errors.append(f"{TOP_CPP}: missing bounded TOP inventory module")
else:
    if len(re.findall(r"\bOSReadLittleInt32\s*\(", top)) != 1:
        errors.append(f"{TOP_CPP}: exactly one TOP OSReadLittleInt32 accessor is required")
    if len(re.findall(r"\breadTopWord32\s*\(", top)) != 2:
        errors.append(f"{TOP_CPP}: TOP accessor must have one definition and one bounded call site")
    loops = re.findall(r"for\s*\(([^)]*)\)", top)
    if len(loops) != 1 or "index < kTopTableWordCount" not in loops[0]:
        errors.append(f"{TOP_CPP}: exactly one loop bounded by kTopTableWordCount is required")
    if "kTopTableBaseOffset + index * 4U" not in top:
        errors.append(f"{TOP_CPP}: TOP reads must use the fixed 0x022700 + index*4 formula")
    if re.search(r"\b(?:while|do)\s*(?:\(|\{)", top):
        errors.append(f"{TOP_CPP}: TOP module must contain no polling/unbounded loops")
    if re.search(r"\bvolatile\b", top):
        errors.append(f"{TOP_CPP}: no direct volatile pointer is allowed")

fb = texts.get(FB_CPP, "")
if not fb:
    errors.append(f"{FB_CPP}: missing FB/MMU inventory module")
else:
    if len(re.findall(r"\bOSReadLittleInt32\s*\(", fb)) != 1:
        errors.append(f"{FB_CPP}: exactly one FB OSReadLittleInt32 accessor is required")
    if len(re.findall(r"\breadFbCapacity32\s*\(", fb)) != 2:
        errors.append(f"{FB_CPP}: FB accessor must have one definition and one call site")
    if re.search(r"\b(?:for|while|do)\s*(?:\(|\{)", fb):
        errors.append(f"{FB_CPP}: FB/MMU module must contain no loops or polling")
    if re.search(r"\bvolatile\b", fb):
        errors.append(f"{FB_CPP}: no direct volatile pointer is allowed")
    if "kNvPfbVidmemSizeOffset" not in fb:
        errors.append(f"{FB_CPP}: source-backed 0x100CE0 register constant missing")
    if "kExpectedTargetVidmemBytes" not in fb:
        errors.append(f"{FB_CPP}: exact 6 GiB target validation missing")
    if "TPMMUSourceProfile" not in fb:
        errors.append(f"{FB_CPP}: source-backed MMU metadata must be clearly labelled")
    if "TURINGPROBE_ENABLE_FB_READ" not in fb:
        errors.append(f"{FB_CPP}: dedicated compile-time FB read gate missing")
    if 'TPFBInventoryCompileGateEnabled' not in fb:
        errors.append(f"{FB_CPP}: compile-gate telemetry missing")


host = texts.get(HOST_CPP, "")
if not host:
    errors.append(f"{HOST_CPP}: missing bounded host-memory self-test module")
else:
    if len(re.findall(r"\bIOMallocAligned\s*\(", host)) != 1:
        errors.append(f"{HOST_CPP}: exactly one IOMallocAligned call is required")
    if len(re.findall(r"\bIOFreeAligned\s*\(", host)) != 1:
        errors.append(f"{HOST_CPP}: exactly one matching IOFreeAligned call is required")
    for token in (
        "IOBufferMemoryDescriptor", "IOMemoryDescriptor", "IODMACommand",
        "IOMallocContiguous", "getPhysicalSegment", "getPhysicalAddress",
        "prepare(", "complete(", "IOMappedWrite", "OSWriteLittleInt",
        "configWrite", "setBusMasterEnable",
    ):
        if token in host:
            errors.append(f"{HOST_CPP}: forbidden host-memory token: {token}")
    required_host_tokens = (
        "kHostMemoryAllocationSize", "kHostMemoryAlignment",
        "kExpectedPayloadChecksum", "TPHostMemoryPayloadReadbackMatched",
        "TPHostMemoryPrefixCanaryValidAfterWrite",
        "TPHostMemorySuffixCanaryValidAfterWrite",
        "TPHostMemoryPayloadZeroized",
        "TPHostMemoryEntireAllocationZeroBeforeFree",
        "TPHostMemoryAllocationFreed",
        "TURINGPROBE_ENABLE_HOST_MEMORY_TEST",
    )
    for token in required_host_tokens:
        if token not in host:
            errors.append(f"{HOST_CPP}: missing host-memory contract token {token}")

registers = texts.get(Path("include/TuringRegisters.hpp"), "")
expected_constants = {
    "kNvPmcBoot0Offset": 0x000000,
    "kNvPmcBoot1Offset": 0x000004,
    "kNvPextdevBoot0StrapOffset": 0x101000,
    "kTopTableBaseOffset": 0x022700,
    "kTopTableWordCount": 64,
    "kNvPfbVidmemSizeOffset": 0x100CE0,
    "kFbMmuInventoryMmioReadCount": 1,
    "kTu102MmuDmaAddressBits": 47,
    "kTu102MmuVirtualAddressBits": 49,
    "kTu102MmuKindCount": 16,
    "kTu102MmuInvalidKind": 0x07,
    "kTu102SmallPageShift": 12,
    "kTu102SmallPageKiB": 4,
    "kTu102BigPageShift": 16,
    "kTu102BigPageKiB": 64,
}
for name, expected in expected_constants.items():
    match = re.search(rf"constexpr\s+UInt32\s+{name}\s*=\s*(0x[0-9A-Fa-f]+|[0-9]+)U", registers)
    if not match or int(match.group(1), 0) != expected:
        errors.append(f"include/TuringRegisters.hpp: {name} must equal {expected:#x}")
if "kExpandedTopMmioReadCount == 67U" not in registers:
    errors.append("include/TuringRegisters.hpp: TOP expanded read count must be fixed at 67")
if "kExpandedFbMmuMmioReadCount == 4U" not in registers:
    errors.append("include/TuringRegisters.hpp: FB/MMU expanded read count must be fixed at 4")

main = texts.get(Path("kext/TuringProbe/TuringProbe.cpp"), "")
if 'bootArgumentPresent("-tdtop-read")' not in main:
    errors.append("TuringProbe.cpp: -tdtop-read gate missing")
if 'bootArgumentPresent("-tdfb-read")' not in main:
    errors.append("TuringProbe.cpp: -tdfb-read gate missing")
if "topRequested && !mmioRequested" not in main:
    errors.append("TuringProbe.cpp: -tdtop-read must require -tdmmio-read")
if "fbMmuRequested && !mmioRequested" not in main:
    errors.append("TuringProbe.cpp: -tdfb-read must require -tdmmio-read")
if "topRequested && fbMmuRequested" not in main:
    errors.append("TuringProbe.cpp: TOP and FB modes must be mutually exclusive")

pbx = (ROOT / "TuringProbe.xcodeproj/project.pbxproj").read_text(encoding="utf-8")
if pbx.count("TURINGPROBE_ENABLE_MMIO_READ=1") != 2:
    errors.append("project.pbxproj: Debug and Release must enable compile-time MMIO gate")
if pbx.count("TURINGPROBE_ENABLE_FB_READ=1") != 2:
    errors.append("project.pbxproj: Debug and Release must enable dedicated FB read gate")
if pbx.count("TURINGPROBE_ENABLE_HOST_MEMORY_TEST=1") != 2:
    errors.append("project.pbxproj: Debug and Release must enable host-memory test gate")
if "TopInventory.cpp" not in pbx or "TopInventory.hpp" not in pbx:
    errors.append("project.pbxproj: TOP inventory module is not included")
if "FbMmuInventory.cpp" not in pbx or "FbMmuInventory.hpp" not in pbx:
    errors.append("project.pbxproj: FB/MMU inventory module is not included")
if "HostMemorySelfTest.cpp" not in pbx or "HostMemorySelfTest.hpp" not in pbx:
    errors.append("project.pbxproj: host-memory self-test module is not included")
if pbx.count("MODULE_VERSION = 0.6.0") != 2:
    errors.append("project.pbxproj: module version must be 0.6.0 in both configurations")

build_sh = (ROOT / "tools/build.sh").read_text(encoding="utf-8")
if 'turingprobe_version=0.6.0' not in build_sh:
    errors.append("tools/build.sh: manifest version must be 0.6.0")
if 'mmio_fb_inventory=1x32@0x100ce0' not in build_sh:
    errors.append("tools/build.sh: FB inventory manifest entry missing")
if 'fb_compile_gate=TURINGPROBE_ENABLE_FB_READ=1' not in build_sh:
    errors.append("tools/build.sh: dedicated FB compile gate manifest entry missing")
if 'host_memory_compile_gate=TURINGPROBE_ENABLE_HOST_MEMORY_TEST=1' not in build_sh:
    errors.append("tools/build.sh: host-memory compile gate manifest entry missing")
if 'device_memory_write_whitelist=EMPTY' not in build_sh:
    errors.append("tools/build.sh: device-memory write whitelist must remain empty")


# Offline MMU research code must remain physically incapable of touching IOKit
# or an MMIO mapping. These tokens are rejected even in comments so any future
# device-facing work must be introduced through an explicit reviewed gate.
RESEARCH_REQUIRED = {
    Path("research/tu102_mmu_model.py"),
    Path("research/tu102_page_table_image.py"),
    Path("research/tu102_address_space.py"),
    Path("research/mmu_transaction_plan.py"),
    Path("research/mmu-golden-vectors.json"),
    Path("research/host_memory_model.py"),
}
RESEARCH_FORBIDDEN_TOKENS = (
    "IOMemoryMap", "IOPCIDevice", "OSReadLittleInt32", "OSWriteLittleInt32",
    "configRead32", "configWrite32", "mmap", "/dev/", "ioreg", "kmutil",
    "subprocess", "ctypes", "socket", "requests", "urllib",
)
for rel in sorted(RESEARCH_REQUIRED):
    path = ROOT / rel
    if not path.exists():
        errors.append(f"{rel}: required offline MMU research file missing")
        continue
    text = path.read_text(encoding="utf-8")
    if rel.suffix == ".py":
        for token in RESEARCH_FORBIDDEN_TOKENS:
            if token in text:
                errors.append(f"{rel}: forbidden device/network token in offline model: {token}")

if 'bootArgumentPresent("-tdhostmem-test")' not in main:
    errors.append("TuringProbe.cpp: isolated -tdhostmem-test gate missing")
if "hostMemoryRequested && mmioRequested" not in main:
    errors.append("TuringProbe.cpp: host-memory mode must reject all MMIO modes")
if 'bootArgumentPresent("-tdmmu-read")' in main or "-tdmmu-read" in main:
    errors.append("TuringProbe.cpp: no MMU hardware boot argument is authorised")

for research_name in (
    "tu102_mmu_model.py", "tu102_page_table_image.py",
    "tu102_address_space.py", "mmu_transaction_plan.py",
):
    if research_name in pbx:
        errors.append(f"project.pbxproj: offline research file must not be compiled: {research_name}")

workflow = (ROOT / ".github/workflows/build-kext.yml").read_text(encoding="utf-8")
required_workflow_tokens = (
    "research/**",
    "bash tools/run-offline-validation.sh",
    "tools/test-mmu-model.py",
    "tools/test-page-table-image.py",
    "tools/test-golden-vectors.py",
    "tools/test-address-space.py",
    "tools/test-transaction-plan.py",
    "tools/test-host-memory-model.py",
    "tools/test-host-memory-kext-contract.py",
)
validation_script = (ROOT / "tools/run-offline-validation.sh").read_text(encoding="utf-8")
for token in required_workflow_tokens:
    if token == "research/**":
        if token not in workflow:
            errors.append("build workflow: research/** changes must trigger CI")
    elif token == "bash tools/run-offline-validation.sh":
        if token not in workflow:
            errors.append("build workflow: complete validation script is not invoked")
    elif token not in validation_script:
        errors.append(f"run-offline-validation.sh: missing required suite {token}")

if 'bash "$ROOT/tools/run-offline-validation.sh"' not in build_sh:
    errors.append("tools/build.sh: complete offline validation suite must run before build")
if "mmu_hardware_whitelist=EMPTY" not in build_sh:
    errors.append("tools/build.sh: manifest must state empty MMU hardware whitelist")
if "kextutil -n" in build_sh:
    errors.append("tools/build.sh: unsupported kextutil -n check must not be used")

if errors:
    print("SAFETY AUDIT FAILED", file=sys.stderr)
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

print("SAFETY AUDIT PASSED: v0.6.0 adds isolated aligned host-memory CPU write/readback; no device-memory access")
