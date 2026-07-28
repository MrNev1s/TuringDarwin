#include "BARInspector.hpp"

#include <IOKit/IOMemoryDescriptor.h>
#include <libkern/c++/OSArray.h>
#include <libkern/c++/OSDictionary.h>
#include <libkern/c++/OSNumber.h>

#include "PCIConfig.hpp"

namespace td {
namespace {

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

}

void publishBarAndMemoryDescriptors(IOPCIDevice *device, IOService *owner) {
    if (device == nullptr || owner == nullptr) return;

    OSArray *bars = OSArray::withCapacity(6);
    if (bars != nullptr) {
        bool continuationOf64BitBar = false;
        for (UInt32 index = 0; index < 6; ++index) {
            const UInt16 registerOffset = static_cast<UInt16>(kPciBar0Offset + index * 4U);
            const UInt32 raw = device->configRead32(registerOffset);

            OSDictionary *entry = OSDictionary::withCapacity(15);
            if (entry == nullptr) continue;
            dictionaryNumber(entry, "Index", index, 8);
            dictionaryNumber(entry, "RegisterOffset", registerOffset, 16);
            dictionaryNumber(entry, "Raw", raw, 32);

            if (continuationOf64BitBar) {
                dictionaryBoolean(entry, "ContinuationOfPrevious64BitBAR", true);
                dictionaryBoolean(entry, "Implemented", false);
                continuationOf64BitBar = false;
                bars->setObject(entry);
                entry->release();
                continue;
            }

            const bool implemented = raw != 0 && raw != 0xFFFFFFFFU;
            const bool ioSpace = implemented && ((raw & 0x1U) != 0);
            const UInt32 memoryType = ioSpace ? 0 : ((raw >> 1U) & 0x3U);
            const bool is64Bit = implemented && !ioSpace && memoryType == 0x2U && index < 5;
            const bool prefetchable = implemented && !ioSpace && ((raw & 0x8U) != 0);

            dictionaryBoolean(entry, "ContinuationOfPrevious64BitBAR", false);
            dictionaryBoolean(entry, "Implemented", implemented);
            dictionaryBoolean(entry, "IOSpace", ioSpace);
            dictionaryBoolean(entry, "Memory64Bit", is64Bit);
            dictionaryBoolean(entry, "Prefetchable", prefetchable);
            dictionaryNumber(entry, "MemoryTypeEncoding", memoryType, 8);

            if (implemented) {
                UInt64 assignedBase = 0;
                if (ioSpace) {
                    assignedBase = static_cast<UInt64>(raw & ~0x3U);
                } else {
                    assignedBase = static_cast<UInt64>(raw & ~0xFU);
                    if (is64Bit) {
                        const UInt32 high = device->configRead32(registerOffset + 4U);
                        dictionaryNumber(entry, "AssignedBaseHigh", high, 32);
                        assignedBase |= static_cast<UInt64>(high) << 32U;
                        continuationOf64BitBar = true;
                    }
                }
                dictionaryNumber(entry, "AssignedBase", assignedBase, 64);
            }

            IOMemoryDescriptor *descriptor =
                device->getDeviceMemoryWithRegister(static_cast<UInt8>(registerOffset));
            if (descriptor != nullptr) {
                dictionaryBoolean(entry, "HasIODeviceMemory", true);
                dictionaryNumber(entry, "PhysicalAddress",
                                 descriptor->getPhysicalAddress(), 64);
                dictionaryNumber(entry, "Length", descriptor->getLength(), 64);
            } else {
                dictionaryBoolean(entry, "HasIODeviceMemory", false);
            }

            bars->setObject(entry);
            entry->release();
        }
        owner->setProperty("TPBARDescriptors", bars);
        bars->release();
    }

    const UInt32 memoryCount = device->getDeviceMemoryCount();
    publishNumber(owner, "TPMemoryRangeCount", memoryCount, 32);
    OSArray *ranges = OSArray::withCapacity(memoryCount);
    if (ranges == nullptr) return;

    for (UInt32 index = 0; index < memoryCount; ++index) {
        IOMemoryDescriptor *descriptor = device->getDeviceMemoryWithIndex(index);
        if (descriptor == nullptr) continue;
        OSDictionary *entry = OSDictionary::withCapacity(4);
        if (entry == nullptr) continue;
        dictionaryNumber(entry, "Index", index, 32);
        dictionaryNumber(entry, "PhysicalAddress", descriptor->getPhysicalAddress(), 64);
        dictionaryNumber(entry, "Length", descriptor->getLength(), 64);
        ranges->setObject(entry);
        entry->release();
    }

    owner->setProperty("TPMemoryRanges", ranges);
    ranges->release();
}

}
