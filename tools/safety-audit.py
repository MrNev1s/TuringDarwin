#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = [ROOT / "kext", ROOT / "include"]
MMIO_CPP = Path("kext/TuringProbe/MMIOReadOnly.cpp")
MMIO_HPP = Path("kext/TuringProbe/MMIOReadOnly.hpp")
MMIO_ALLOWED_FILES = {MMIO_CPP, MMIO_HPP}

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
    r"\bIOCommandGate\b": "command gate not authorised in v0.2",
    r"\bIOWorkLoop\b": "work loop not authorised in v0.2",
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
    r"\bunmap\s*\(": "manual mapping mutation; rely on OSPtr lifetime",
}

MMIO_ONLY_TOKENS = {
    r"\bIOMemoryMap\b": "mapping object",
    r"\bgetVirtualAddress\b": "mapped virtual address",
    r"\bkIOMapReadOnly\b": "read-only mapping option",
    r"\bOSReadLittleInt32\b": "whitelisted MMIO read primitive",
    r"->map\s*\(": "IOMemoryDescriptor mapping",
}

ALLOWED_PCI_METHODS = {
    "configRead8", "configRead16", "configRead32", "extendedConfigRead32",
    "getBusNumber", "getDeviceNumber", "getFunctionNumber",
    "getDeviceMemoryWithRegister", "getDeviceMemoryCount",
    "getDeviceMemoryWithIndex", "getPath", "getRegistryEntryID",
    "getName", "getLocation", "retain", "release",
}

ALLOWED_MMIO_OFFSETS = {0x000000, 0x000004, 0x101000}
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
                errors.append(f"{rel}:{line}: MMIO token outside dedicated module ({reason})")

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
        errors.append(f"{MMIO_CPP}: exactly one checked OSReadLittleInt32 accessor is required")
    if len(re.findall(r"\breadWhitelisted32\s*\(", mmio)) != 4:
        errors.append(f"{MMIO_CPP}: accessor must have one definition and exactly three call sites")
    if re.search(r"\b(for|while|do)\s*(?:\(|\{)", mmio):
        errors.append(f"{MMIO_CPP}: hardware MMIO module must contain no loops")
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
        errors.append(f"{MMIO_CPP}: implicit OSPtr lifetime is forbidden for third-party C++14 builds")
    if 'TPBAR0MappingReleased", mappingReleased' not in mmio:
        errors.append(f"{MMIO_CPP}: release telemetry must report the real mappingReleased state")
    if "TURINGPROBE_ENABLE_MMIO_READ" not in mmio:
        errors.append(f"{MMIO_CPP}: compile-time MMIO gate missing")

registers = texts.get(Path("include/TuringRegisters.hpp"), "")
found_offsets = {
    int(value, 16)
    for value in re.findall(r"constexpr\s+UInt32\s+k\w+Offset\s*=\s*(0x[0-9A-Fa-f]+)U", registers)
}
if found_offsets != ALLOWED_MMIO_OFFSETS:
    errors.append(
        "include/TuringRegisters.hpp: whitelist offsets must be exactly "
        "0x000000, 0x000004, and 0x101000"
    )

pbx = (ROOT / "TuringProbe.xcodeproj/project.pbxproj").read_text(encoding="utf-8")
if pbx.count("TURINGPROBE_ENABLE_MMIO_READ=1") != 2:
    errors.append("project.pbxproj: Debug and Release must both enable the compile-time MMIO gate")

if errors:
    print("SAFETY AUDIT FAILED", file=sys.stderr)
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

print("SAFETY AUDIT PASSED: v0.2.1 permits three read-only BAR0 reads and requires explicit map release")
