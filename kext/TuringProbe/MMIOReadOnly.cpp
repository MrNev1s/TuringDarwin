#include "MMIOReadOnly.hpp"

#include <IOKit/IOMemoryDescriptor.h>
#include <libkern/OSByteOrder.h>

#include "Logging.hpp"
#include "PCIConfig.hpp"
#include "../../include/TuringRegisters.hpp"

#ifndef TURINGPROBE_ENABLE_MMIO_READ
#define TURINGPROBE_ENABLE_MMIO_READ 0
#endif

namespace td {
namespace {

constexpr UInt16 kPciCommandIoSpaceEnable = 0x0001U;
constexpr UInt16 kPciCommandMemorySpaceEnable = 0x0002U;
constexpr UInt16 kPciCommandBusMasterEnable = 0x0004U;

UInt32 readWhitelisted32(const void *bar0, UInt32 offset) {
    return OSReadLittleInt32(bar0, offset);
}

UInt32 decodeCrystalKHz(UInt32 strap) {
    switch (strap & kCrystalSelectMask) {
        case 0x00000000U: return 13500U;
        case 0x00000040U: return 14318U;
        case 0x00400000U: return 27000U;
        case 0x00400040U: return 25000U;
        default: return 0U;
    }
}

bool fail(IOService *owner, const char *reason) {
    if (owner != nullptr && reason != nullptr) {
        owner->setProperty("TPMMIOFailureReason", reason);
    }
    TD_LOG("BAR0 read-only gate failed: %s", reason != nullptr ? reason : "unknown");
    return false;
}

} // namespace

bool performReadOnlyBar0Probe(IOPCIDevice *device, IOService *owner) {
#if TURINGPROBE_ENABLE_MMIO_READ != 1
    return fail(owner, "compile-time MMIO read gate is disabled");
#else
    if (device == nullptr || owner == nullptr) {
        return false;
    }

    const UInt16 commandBeforeMap = device->configRead16(kPciCommandOffset);
    publishNumber(owner, "TPCommandBeforeBAR0Map", commandBeforeMap, 16);
    publishBoolean(owner, "TPMemorySpaceEnabledBeforeBAR0Map",
                   (commandBeforeMap & kPciCommandMemorySpaceEnable) != 0);
    publishBoolean(owner, "TPBusMasterEnabledBeforeBAR0Map",
                   (commandBeforeMap & kPciCommandBusMasterEnable) != 0);

    if ((commandBeforeMap & kPciCommandMemorySpaceEnable) == 0) {
        return fail(owner, "PCI memory-space decoding is disabled");
    }
    if ((commandBeforeMap & kPciCommandBusMasterEnable) != 0) {
        return fail(owner, "bus mastering is unexpectedly enabled");
    }

    const UInt32 bar0Raw = device->configRead32(kPciBar0Offset);
    publishNumber(owner, "TPBAR0GateRaw", static_cast<UInt64>(bar0Raw), 64);
    if (bar0Raw == 0U || bar0Raw == 0xFFFFFFFFU) {
        return fail(owner, "BAR0 is not implemented");
    }
    if ((bar0Raw & 0x1U) != 0) {
        return fail(owner, "BAR0 is I/O space, not MMIO");
    }
    if (((bar0Raw >> 1U) & 0x3U) != 0U) {
        return fail(owner, "BAR0 is not the expected 32-bit memory BAR");
    }
    if ((bar0Raw & 0x8U) != 0) {
        return fail(owner, "BAR0 is unexpectedly prefetchable");
    }

    IOMemoryDescriptor *descriptor =
        device->getDeviceMemoryWithRegister(static_cast<UInt8>(kPciBar0Offset));
    if (descriptor == nullptr) {
        return fail(owner, "IOPCIFamily did not publish a BAR0 descriptor");
    }

    const UInt64 physicalAddress = descriptor->getPhysicalAddress();
    const UInt64 descriptorLength = descriptor->getLength();
    const UInt64 rawAssignedBase = static_cast<UInt64>(bar0Raw & ~0xFU);
    publishNumber(owner, "TPBAR0GatePhysicalAddress", physicalAddress, 64);
    publishNumber(owner, "TPBAR0GateDescriptorLength", descriptorLength, 64);

    if (physicalAddress == 0U || physicalAddress != rawAssignedBase) {
        return fail(owner, "BAR0 descriptor base does not match PCI configuration");
    }
    if (descriptorLength != static_cast<UInt64>(kExpectedBar0Length)) {
        return fail(owner, "BAR0 descriptor length is not exactly 16 MiB");
    }
    if ((physicalAddress & (static_cast<UInt64>(kExpectedBar0Length) - 1U)) != 0U) {
        return fail(owner, "BAR0 base is not aligned to its verified aperture size");
    }

    UInt32 boot1 = 0U;
    UInt32 boot0 = 0U;
    UInt32 strap = 0U;
    UInt16 commandAfterMap = 0U;
    UInt16 commandAfterReads = 0U;
    UInt64 mappingLength = 0U;
    bool mappingCreated = false;
    const char *mappingFailure = nullptr;

    {
        auto mapping = descriptor->map(kIOMapReadOnly);
        if (!mapping) {
            mappingFailure = "read-only BAR0 mapping failed";
        } else {
            mappingCreated = true;
            mappingLength = mapping->getLength();
            const IOVirtualAddress virtualAddress = mapping->getVirtualAddress();
            if (virtualAddress == 0U) {
                mappingFailure = "BAR0 mapping has no virtual address";
            } else if (mappingLength != static_cast<UInt64>(kExpectedBar0Length)) {
                mappingFailure = "BAR0 mapping length is not exactly 16 MiB";
            } else {
                commandAfterMap = device->configRead16(kPciCommandOffset);
                const void *bar0 = reinterpret_cast<const void *>(virtualAddress);

                // Fixed sequence. Exactly one read per whitelisted register.
                boot1 = readWhitelisted32(bar0, kNvPmcBoot1Offset);
                boot0 = readWhitelisted32(bar0, kNvPmcBoot0Offset);
                strap = readWhitelisted32(bar0, kNvPextdevBoot0StrapOffset);
                commandAfterReads = device->configRead16(kPciCommandOffset);
            }
        }
    } // OSPtr<IOMemoryMap> leaves scope; the BAR0 mapping is destroyed here.

    publishBoolean(owner, "TPBAR0MappingCreated", mappingCreated);
    publishBoolean(owner, "TPBAR0MappingReadOnlyRequested", true);
    publishBoolean(owner, "TPBAR0MappingRetainedAfterProbe", false);
    publishBoolean(owner, "TPBAR0MappingReleased", mappingCreated);
    publishNumber(owner, "TPBAR0MappingLength", mappingLength, 64);

    if (mappingFailure != nullptr) {
        return fail(owner, mappingFailure);
    }

    publishNumber(owner, "TPCommandAfterBAR0Map", commandAfterMap, 16);
    publishNumber(owner, "TPCommandAfterMMIOReads", commandAfterReads, 16);
    publishBoolean(owner, "TPCommandUnchangedAcrossMMIO",
                   commandBeforeMap == commandAfterMap &&
                   commandAfterMap == commandAfterReads);
    publishBoolean(owner, "TPBusMasterEnabledAfterBAR0Map",
                   (commandAfterMap & kPciCommandBusMasterEnable) != 0);
    publishBoolean(owner, "TPBusMasterEnabledAfterMMIOReads",
                   (commandAfterReads & kPciCommandBusMasterEnable) != 0);
    publishBoolean(owner, "TPIOSpaceEnabledAfterMMIOReads",
                   (commandAfterReads & kPciCommandIoSpaceEnable) != 0);
    publishBoolean(owner, "TPMemorySpaceEnabledAfterMMIOReads",
                   (commandAfterReads & kPciCommandMemorySpaceEnable) != 0);

    if (commandBeforeMap != commandAfterMap || commandAfterMap != commandAfterReads) {
        return fail(owner, "PCI Command Register changed during BAR0 probe");
    }
    if ((commandAfterReads & kPciCommandBusMasterEnable) != 0) {
        return fail(owner, "bus mastering became enabled during BAR0 probe");
    }

    publishNumber(owner, "TPMMIONvPmcBoot1", static_cast<UInt64>(boot1), 64);
    publishNumber(owner, "TPMMIONvPmcBoot0", static_cast<UInt64>(boot0), 64);
    publishNumber(owner, "TPMMIONvPextdevBoot0Strap", static_cast<UInt64>(strap), 64);

    if (boot1 == 0xFFFFFFFFU) {
        return fail(owner, "NV_PMC_BOOT_1 returned all ones");
    }
    if (boot1 == kBoot1BigEndianValue) {
        return fail(owner, "GPU reports big-endian MMIO; v0.2.0 will not switch it");
    }

    const UInt32 vgpuBits = boot1 & kBoot1VgpuMask;
    publishNumber(owner, "TPMMIOVgpuBits", vgpuBits, 32);
    if (vgpuBits != 0U) {
        return fail(owner, "NV_PMC_BOOT_1 reports a vGPU mode");
    }

    if (boot0 == 0U || boot0 == 0xFFFFFFFFU) {
        return fail(owner, "NV_PMC_BOOT_0 returned an invalid value");
    }

    const UInt32 chipset = (boot0 & kBoot0ChipsetMask) >> kBoot0ChipsetShift;
    const UInt32 chipRevision = boot0 & kBoot0RevisionMask;
    publishNumber(owner, "TPMMIOChipset", chipset, 16);
    publishNumber(owner, "TPMMIOChipRevision", chipRevision, 8);
    publishBoolean(owner, "TPMMIOChipsetIsTU116", chipset == kTu116ChipsetId);
    if (chipset != kTu116ChipsetId) {
        return fail(owner, "NV_PMC_BOOT_0 does not identify TU116 chipset 0x168");
    }

    if (strap == 0xFFFFFFFFU) {
        return fail(owner, "strap register returned all ones");
    }

    const UInt32 crystalSelect = strap & kCrystalSelectMask;
    const UInt32 crystalKHz = decodeCrystalKHz(strap);
    publishNumber(owner, "TPMMIOCrystalSelect", crystalSelect, 32);
    publishNumber(owner, "TPMMIOCrystalKHz", crystalKHz, 32);
    publishBoolean(owner, "TPMMIOCrystalDecodeValid", crystalKHz != 0U);
    if (crystalKHz == 0U) {
        return fail(owner, "strap crystal selection is not recognised");
    }

    publishNumber(owner, "TPMMIOReadCount", kMmioWhitelistReadCount, 32);
    owner->setProperty("TPMMIOWhitelistSchemaVersion", "1");
    owner->setProperty("TPMMIOWhitelist",
                       "0x000004:NV_PMC_BOOT_1,0x000000:NV_PMC_BOOT_0,0x101000:NV_PEXTDEV_BOOT_0_STRAP");
    publishBoolean(owner, "TPMMIOReadCompleted", true);
    return true;
#endif
}

} // namespace td
