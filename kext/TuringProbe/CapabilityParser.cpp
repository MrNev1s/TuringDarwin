#include "CapabilityParser.hpp"

#include <libkern/c++/OSArray.h>
#include <libkern/c++/OSDictionary.h>
#include <libkern/c++/OSNumber.h>

#include "PCIConfig.hpp"

namespace td {
namespace {

constexpr UInt16 kStatusCapabilitiesList = 1U << 4U;
constexpr UInt32 kMaximumConventionalNodes = 48;
constexpr UInt32 kMaximumExtendedNodes = 128;
constexpr UInt16 kExtendedCapabilitiesStart = 0x100;
constexpr UInt16 kExtendedCapabilitiesEnd = 0xFFC;

constexpr UInt8 kCapabilityPowerManagement = 0x01;
constexpr UInt8 kCapabilityMsi = 0x05;
constexpr UInt8 kCapabilityPcie = 0x10;
constexpr UInt8 kCapabilityMsix = 0x11;
constexpr UInt16 kExtendedCapabilityResizableBar = 0x0015;

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

bool conventionalRangeFits(UInt16 offset, UInt16 byteCount) {
    return offset < kConventionalConfigBytes &&
           byteCount <= kConventionalConfigBytes &&
           offset <= kConventionalConfigBytes - byteCount;
}

bool extendedRangeFits(UInt16 offset, UInt16 byteCount) {
    constexpr UInt32 kExtendedConfigBytes = 4096;
    return offset < kExtendedConfigBytes &&
           byteCount <= kExtendedConfigBytes &&
           offset <= kExtendedConfigBytes - byteCount;
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

            OSDictionary *entry = OSDictionary::withCapacity(7);
            if (entry != nullptr) {
                dictionaryNumber(entry, "ID", id, 8);
                dictionaryNumber(entry, "Offset", offset, 16);
                dictionaryNumber(entry, "Next", next, 16);
                dictionaryNumber(entry, "Raw0", device->configRead32(offset), 32);
                if (conventionalRangeFits(offset, 8))
                    dictionaryNumber(entry, "Raw1", device->configRead32(offset + 4U), 32);
                if (conventionalRangeFits(offset, 12))
                    dictionaryNumber(entry, "Raw2", device->configRead32(offset + 8U), 32);
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

        OSDictionary *entry = OSDictionary::withCapacity(8);
        if (entry != nullptr) {
            dictionaryNumber(entry, "ID", id, 16);
            dictionaryNumber(entry, "Version", version, 8);
            dictionaryNumber(entry, "Offset", offset, 16);
            dictionaryNumber(entry, "Next", next, 16);
            dictionaryNumber(entry, "Header", header, 32);
            if (extendedRangeFits(offset, 8))
                dictionaryNumber(entry, "Raw1", device->extendedConfigRead32(offset + 4U), 32);
            if (extendedRangeFits(offset, 12))
                dictionaryNumber(entry, "Raw2", device->extendedConfigRead32(offset + 8U), 32);
            capabilities->setObject(entry);
            entry->release();
        }

        if (id == kExtendedCapabilityResizableBar) {
            resizableBarPresent = true;
            publishNumber(owner, "TPResizableBARCapabilityOffset", offset, 16);
            if (extendedRangeFits(offset, 8)) {
                publishNumber(owner, "TPResizableBARCapability0",
                              device->extendedConfigRead32(offset + 4U), 32);
            }
            if (extendedRangeFits(offset, 12)) {
                publishNumber(owner, "TPResizableBARControl0",
                              device->extendedConfigRead32(offset + 8U), 32);
            }
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
