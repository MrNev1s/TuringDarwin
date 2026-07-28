#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = [ROOT / "kext", ROOT / "include"]
FORBIDDEN = {
    r"\bconfigWrite(?:8|16|32)\b": "PCI configuration write",
    r"\bextendedConfigWrite(?:8|16|32)\b": "extended PCI configuration write",
    r"\bsetConfigBits\b": "masked PCI configuration write",
    r"\bsetBusMasterEnable\b": "bus-master state change",
    r"\bsetMemoryEnable\b": "PCI memory-enable state change",
    r"\bsetIOEnable\b": "PCI I/O-enable state change",
    r"\benablePCIPowerManagement\b": "PCI power-management state change",
    r"\bmapDeviceMemory(?:WithIndex|WithRegister)?\b": "BAR mapping",
    r"\bIOMemoryMap\b": "memory mapping object",
    r"\bgetVirtualAddress\b": "mapped virtual address access",
    r"\bIOInterruptEventSource\b": "interrupt source",
    r"\bIOFilterInterruptEventSource\b": "filtered interrupt source",
    r"\bregisterInterrupt\b": "interrupt registration",
    r"\bIODMACommand\b": "DMA command",
    r"\bIOBufferMemoryDescriptor\b": "buffer suitable for later DMA",
    r"\bIOUserClient\b": "user client surface",
    r"\bIOCommandGate\b": "command gate not authorised in v0.1",
    r"\bIOWorkLoop\b": "work loop not authorised in v0.1",
    r"\bvolatile\b": "direct volatile access",
    r"\bioWrite(?:8|16|32)\b": "I/O-space write",
    r"\bOSWrite(?:Little|Big)Int(?:8|16|32|64)\b": "memory write primitive",
    r"\bml_phys_write\b": "physical-memory write primitive",
    r"\bsetPowerState\b": "power-state change",
    r"\bchangePowerStateTo\b": "power-state change",
    r"\brequestPowerDomainState\b": "power-domain state request",
    r"\bwriteBytes\b": "memory descriptor write",
}

ALLOWED_PCI_METHODS = {
    "configRead8", "configRead16", "configRead32", "extendedConfigRead32",
    "getBusNumber", "getDeviceNumber", "getFunctionNumber",
    "getDeviceMemoryWithRegister", "getDeviceMemoryCount",
    "getDeviceMemoryWithIndex", "getPath", "getRegistryEntryID",
    "getName", "getLocation", "retain", "release",
}

errors = []
for base in SOURCE_DIRS:
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix not in {".cpp", ".hpp", ".h", ".c"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, reason in FORBIDDEN.items():
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{path.relative_to(ROOT)}:{line}: {reason}: {match.group(0)}")

        for match in re.finditer(r"\b(?:device|pciDevice_|candidate)->([A-Za-z_][A-Za-z0-9_]*)\s*\(", text):
            method = match.group(1)
            if method not in ALLOWED_PCI_METHODS:
                line = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{path.relative_to(ROOT)}:{line}: unapproved IOPCIDevice method: {method}"
                )

if errors:
    print("SAFETY AUDIT FAILED", file=sys.stderr)
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

print("SAFETY AUDIT PASSED: v0.1.1 source contains only approved read/metadata primitives")
