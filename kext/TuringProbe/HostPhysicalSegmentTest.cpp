#include "HostPhysicalSegmentTest.hpp"

#include <IOKit/IOBufferMemoryDescriptor.h>

#include "Logging.hpp"
#include "PCIConfig.hpp"

#ifndef TURINGPROBE_ENABLE_HOST_PHYSICAL_TEST
#define TURINGPROBE_ENABLE_HOST_PHYSICAL_TEST 0
#endif

namespace td {
namespace {

constexpr vm_size_t kDescriptorCapacity = 4096U;
constexpr vm_size_t kDescriptorAlignment = 4096U;
constexpr vm_size_t kPrefixGuardSize = 64U;
constexpr vm_size_t kSuffixGuardSize = 64U;
constexpr vm_size_t kPayloadSize =
    kDescriptorCapacity - kPrefixGuardSize - kSuffixGuardSize;
constexpr UInt8 kPrefixCanary = 0xC3U;
constexpr UInt8 kSuffixCanary = 0x3CU;
constexpr UInt64 kFnvOffsetBasis = 0xCBF29CE484222325ULL;
constexpr UInt64 kFnvPrime = 0x00000100000001B3ULL;
constexpr UInt64 kExpectedPayloadChecksum = 0xBB8BA5B0A94B2525ULL;
constexpr UInt64 kHostPhysicalAddressBits = 47U;
constexpr UInt64 kHostPhysicalAddressLimit = 1ULL << kHostPhysicalAddressBits;
constexpr IOOptionBits kDescriptorOptions =
    kIODirectionNone | kIOMemoryMapperNone;

void fillBytes(UInt8 *bytes, vm_size_t length, UInt8 value) {
    if (bytes == nullptr) return;
    for (vm_size_t index = 0; index < length; ++index) {
        bytes[index] = value;
    }
}

bool bytesEqual(const UInt8 *bytes, vm_size_t length, UInt8 value) {
    if (bytes == nullptr) return false;
    for (vm_size_t index = 0; index < length; ++index) {
        if (bytes[index] != value) return false;
    }
    return true;
}

UInt8 payloadByte(vm_size_t index) {
    return static_cast<UInt8>((index * 131U + 0x5DU) & 0xFFU);
}

void writePayload(UInt8 *payload) {
    if (payload == nullptr) return;
    for (vm_size_t index = 0; index < kPayloadSize; ++index) {
        payload[index] = payloadByte(index);
    }
}

bool verifyPayload(const UInt8 *payload) {
    if (payload == nullptr) return false;
    for (vm_size_t index = 0; index < kPayloadSize; ++index) {
        if (payload[index] != payloadByte(index)) return false;
    }
    return true;
}

UInt64 checksumPayload(const UInt8 *payload) {
    if (payload == nullptr) return 0U;
    UInt64 checksum = kFnvOffsetBasis;
    for (vm_size_t index = 0; index < kPayloadSize; ++index) {
        checksum ^= static_cast<UInt64>(payload[index]);
        checksum *= kFnvPrime;
    }
    return checksum;
}

bool physicalRangeWithin47Bits(addr64_t address, IOByteCount length) {
    if (address == 0U || length == 0U) return false;
    const UInt64 start = static_cast<UInt64>(address);
    const UInt64 span = static_cast<UInt64>(length);
    if (start >= kHostPhysicalAddressLimit) return false;
    if (span > kHostPhysicalAddressLimit) return false;
    return start <= kHostPhysicalAddressLimit - span;
}

} // namespace

bool performHostPhysicalSegmentTest(IOService *owner) {
#if TURINGPROBE_ENABLE_HOST_PHYSICAL_TEST != 1
    if (owner != nullptr) {
        publishBoolean(owner, "TPHostPhysicalCompileGateEnabled", false);
    }
    return false;
#else
    if (owner == nullptr) return false;

    publishBoolean(owner, "TPHostPhysicalCompileGateEnabled", true);
    publishBoolean(owner, "TPHostPhysicalRequested", true);
    publishNumber(owner, "TPHostPhysicalDescriptorCapacity",
                  kDescriptorCapacity, 32);
    publishNumber(owner, "TPHostPhysicalDescriptorAlignment",
                  kDescriptorAlignment, 32);
    publishNumber(owner, "TPHostPhysicalPrefixGuardSize",
                  kPrefixGuardSize, 32);
    publishNumber(owner, "TPHostPhysicalPayloadSize", kPayloadSize, 32);
    publishNumber(owner, "TPHostPhysicalSuffixGuardSize",
                  kSuffixGuardSize, 32);
    publishNumber(owner, "TPHostPhysicalAddressBits",
                  kHostPhysicalAddressBits, 32);
    publishNumber(owner, "TPHostPhysicalExpectedChecksum",
                  kExpectedPayloadChecksum, 64);
    publishNumber(owner, "TPHostPhysicalDescriptorOptions",
                  kDescriptorOptions, 32);
    owner->setProperty("TPHostPhysicalDescriptorClass",
                       "IOBufferMemoryDescriptor");
    owner->setProperty("TPHostPhysicalCachePolicy", "default/copyback");
    owner->setProperty("TPHostPhysicalSegmentType", "raw host physical");
    publishBoolean(owner, "TPHostPhysicalMapperNone", true);
    publishBoolean(owner, "TPHostPhysicalPrepareCalled", false);
    publishBoolean(owner, "TPHostPhysicalCompleteCalled", false);
    publishBoolean(owner, "TPHostPhysicalDeviceMapped", false);
    publishBoolean(owner, "TPHostPhysicalDMACommandCreated", false);

    IOBufferMemoryDescriptor *descriptor =
        IOBufferMemoryDescriptor::withOptions(
            kDescriptorOptions, kDescriptorCapacity, kDescriptorAlignment);
    UInt8 *base = descriptor == nullptr ? nullptr :
        static_cast<UInt8 *>(descriptor->getBytesNoCopy(
            0U, kDescriptorCapacity));
    UInt8 *prefix = base;
    UInt8 *payload = base == nullptr ? nullptr : base + kPrefixGuardSize;
    UInt8 *suffix = payload == nullptr ? nullptr : payload + kPayloadSize;

    const bool descriptorCreated = descriptor != nullptr;
    const bool capacityValid = descriptorCreated &&
        descriptor->getCapacity() == kDescriptorCapacity &&
        descriptor->getLength() == kDescriptorCapacity;
    const bool virtualAddressAvailable = base != nullptr;
    const bool virtualAlignmentValid = virtualAddressAvailable &&
        ((reinterpret_cast<uintptr_t>(base) &
          (static_cast<uintptr_t>(kDescriptorAlignment) - 1U)) == 0U);

    bool initialZeroVerified = false;
    bool payloadReadbackMatched = false;
    bool checksumMatched = false;
    bool prefixValidAfterWrite = false;
    bool suffixValidAfterWrite = false;
    bool physicalSegmentQueried = false;
    bool physicalAddressNonZero = false;
    bool physicalAddressPageAligned = false;
    bool physicalAddressWithin47 = false;
    bool physicalSegmentCoversDescriptor = false;
    bool payloadZeroized = false;
    bool prefixValidAfterZeroize = false;
    bool suffixValidAfterZeroize = false;
    bool entireDescriptorZeroBeforeRelease = false;
    bool descriptorReleased = false;
    UInt64 payloadChecksum = 0U;
    addr64_t physicalAddress = 0U;
    IOByteCount physicalSegmentLength = 0U;
    const char *failure = nullptr;

    if (!descriptorCreated) {
        failure = "IOBufferMemoryDescriptor::withOptions returned null";
    } else if (!capacityValid) {
        failure = "descriptor capacity or length is not exactly 4096";
    } else if (!virtualAddressAvailable) {
        failure = "getBytesNoCopy returned null";
    } else if (!virtualAlignmentValid) {
        failure = "descriptor virtual address is not 4096-byte aligned";
    } else {
        initialZeroVerified = bytesEqual(base, kDescriptorCapacity, 0U);
        if (!initialZeroVerified) {
            failure = "descriptor initial zero verification failed";
        }
    }

    if (failure == nullptr) {
        fillBytes(prefix, kPrefixGuardSize, kPrefixCanary);
        fillBytes(suffix, kSuffixGuardSize, kSuffixCanary);
        writePayload(payload);

        payloadReadbackMatched = verifyPayload(payload);
        payloadChecksum = checksumPayload(payload);
        checksumMatched = payloadChecksum == kExpectedPayloadChecksum;
        prefixValidAfterWrite = bytesEqual(prefix, kPrefixGuardSize,
                                           kPrefixCanary);
        suffixValidAfterWrite = bytesEqual(suffix, kSuffixGuardSize,
                                           kSuffixCanary);

        if (!payloadReadbackMatched) {
            failure = "descriptor payload readback mismatch";
        } else if (!checksumMatched) {
            failure = "descriptor payload checksum mismatch";
        } else if (!prefixValidAfterWrite || !suffixValidAfterWrite) {
            failure = "descriptor guard changed during payload write";
        }
    }

    if (failure == nullptr) {
        physicalAddress = descriptor->getPhysicalSegment(
            0U, &physicalSegmentLength, kIOMemoryMapperNone);
        physicalSegmentQueried = true;
        physicalAddressNonZero = physicalAddress != 0U;
        physicalAddressPageAligned = physicalAddressNonZero &&
            ((static_cast<UInt64>(physicalAddress) &
              (static_cast<UInt64>(kDescriptorAlignment) - 1U)) == 0U);
        physicalSegmentCoversDescriptor =
            physicalSegmentLength == kDescriptorCapacity;
        physicalAddressWithin47 = physicalRangeWithin47Bits(
            physicalAddress, physicalSegmentLength);

        if (!physicalAddressNonZero) {
            failure = "raw physical segment address is zero";
        } else if (!physicalAddressPageAligned) {
            failure = "raw physical segment address is not page aligned";
        } else if (!physicalSegmentCoversDescriptor) {
            failure = "raw physical segment does not cover exactly 4096 bytes";
        } else if (!physicalAddressWithin47) {
            failure = "raw physical segment exceeds TU116 47-bit address width";
        }
    }

    if (base != nullptr) {
        fillBytes(payload, kPayloadSize, 0U);
        payloadZeroized = bytesEqual(payload, kPayloadSize, 0U);
        prefixValidAfterZeroize = bytesEqual(prefix, kPrefixGuardSize,
                                             kPrefixCanary);
        suffixValidAfterZeroize = bytesEqual(suffix, kSuffixGuardSize,
                                             kSuffixCanary);
        if (failure == nullptr && !payloadZeroized) {
            failure = "descriptor payload zeroization failed";
        }
        if (failure == nullptr &&
            (!prefixValidAfterZeroize || !suffixValidAfterZeroize)) {
            failure = "descriptor guard changed during payload zeroization";
        }

        fillBytes(base, kDescriptorCapacity, 0U);
        entireDescriptorZeroBeforeRelease =
            bytesEqual(base, kDescriptorCapacity, 0U);
        if (failure == nullptr && !entireDescriptorZeroBeforeRelease) {
            failure = "full descriptor cleanup verification failed";
        }
    }

    if (descriptor != nullptr) {
        descriptor->release();
        descriptor = nullptr;
        base = nullptr;
        prefix = nullptr;
        payload = nullptr;
        suffix = nullptr;
        descriptorReleased = true;
    }

    const bool completed = failure == nullptr && descriptorReleased;
    publishBoolean(owner, "TPHostPhysicalDescriptorCreated", descriptorCreated);
    publishBoolean(owner, "TPHostPhysicalCapacityValid", capacityValid);
    publishBoolean(owner, "TPHostPhysicalVirtualAddressAvailable",
                   virtualAddressAvailable);
    publishBoolean(owner, "TPHostPhysicalVirtualAlignmentValid",
                   virtualAlignmentValid);
    publishBoolean(owner, "TPHostPhysicalInitialZeroVerified",
                   initialZeroVerified);
    publishNumber(owner, "TPHostPhysicalPayloadBytesWritten",
                  payloadReadbackMatched ? kPayloadSize : 0U, 32);
    publishNumber(owner, "TPHostPhysicalPayloadBytesReadBack",
                  payloadReadbackMatched ? kPayloadSize : 0U, 32);
    publishNumber(owner, "TPHostPhysicalPayloadChecksum",
                  payloadChecksum, 64);
    publishBoolean(owner, "TPHostPhysicalChecksumMatched", checksumMatched);
    publishBoolean(owner, "TPHostPhysicalPayloadReadbackMatched",
                   payloadReadbackMatched);
    publishBoolean(owner, "TPHostPhysicalPrefixCanaryValidAfterWrite",
                   prefixValidAfterWrite);
    publishBoolean(owner, "TPHostPhysicalSuffixCanaryValidAfterWrite",
                   suffixValidAfterWrite);
    publishBoolean(owner, "TPHostPhysicalSegmentQueried",
                   physicalSegmentQueried);
    publishNumber(owner, "TPHostPhysicalSegmentAddress",
                  static_cast<UInt64>(physicalAddress), 64);
    publishNumber(owner, "TPHostPhysicalSegmentLength",
                  static_cast<UInt64>(physicalSegmentLength), 64);
    publishNumber(owner, "TPHostPhysicalSegmentCount",
                  physicalSegmentCoversDescriptor ? 1U : 0U, 32);
    publishBoolean(owner, "TPHostPhysicalAddressNonZero",
                   physicalAddressNonZero);
    publishBoolean(owner, "TPHostPhysicalAddressPageAligned",
                   physicalAddressPageAligned);
    publishBoolean(owner, "TPHostPhysicalAddressWithin47Bits",
                   physicalAddressWithin47);
    publishBoolean(owner, "TPHostPhysicalSegmentCoversDescriptor",
                   physicalSegmentCoversDescriptor);
    publishBoolean(owner, "TPHostPhysicalPayloadZeroized", payloadZeroized);
    publishBoolean(owner, "TPHostPhysicalPrefixCanaryValidAfterZeroize",
                   prefixValidAfterZeroize);
    publishBoolean(owner, "TPHostPhysicalSuffixCanaryValidAfterZeroize",
                   suffixValidAfterZeroize);
    publishBoolean(owner, "TPHostPhysicalEntireDescriptorZeroBeforeRelease",
                   entireDescriptorZeroBeforeRelease);
    publishBoolean(owner, "TPHostPhysicalDescriptorReleased",
                   descriptorReleased);
    publishBoolean(owner, "TPHostPhysicalCompleted", completed);
    if (failure != nullptr) {
        owner->setProperty("TPHostPhysicalFailureReason", failure);
    }

    TD_LOG("host-physical descriptor created=%s readback=%s checksum=%016llx physical=0x%016llx length=%llu within47=%s released=%s",
           descriptorCreated ? "yes" : "no",
           payloadReadbackMatched ? "yes" : "no",
           static_cast<unsigned long long>(payloadChecksum),
           static_cast<unsigned long long>(physicalAddress),
           static_cast<unsigned long long>(physicalSegmentLength),
           physicalAddressWithin47 ? "yes" : "no",
           descriptorReleased ? "yes" : "no");
    return completed;
#endif
}

} // namespace td
