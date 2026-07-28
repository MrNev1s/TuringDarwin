#pragma once

#include <IOKit/IOService.h>
#include <IOKit/pci/IOPCIDevice.h>
#include <libkern/OSTypes.h>

#include "../../include/TuringTypes.hpp"

namespace td {

constexpr UInt16 kPciCommandOffset = 0x04;
constexpr UInt16 kPciStatusOffset = 0x06;
constexpr UInt16 kPciClassCodeOffset = 0x08;
constexpr UInt16 kPciHeaderTypeOffset = 0x0E;
constexpr UInt16 kPciBar0Offset = 0x10;
constexpr UInt16 kPciSubsystemVendorOffset = 0x2C;
constexpr UInt16 kPciSubsystemDeviceOffset = 0x2E;
constexpr UInt16 kPciExpansionRomOffset = 0x30;
constexpr UInt16 kPciCapabilitiesPointerOffset = 0x34;
constexpr UInt16 kPciInterruptLineOffset = 0x3C;
constexpr UInt16 kPciInterruptPinOffset = 0x3D;
constexpr UInt32 kConventionalConfigBytes = 256;

PciIdentity readIdentity(IOPCIDevice *device);
bool isExactTarget(const PciIdentity &identity);
void publishPciSnapshot(IOPCIDevice *device, IOService *owner);
void publishRegistryPaths(IOPCIDevice *device, IOService *owner);
void publishConventionalConfigSnapshot(IOPCIDevice *device, IOService *owner);
void publishNumber(IOService *owner, const char *key, UInt64 value,
                   unsigned int bits = 64);
void publishBoolean(IOService *owner, const char *key, bool value);

}
