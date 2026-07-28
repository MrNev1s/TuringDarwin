#include "PCIConfig.hpp"

#include <IOKit/IOLib.h>
#include <IOKit/IORegistryEntry.h>
#include <libkern/c++/OSData.h>
#include <libkern/c++/OSNumber.h>

#include "../../include/TuringDeviceIds.hpp"

namespace td {
namespace {

void publishPath(IOPCIDevice *device, IOService *owner, const char *key,
                 const IORegistryPlane *plane) {
    if (device == nullptr || owner == nullptr || key == nullptr || plane == nullptr) return;

    char path[1024] {};
    int length = static_cast<int>(sizeof(path));
    if (device->getPath(path, &length, plane)) {
        owner->setProperty(key, path);
    }
}

}

PciIdentity readIdentity(IOPCIDevice *device) {
    PciIdentity identity {};
    if (device == nullptr) return identity;

    identity.vendor = device->configRead16(kIOPCIConfigVendorID);
    identity.device = device->configRead16(kIOPCIConfigDeviceID);
    identity.subsystemVendor = device->configRead16(kPciSubsystemVendorOffset);
    identity.subsystemDevice = device->configRead16(kPciSubsystemDeviceOffset);
    return identity;
}

bool isExactTarget(const PciIdentity &identity) {
    return identity.vendor == kNvidiaVendorId &&
           identity.device == kTu116Gtx1660TiDeviceId &&
           identity.subsystemVendor == kAsusSubsystemVendorId &&
           identity.subsystemDevice == kAsusSubsystemDeviceId;
}

void publishNumber(IOService *owner, const char *key, UInt64 value,
                   unsigned int bits) {
    if (owner == nullptr || key == nullptr) return;
    OSNumber *number = OSNumber::withNumber(value, bits);
    if (number == nullptr) return;
    owner->setProperty(key, number);
    number->release();
}

void publishBoolean(IOService *owner, const char *key, bool value) {
    if (owner == nullptr || key == nullptr) return;
    owner->setProperty(key, value ? kOSBooleanTrue : kOSBooleanFalse);
}

void publishPciSnapshot(IOPCIDevice *device, IOService *owner) {
    if (device == nullptr || owner == nullptr) return;

    const UInt32 classAndRevision = device->configRead32(kPciClassCodeOffset);
    const UInt8 headerType = device->configRead8(kPciHeaderTypeOffset);

    publishNumber(owner, "TPVendorID", device->configRead16(kIOPCIConfigVendorID), 16);
    publishNumber(owner, "TPDeviceID", device->configRead16(kIOPCIConfigDeviceID), 16);
    publishNumber(owner, "TPCommand", device->configRead16(kPciCommandOffset), 16);
    publishNumber(owner, "TPStatus", device->configRead16(kPciStatusOffset), 16);
    publishNumber(owner, "TPRevisionID", classAndRevision & 0xFFU, 8);
    publishNumber(owner, "TPClassCode", (classAndRevision >> 8U) & 0x00FFFFFFU, 32);
    publishNumber(owner, "TPHeaderType", headerType, 8);
    publishBoolean(owner, "TPMultifunction", (headerType & 0x80U) != 0);
    publishNumber(owner, "TPSubsystemVendorID",
                  device->configRead16(kPciSubsystemVendorOffset), 16);
    publishNumber(owner, "TPSubsystemDeviceID",
                  device->configRead16(kPciSubsystemDeviceOffset), 16);
    publishNumber(owner, "TPInterruptLine",
                  device->configRead8(kPciInterruptLineOffset), 8);
    publishNumber(owner, "TPInterruptPin",
                  device->configRead8(kPciInterruptPinOffset), 8);
    publishNumber(owner, "TPExpansionRomBARRaw",
                  static_cast<UInt64>(device->configRead32(kPciExpansionRomOffset)), 64);
    publishNumber(owner, "TPBusNumber", device->getBusNumber(), 8);
    publishNumber(owner, "TPDeviceNumber", device->getDeviceNumber(), 8);
    publishNumber(owner, "TPFunctionNumber", device->getFunctionNumber(), 8);
    publishNumber(owner, "TPRegistryEntryID", device->getRegistryEntryID(), 64);

    for (UInt32 index = 0; index < 6; ++index) {
        const UInt16 offset = static_cast<UInt16>(kPciBar0Offset + index * 4U);
        char key[24] {};
        snprintf(key, sizeof(key), "TPBAR%uRaw", index);
        publishNumber(owner, key,
                      static_cast<UInt64>(device->configRead32(offset)), 64);
    }
}

void publishRegistryPaths(IOPCIDevice *device, IOService *owner) {
    publishPath(device, owner, "TPIOServicePath", gIOServicePlane);
    publishPath(device, owner, "TPIODeviceTreePath",
                IORegistryEntry::getPlane("IODeviceTree"));

    const char *name = device != nullptr ? device->getName(gIOServicePlane) : nullptr;
    const char *location = device != nullptr ? device->getLocation(gIOServicePlane) : nullptr;
    if (owner != nullptr && name != nullptr) owner->setProperty("TPProviderName", name);
    if (owner != nullptr && location != nullptr) owner->setProperty("TPProviderLocation", location);
}

void publishConventionalConfigSnapshot(IOPCIDevice *device, IOService *owner) {
    if (device == nullptr || owner == nullptr) return;

    UInt8 bytes[kConventionalConfigBytes] {};
    for (UInt32 offset = 0; offset < kConventionalConfigBytes; ++offset) {
        bytes[offset] = device->configRead8(static_cast<UInt16>(offset));
    }

    OSData *snapshot = OSData::withBytes(bytes, sizeof(bytes));
    if (snapshot == nullptr) return;
    owner->setProperty("TPPCIConfigSpace256", snapshot);
    snapshot->release();
}

}
