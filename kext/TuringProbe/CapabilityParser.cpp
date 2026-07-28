#include "CapabilityParser.hpp"

#include <libkern/c++/OSArray.h>
#include <libkern/c++/OSDictionary.h>
#include <libkern/c++/OSNumber.h>
#include <libkern/c++/OSString.h>

#include "PCIConfig.hpp"

namespace td {
namespace {

constexpr UInt16 kStatusCapabilitiesList = 1U << 4U;
constexpr UInt32 kMaximumConventionalNodes = 48;
constexpr UInt32 kMaximumExtendedNodes = 128;
constexpr UInt16 kExtendedCapabilitiesStart = 0x100;
constexpr UInt16 kExtendedCapabilitiesEnd = 0xFFC;
constexpr UInt32 kExtendedConfigBytes = 4096;

constexpr UInt8 kCapabilityPowerManagement = 0x01;
constexpr UInt8 kCapabilityMsi = 0x05;
constexpr UInt8 kCapabilityPcie = 0x10;
constexpr UInt8 kCapabilityMsix = 0x11;
constexpr UInt16 kExtendedCapabilityResizableBar = 0x0015;

constexpr UInt16 kResizableBarCapabilityRegister = 0x04;
constexpr UInt16 kResizableBarControlRegister = 0x08;
constexpr UInt32 kResizableBarSupportedSizesMask = 0xFFFFFFF0U;
constexpr UInt32 kResizableBarIndexMask = 0x00000007U;
constexpr UInt32 kResizableBarCountMask = 0x000000E0U;
constexpr UInt32 kResizableBarCountShift = 5U;
constexpr UInt32 kResizableBarCurrentSizeMask = 0x00001F00U;
constexpr UInt32 kResizableBarCurrentSizeShift = 8U;
constexpr UInt32 kMaximumResizableBarEntries = 6U;
constexpr UInt32 kMaximumResizableBarSizeEncoding = 27U;

void dictionaryNumber(OSDictionary *dictionary, const char *key,
                      UInt64 value, unsigned int bits) {
    if (dictionary == nullptr || key == nullptr) return;
    OSNumber *number = OSNumber::withNumber(value, bits);
    if (number == nullptr) return;
    dictionary->setObject(key, number);
    number->release();
}

void dictionaryBoolean(OSDictionary *dictionary, const char *key, bool value) {
    if (dictionary == nullptr || key == nullptr) return;
    dictionary->setObject(key, value ? kOSBooleanTrue : kOSBooleanFalse);
}

void dictionaryString(OSDictionary *dictionary, const char *key,
                      const char *value) {
    if (dictionary == nullptr || key == nullptr || value == nullptr) return;
    OSString *string = OSString::withCString(value);
    if (string == nullptr) return;
    dictionary->setObject(key, string);
    string->release();
}

const char *conventionalCapabilityName(UInt8 id) {
    switch (id) {
        case 0x01: return "Power Management";
        case 0x02: return "Accelerated Graphics Port";
        case 0x03: return "Vital Product Data";
        case 0x05: return "MSI";
        case 0x09: return "Vendor-Specific";
        case 0x10: return "PCI Express";
        case 0x11: return "MSI-X";
        case 0x13: return "Advanced Features";
        case 0x14: return "Enhanced Allocation";
        default: return "Unknown";
    }
}

const char *extendedCapabilityName(UInt16 id) {
    switch (id) {
        case 0x0001: return "Advanced Error Reporting";
        case 0x0002: return "Virtual Channel";
        case 0x0003: return "Device Serial Number";
        case 0x0004: return "Power Budgeting";
        case 0x000B: return "Vendor-Specific Extended Capability";
        case 0x0015: return "Resizable BAR";
        case 0x0018: return "Latency Tolerance Reporting";
        case 0x0019: return "Secondary PCI Express";
        case 0x001E: return "L1 PM Substates";
        default: return "Unknown";
    }
}

bool conventionalRangeFits(UInt16 offset, UInt16 byteCount) {
    return offset < kConventionalConfigBytes &&
           byteCount <= kConventionalConfigBytes &&
           offset <= kConventionalConfigBytes - byteCount;
}

bool extendedRangeFits(UInt16 offset, UInt16 byteCount) {
    return offset < kExtendedConfigBytes &&
           byteCount <= kExtendedConfigBytes &&
           offset <= kExtendedConfigBytes - byteCount;
}

bool extendedRangeFitsCapability(UInt16 offset, UInt16 byteCount,
                                 UInt16 nextCapabilityOffset) {
    if (!extendedRangeFits(offset, byteCount)) return false;
    const UInt32 end = static_cast<UInt32>(offset) + byteCount;
    const UInt32 limit = nextCapabilityOffset == 0
        ? kExtendedConfigBytes
        : static_cast<UInt32>(nextCapabilityOffset);
    return end <= limit;
}

UInt64 resizableBarSizeBytes(UInt32 encoding) {
    // PCIe Resizable BAR size encoding n represents 2^(n + 20) bytes.
    if (encoding > 43U) return 0;
    return static_cast<UInt64>(1) << (encoding + 20U);
}

void decodeResizableBars(IOPCIDevice *device, IOService *owner,
                         UInt16 capabilityOffset, UInt16 nextCapabilityOffset) {
    publishNumber(owner, "TPResizableBARCapabilityOffset", capabilityOffset, 16);

    if (!extendedRangeFitsCapability(
            capabilityOffset + kResizableBarCapabilityRegister, 8,
            nextCapabilityOffset)) {
        publishBoolean(owner, "TPResizableBARDecodeValid", false);
        return;
    }

    const UInt32 firstCapability = device->extendedConfigRead32(
        capabilityOffset + kResizableBarCapabilityRegister);
    const UInt32 firstControl = device->extendedConfigRead32(
        capabilityOffset + kResizableBarControlRegister);
    const UInt32 entryCount =
        (firstControl & kResizableBarCountMask) >> kResizableBarCountShift;

    // Preserve the v0.1 compatibility properties.
    publishNumber(owner, "TPResizableBARCapability0",
                  static_cast<UInt64>(firstCapability), 64);
    publishNumber(owner, "TPResizableBARControl0",
                  static_cast<UInt64>(firstControl), 64);
    publishNumber(owner, "TPResizableBARCountField", entryCount, 8);

    if (entryCount == 0 || entryCount > kMaximumResizableBarEntries) {
        publishBoolean(owner, "TPResizableBARDecodeValid", false);
        publishNumber(owner, "TPResizableBARDecodedEntryCount", 0, 8);
        return;
    }

    OSArray *entries = OSArray::withCapacity(entryCount);
    if (entries == nullptr) {
        publishBoolean(owner, "TPResizableBARDecodeValid", false);
        return;
    }

    bool valid = true;
    UInt32 decodedCount = 0;
    for (UInt32 index = 0; index < entryCount; ++index) {
        const UInt32 entryBase = static_cast<UInt32>(capabilityOffset) +
                                 kResizableBarCapabilityRegister + index * 8U;
        if (entryBase > 0xFFFFU ||
            !extendedRangeFitsCapability(static_cast<UInt16>(entryBase), 8,
                                         nextCapabilityOffset)) {
            valid = false;
            break;
        }

        const UInt16 capabilityRegisterOffset = static_cast<UInt16>(entryBase);
        const UInt16 controlRegisterOffset =
            static_cast<UInt16>(entryBase + 4U);
        const UInt32 capability =
            device->extendedConfigRead32(capabilityRegisterOffset);
        const UInt32 control =
            device->extendedConfigRead32(controlRegisterOffset);
        const UInt32 barIndex = control & kResizableBarIndexMask;
        const UInt32 sizeEncoding =
            (control & kResizableBarCurrentSizeMask) >>
            kResizableBarCurrentSizeShift;
        const UInt32 supportedSizeMask =
            (capability & kResizableBarSupportedSizesMask) >> 4U;
        const UInt64 currentSizeBytes = resizableBarSizeBytes(sizeEncoding);
        const bool currentSizeAdvertised =
            sizeEncoding <= kMaximumResizableBarSizeEncoding &&
            (supportedSizeMask & (1U << sizeEncoding)) != 0;

        OSDictionary *entry = OSDictionary::withCapacity(14);
        if (entry == nullptr) {
            valid = false;
            break;
        }

        dictionaryNumber(entry, "EntryIndex", index, 8);
        dictionaryNumber(entry, "CapabilityRegisterOffset",
                         capabilityRegisterOffset, 16);
        dictionaryNumber(entry, "ControlRegisterOffset",
                         controlRegisterOffset, 16);
        dictionaryNumber(entry, "CapabilityRaw",
                         static_cast<UInt64>(capability), 64);
        dictionaryNumber(entry, "ControlRaw",
                         static_cast<UInt64>(control), 64);
        dictionaryNumber(entry, "BARIndex", barIndex, 8);
        dictionaryBoolean(entry, "BARIndexValid", barIndex < 6U);
        dictionaryNumber(entry, "SupportedSizeMask", supportedSizeMask, 32);
        dictionaryNumber(entry, "CurrentSizeEncoding", sizeEncoding, 8);
        dictionaryNumber(entry, "CurrentSizeBytes", currentSizeBytes, 64);
        dictionaryBoolean(entry, "CurrentSizeAdvertised",
                          currentSizeAdvertised);

        OSArray *supportedSizes = OSArray::withCapacity(8);
        if (supportedSizes != nullptr) {
            for (UInt32 encoding = 0;
                 encoding <= kMaximumResizableBarSizeEncoding;
                 ++encoding) {
                if ((supportedSizeMask & (1U << encoding)) == 0) continue;
                OSNumber *size = OSNumber::withNumber(
                    resizableBarSizeBytes(encoding), 64);
                if (size == nullptr) continue;
                supportedSizes->setObject(size);
                size->release();
            }
            entry->setObject("SupportedSizesBytes", supportedSizes);
            supportedSizes->release();
        }

        entries->setObject(entry);
        entry->release();
        ++decodedCount;
    }

    publishNumber(owner, "TPResizableBARDecodedEntryCount", decodedCount, 8);
    publishBoolean(owner, "TPResizableBARDecodeValid",
                   valid && decodedCount == entryCount);
    owner->setProperty("TPResizableBAREntries", entries);
    entries->release();
}

void decodeConventional(IOPCIDevice *device, IOService *owner,
                        UInt8 capabilityId, UInt16 offset) {
    switch (capabilityId) {
        case kCapabilityPowerManagement: {
            if (!conventionalRangeFits(offset, 6)) return;
            publishNumber(owner, "TPPowerManagementCapabilityOffset", offset, 16);
            publishNumber(owner, "TPPowerManagementCapabilities",
                          device->configRead16(offset + 2U), 16);
            publishNumber(owner, "TPPowerManagementControlStatus",
                          device->configRead16(offset + 4U), 16);
            break;
        }
        case kCapabilityMsi: {
            if (!conventionalRangeFits(offset, 4)) return;
            const UInt16 control = device->configRead16(offset + 2U);
            publishNumber(owner, "TPMSICapabilityOffset", offset, 16);
            publishNumber(owner, "TPMSIMessageControl", control, 16);
            publishBoolean(owner, "TPMSIEnabled", (control & 0x0001U) != 0);
            publishBoolean(owner, "TPMSI64BitCapable", (control & 0x0080U) != 0);
            publishNumber(owner, "TPMSIMultipleMessageCapable",
                          (control >> 1U) & 0x7U, 8);
            break;
        }
        case kCapabilityPcie: {
            if (!conventionalRangeFits(offset, 0x14)) return;
            const UInt16 capabilities = device->configRead16(offset + 2U);
            const UInt32 linkCapabilities = device->configRead32(offset + 0x0CU);
            const UInt16 linkStatus = device->configRead16(offset + 0x12U);
            publishNumber(owner, "TPPCIExpressCapabilityOffset", offset, 16);
            publishNumber(owner, "TPPCIExpressCapabilities", capabilities, 16);
            publishNumber(owner, "TPPCIExpressVersion", capabilities & 0xFU, 8);
            publishNumber(owner, "TPPCIExpressDeviceType",
                          (capabilities >> 4U) & 0xFU, 8);
            publishNumber(owner, "TPPCIExpressLinkCapabilities", linkCapabilities, 32);
            publishNumber(owner, "TPPCIExpressMaximumLinkSpeed",
                          linkCapabilities & 0xFU, 8);
            publishNumber(owner, "TPPCIExpressMaximumLinkWidth",
                          (linkCapabilities >> 4U) & 0x3FU, 8);
            publishNumber(owner, "TPPCIExpressLinkStatus", linkStatus, 16);
            publishNumber(owner, "TPPCIExpressCurrentLinkSpeed",
                          linkStatus & 0xFU, 8);
            publishNumber(owner, "TPPCIExpressNegotiatedLinkWidth",
                          (linkStatus >> 4U) & 0x3FU, 8);
            break;
        }
        case kCapabilityMsix: {
            if (!conventionalRangeFits(offset, 12)) return;
            const UInt16 control = device->configRead16(offset + 2U);
            publishNumber(owner, "TPMSIXCapabilityOffset", offset, 16);
            publishNumber(owner, "TPMSIXMessageControl", control, 16);
            publishBoolean(owner, "TPMSIXEnabled", (control & 0x8000U) != 0);
            publishNumber(owner, "TPMSIXTableSize", (control & 0x07FFU) + 1U, 16);
            publishNumber(owner, "TPMSIXTable", device->configRead32(offset + 4U), 32);
            publishNumber(owner, "TPMSIXPendingBitArray",
                          device->configRead32(offset + 8U), 32);
            break;
        }
        default:
            break;
    }
}

void publishConventionalCapabilities(IOPCIDevice *device, IOService *owner) {
    OSArray *capabilities = OSArray::withCapacity(12);
    if (capabilities == nullptr) return;

    UInt32 count = 0;
    bool terminatedSafely = true;
    const UInt16 status = device->configRead16(kPciStatusOffset);
    if ((status & kStatusCapabilitiesList) != 0) {
        UInt16 offset = device->configRead8(kPciCapabilitiesPointerOffset) & 0xFCU;
        bool visited[256] {};

        while (offset >= 0x40U && offset <= 0xFCU &&
               !visited[offset] && count < kMaximumConventionalNodes) {
            visited[offset] = true;
            const UInt8 id = device->configRead8(offset);
            const UInt16 next = device->configRead8(offset + 1U) & 0xFCU;

            OSDictionary *entry = OSDictionary::withCapacity(9);
            if (entry != nullptr) {
                dictionaryNumber(entry, "ID", id, 8);
                dictionaryString(entry, "Name", conventionalCapabilityName(id));
                dictionaryBoolean(entry, "Known",
                                  conventionalCapabilityName(id)[0] != 'U');
                dictionaryNumber(entry, "Offset", offset, 16);
                dictionaryNumber(entry, "Next", next, 16);
                dictionaryNumber(entry, "Raw0",
                                 static_cast<UInt64>(device->configRead32(offset)), 64);
                if (conventionalRangeFits(offset, 8))
                    dictionaryNumber(entry, "Raw1",
                                     static_cast<UInt64>(device->configRead32(offset + 4U)), 64);
                if (conventionalRangeFits(offset, 12))
                    dictionaryNumber(entry, "Raw2",
                                     static_cast<UInt64>(device->configRead32(offset + 8U)), 64);
                capabilities->setObject(entry);
                entry->release();
            }

            decodeConventional(device, owner, id, offset);
            ++count;
            if (next == 0) break;
            if (next == offset || next < 0x40U || next > 0xFCU || visited[next]) {
                terminatedSafely = false;
                break;
            }
            offset = next;
        }

        if (count == kMaximumConventionalNodes) terminatedSafely = false;
    }

    publishNumber(owner, "TPConventionalCapabilityCount", count, 32);
    publishBoolean(owner, "TPConventionalCapabilityWalkValid", terminatedSafely);
    owner->setProperty("TPConventionalCapabilities", capabilities);
    capabilities->release();
}

void publishExtendedCapabilities(IOPCIDevice *device, IOService *owner) {
    OSArray *capabilities = OSArray::withCapacity(16);
    if (capabilities == nullptr) return;

    bool seenOffsets[1024] {};
    UInt16 offset = kExtendedCapabilitiesStart;
    UInt32 count = 0;
    bool resizableBarPresent = false;
    bool terminatedSafely = true;

    while (offset >= kExtendedCapabilitiesStart &&
           offset <= kExtendedCapabilitiesEnd &&
           (offset & 0x3U) == 0 &&
           count < kMaximumExtendedNodes) {
        const UInt32 index = offset >> 2U;
        if (index >= 1024U || seenOffsets[index]) {
            terminatedSafely = false;
            break;
        }
        seenOffsets[index] = true;

        const UInt32 header = device->extendedConfigRead32(offset);
        if (header == 0 || header == 0xFFFFFFFFU) break;

        const UInt16 id = header & 0xFFFFU;
        const UInt8 version = (header >> 16U) & 0xFU;
        const UInt16 next = (header >> 20U) & 0xFFFU;

        OSDictionary *entry = OSDictionary::withCapacity(10);
        if (entry != nullptr) {
            dictionaryNumber(entry, "ID", id, 16);
            dictionaryString(entry, "Name", extendedCapabilityName(id));
            dictionaryBoolean(entry, "Known",
                              extendedCapabilityName(id)[0] != 'U');
            dictionaryNumber(entry, "Version", version, 8);
            dictionaryNumber(entry, "Offset", offset, 16);
            dictionaryNumber(entry, "Next", next, 16);
            dictionaryNumber(entry, "Header", static_cast<UInt64>(header), 64);
            if (extendedRangeFits(offset, 8))
                dictionaryNumber(entry, "Raw1",
                                 static_cast<UInt64>(device->extendedConfigRead32(offset + 4U)), 64);
            if (extendedRangeFits(offset, 12))
                dictionaryNumber(entry, "Raw2",
                                 static_cast<UInt64>(device->extendedConfigRead32(offset + 8U)), 64);
            capabilities->setObject(entry);
            entry->release();
        }

        if (id == kExtendedCapabilityResizableBar) {
            resizableBarPresent = true;
            decodeResizableBars(device, owner, offset, next);
        }

        ++count;
        if (next == 0) break;
        if (next == offset || next < kExtendedCapabilitiesStart ||
            next > kExtendedCapabilitiesEnd || (next & 0x3U) != 0) {
            terminatedSafely = false;
            break;
        }
        offset = next;
    }

    if (count == kMaximumExtendedNodes) terminatedSafely = false;
    publishNumber(owner, "TPExtendedCapabilityCount", count, 32);
    publishBoolean(owner, "TPExtendedCapabilityWalkValid", terminatedSafely);
    publishBoolean(owner, "TPResizableBARPresent", resizableBarPresent);
    owner->setProperty("TPExtendedCapabilities", capabilities);
    capabilities->release();
}

}

void publishCapabilities(IOPCIDevice *device, IOService *owner) {
    if (device == nullptr || owner == nullptr) return;
    publishConventionalCapabilities(device, owner);
    publishExtendedCapabilities(device, owner);
}

}
