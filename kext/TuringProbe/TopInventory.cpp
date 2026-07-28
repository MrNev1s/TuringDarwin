#include "TopInventory.hpp"

#include <libkern/OSByteOrder.h>
#include <libkern/c++/OSArray.h>
#include <libkern/c++/OSData.h>
#include <libkern/c++/OSDictionary.h>
#include <libkern/c++/OSNumber.h>
#include <libkern/c++/OSString.h>

#include "PCIConfig.hpp"
#include "../../include/TuringRegisters.hpp"

namespace td {
namespace {

constexpr UInt32 kUnsetField = 0xFFFFFFFFU;

struct TopRecord {
    UInt32 startWord;
    UInt32 endWord;
    UInt32 rawType;
    UInt32 instance;
    UInt32 address;
    UInt32 fault;
    UInt32 engine;
    UInt32 runlist;
    UInt32 interrupt;
    UInt32 reset;
    bool hasType;
    bool hasAddress;
    bool hasFault;
    bool hasEngine;
    bool hasRunlist;
    bool hasInterrupt;
    bool hasReset;
};

void resetRecord(TopRecord &record, UInt32 startWord) {
    record.startWord = startWord;
    record.endWord = startWord;
    record.rawType = kUnsetField;
    record.instance = 0U;
    record.address = 0U;
    record.fault = 0U;
    record.engine = 0U;
    record.runlist = 0U;
    record.interrupt = 0U;
    record.reset = 0U;
    record.hasType = false;
    record.hasAddress = false;
    record.hasFault = false;
    record.hasEngine = false;
    record.hasRunlist = false;
    record.hasInterrupt = false;
    record.hasReset = false;
}

UInt32 readTopWord32(const void *bar0, UInt32 index) {
    return OSReadLittleInt32(bar0, kTopTableBaseOffset + index * 4U);
}

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

const char *engineTypeName(UInt32 type) {
    switch (type) {
        case 0x00U: return "GR";
        case 0x01U: return "CE";
        case 0x02U: return "CE";
        case 0x03U: return "CE";
        case 0x08U: return "MSPDEC";
        case 0x09U: return "MSPPP";
        case 0x0AU: return "MSVLD";
        case 0x0BU: return "MSENC";
        case 0x0CU: return "VIC";
        case 0x0DU: return "SEC2";
        case 0x0EU: return "NVENC";
        case 0x0FU: return "NVENC";
        case 0x10U: return "NVDEC";
        case 0x12U: return "IOCTRL";
        case 0x13U: return "CE";
        case 0x14U: return "GSP";
        case 0x15U: return "NVJPG";
        default: return "UNKNOWN";
    }
}

bool engineTypeKnown(UInt32 type) {
    return engineTypeName(type)[0] != 'U';
}

UInt32 effectiveInstance(UInt32 type, UInt32 parsedInstance) {
    switch (type) {
        case 0x01U: return 0U;
        case 0x02U: return 1U;
        case 0x03U: return 2U;
        case 0x0FU: return 1U;
        case 0x0EU:
        case 0x10U:
        case 0x12U:
        case 0x13U:
        case 0x15U:
            return parsedInstance;
        default:
            return 0U;
    }
}

bool appendRecord(OSArray *devices, const TopRecord &record) {
    if (devices == nullptr || !record.hasType) return false;

    OSDictionary *entry = OSDictionary::withCapacity(24);
    if (entry == nullptr) return false;

    const bool known = engineTypeKnown(record.rawType);
    dictionaryNumber(entry, "StartWordIndex", record.startWord, 8);
    dictionaryNumber(entry, "EndWordIndex", record.endWord, 8);
    dictionaryNumber(entry, "RawType", record.rawType, 32);
    dictionaryString(entry, "Name", engineTypeName(record.rawType));
    dictionaryBoolean(entry, "KnownType", known);
    dictionaryNumber(entry, "ParsedInstance", record.instance, 8);
    dictionaryNumber(entry, "Instance",
                     effectiveInstance(record.rawType, record.instance), 8);
    dictionaryNumber(entry, "Address", record.address, 32);
    dictionaryBoolean(entry, "HasAddress", record.hasAddress);
    dictionaryNumber(entry, "Fault", record.fault, 16);
    dictionaryBoolean(entry, "HasFault", record.hasFault);
    dictionaryNumber(entry, "Engine", record.engine, 8);
    dictionaryBoolean(entry, "HasEngine", record.hasEngine);
    dictionaryNumber(entry, "Runlist", record.runlist, 8);
    dictionaryBoolean(entry, "HasRunlist", record.hasRunlist);
    dictionaryNumber(entry, "Interrupt", record.interrupt, 8);
    dictionaryBoolean(entry, "HasInterrupt", record.hasInterrupt);
    dictionaryNumber(entry, "Reset", record.reset, 8);
    dictionaryBoolean(entry, "HasReset", record.hasReset);

    devices->setObject(entry);
    entry->release();
    return true;
}

} // namespace

bool performReadOnlyTopInventory(const void *bar0, IOService *owner) {
    if (bar0 == nullptr || owner == nullptr) return false;

    UInt32 rawWords[kTopTableWordCount] {};
    OSArray *devices = OSArray::withCapacity(16);
    if (devices == nullptr) return false;

    UInt32 notValidWords = 0U;
    UInt32 dataWords = 0U;
    UInt32 enumWords = 0U;
    UInt32 typeWords = 0U;
    UInt32 decodedRecords = 0U;
    UInt32 knownRecords = 0U;
    UInt32 unknownRecords = 0U;
    UInt32 malformedRecords = 0U;
    bool recordActive = false;
    TopRecord record {};

    // Exact Nouveau gk104_top_parse table extent: 64 fixed dwords beginning
    // at 0x022700. This is a finite inventory walk, not polling.
    for (UInt32 index = 0U; index < kTopTableWordCount; ++index) {
        const UInt32 data = readTopWord32(bar0, index);
        rawWords[index] = data;
        const UInt32 kind = data & kTopWordKindMask;

        if (kind == kTopWordKindNotValid) {
            ++notValidWords;
            continue;
        }

        if (!recordActive) {
            resetRecord(record, index);
            recordActive = true;
        }
        record.endWord = index;

        switch (kind) {
            case kTopWordKindData:
                ++dataWords;
                record.instance = (data & kTopDataInstanceMask) >>
                                  kTopDataInstanceShift;
                record.address = data & kTopDataAddressMask;
                record.hasAddress = true;
                if ((data & kTopDataFaultValidBit) != 0U) {
                    record.fault = (data & kTopDataFaultMask) >>
                                   kTopDataFaultShift;
                    record.hasFault = true;
                }
                break;
            case kTopWordKindEnum:
                ++enumWords;
                if ((data & kTopEnumEngineValidBit) != 0U) {
                    record.engine = (data & kTopEnumEngineMask) >>
                                    kTopEnumEngineShift;
                    record.hasEngine = true;
                }
                if ((data & kTopEnumRunlistValidBit) != 0U) {
                    record.runlist = (data & kTopEnumRunlistMask) >>
                                     kTopEnumRunlistShift;
                    record.hasRunlist = true;
                }
                if ((data & kTopEnumInterruptValidBit) != 0U) {
                    record.interrupt = (data & kTopEnumInterruptMask) >>
                                       kTopEnumInterruptShift;
                    record.hasInterrupt = true;
                }
                if ((data & kTopEnumResetValidBit) != 0U) {
                    record.reset = (data & kTopEnumResetMask) >>
                                   kTopEnumResetShift;
                    record.hasReset = true;
                }
                break;
            case kTopWordKindEngineType:
                ++typeWords;
                record.rawType = (data & kTopEngineTypeMask) >>
                                 kTopEngineTypeShift;
                record.hasType = true;
                break;
            default:
                ++malformedRecords;
                recordActive = false;
                break;
        }

        if (!recordActive || (data & kTopWordContinuationBit) != 0U) continue;

        if (appendRecord(devices, record)) {
            ++decodedRecords;
            if (engineTypeKnown(record.rawType)) ++knownRecords;
            else ++unknownRecords;
        } else {
            ++malformedRecords;
        }
        recordActive = false;
    }

    if (recordActive) ++malformedRecords;

    OSData *raw = OSData::withBytes(rawWords, sizeof(rawWords));
    if (raw != nullptr) {
        owner->setProperty("TPTopRawTable", raw);
        raw->release();
    }

    owner->setProperty("TPTopDevices", devices);
    devices->release();

    const bool valid = decodedRecords > 0U && malformedRecords == 0U;
    publishNumber(owner, "TPTopTableBaseOffset", kTopTableBaseOffset, 32);
    publishNumber(owner, "TPTopTableWordCount", kTopTableWordCount, 32);
    publishNumber(owner, "TPTopMMIOReadCount", kTopTableWordCount, 32);
    publishNumber(owner, "TPTopNotValidWordCount", notValidWords, 32);
    publishNumber(owner, "TPTopDataWordCount", dataWords, 32);
    publishNumber(owner, "TPTopEnumWordCount", enumWords, 32);
    publishNumber(owner, "TPTopEngineTypeWordCount", typeWords, 32);
    publishNumber(owner, "TPTopDecodedDeviceCount", decodedRecords, 32);
    publishNumber(owner, "TPTopKnownDeviceCount", knownRecords, 32);
    publishNumber(owner, "TPTopUnknownDeviceCount", unknownRecords, 32);
    publishNumber(owner, "TPTopMalformedRecordCount", malformedRecords, 32);
    publishBoolean(owner, "TPTopDecodeValid", valid);
    publishBoolean(owner, "TPTopReadCompleted", true);
    owner->setProperty("TPTopInventorySchemaVersion", "1");
    owner->setProperty("TPTopInventorySource",
                       "Linux Nouveau gk104_top_parse: 64 dwords at 0x022700");
    return valid;
}

} // namespace td
