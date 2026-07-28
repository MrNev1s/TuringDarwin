#include "MMIOReadOnly.hpp"

#include <IOKit/IOMemoryDescriptor.h>
#include <libkern/OSByteOrder.h>

#include "Logging.hpp"
#include "PCIConfig.hpp"
#include "TopInventory.hpp"
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

bool performReadOnlyBar0Probe(IOPCIDevice *device, IOService *owner,
                              bool topInventoryRequested) {
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
    UInt32 vgpuBits = 0U;
    UInt32 chipset = 0U;
    UInt32 chipRevision = 0U;
    UInt32 crystalSelect = 0U;
    UInt32 crystalKHz = 0U;
    UInt16 commandAfterMap = 0U;
    UInt16 commandAfterReads = 0U;
    UInt64 mappingLength = 0U;
    bool mappingCreated = false;
    bool mappingReleased = false;
    bool topInventoryCompleted = false;
    const char *mappingFailure = nullptr;

    // For third-party C++14 kexts, the IOKit transition pointer alias is raw
    // unless the experimental shared-pointer API is enabled. The mapping must be
    // released explicitly on every path after a successful map().
    IOMemoryMap *mapping = descriptor->map(kIOMapReadOnly);
    if (mapping == nullptr) {
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

            // Fixed identity sequence. Exactly one read per identity register.
            boot1 = readWhitelisted32(bar0, kNvPmcBoot1Offset);
            boot0 = readWhitelisted32(bar0, kNvPmcBoot0Offset);
            strap = readWhitelisted32(bar0, kNvPextdevBoot0StrapOffset);

            vgpuBits = boot1 & kBoot1VgpuMask;
            chipset = (boot0 & kBoot0ChipsetMask) >> kBoot0ChipsetShift;
            chipRevision = boot0 & kBoot0RevisionMask;
            crystalSelect = strap & kCrystalSelectMask;
            crystalKHz = decodeCrystalKHz(strap);

            if (boot1 == 0xFFFFFFFFU) {
                mappingFailure = "NV_PMC_BOOT_1 returned all ones";
            } else if (boot1 == kBoot1BigEndianValue) {
                mappingFailure = "GPU reports big-endian MMIO; v0.3.0 will not switch it";
            } else if (vgpuBits != 0U) {
                mappingFailure = "NV_PMC_BOOT_1 reports a vGPU mode";
            } else if (boot0 == 0U || boot0 == 0xFFFFFFFFU) {
                mappingFailure = "NV_PMC_BOOT_0 returned an invalid value";
            } else if (chipset != kTu116ChipsetId) {
                mappingFailure = "NV_PMC_BOOT_0 does not identify TU116 chipset 0x168";
            } else if (strap == 0xFFFFFFFFU) {
                mappingFailure = "strap register returned all ones";
            } else if (crystalKHz == 0U) {
                mappingFailure = "strap crystal selection is not recognised";
            } else if (topInventoryRequested) {
                topInventoryCompleted = performReadOnlyTopInventory(bar0, owner);
                if (!topInventoryCompleted) {
                    mappingFailure = "bounded TOP device inventory did not decode safely";
                }
            }

            commandAfterReads = device->configRead16(kPciCommandOffset);
        }

        mapping->release();
        mapping = nullptr;
        mappingReleased = true;
    }

    publishBoolean(owner, "TPBAR0MappingCreated", mappingCreated);
    publishBoolean(owner, "TPBAR0MappingReadOnlyRequested", true);
    publishBoolean(owner, "TPBAR0MappingRetainedAfterProbe",
                   mappingCreated && !mappingReleased);
    publishBoolean(owner, "TPBAR0MappingReleased", mappingReleased);
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
    publishNumber(owner, "TPMMIOVgpuBits", vgpuBits, 32);
    publishNumber(owner, "TPMMIOChipset", chipset, 16);
    publishNumber(owner, "TPMMIOChipRevision", chipRevision, 8);
    publishBoolean(owner, "TPMMIOChipsetIsTU116", chipset == kTu116ChipsetId);
    publishNumber(owner, "TPMMIOCrystalSelect", crystalSelect, 32);
    publishNumber(owner, "TPMMIOCrystalKHz", crystalKHz, 32);
    publishBoolean(owner, "TPMMIOCrystalDecodeValid", crystalKHz != 0U);
    publishBoolean(owner, "TPTopInventoryRequested", topInventoryRequested);
    publishBoolean(owner, "TPTopInventoryCompleted", topInventoryCompleted);
    publishNumber(owner, "TPMMIOIdentityReadCount", kIdentityMmioReadCount, 32);
    publishNumber(owner, "TPMMIOTopReadCount",
                  topInventoryRequested ? kTopInventoryMmioReadCount : 0U, 32);
    publishNumber(owner, "TPMMIOReadCount",
                  topInventoryRequested ? kExpandedMmioReadCount :
                                          kIdentityMmioReadCount, 32);
    owner->setProperty("TPMMIOWhitelistSchemaVersion",
                       topInventoryRequested ? "2" : "1");
    owner->setProperty(
        "TPMMIOWhitelist",
        topInventoryRequested ?
            "identity:0x000004,0x000000,0x101000;top:64x32@0x022700" :
            "identity:0x000004,0x000000,0x101000");
    publishBoolean(owner, "TPMMIOReadCompleted", true);
    return true;
#endif
}

} // namespace td
