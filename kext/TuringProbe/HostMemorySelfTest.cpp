#include "HostMemorySelfTest.hpp"

#include <IOKit/IOLib.h>

#include "Logging.hpp"
#include "PCIConfig.hpp"

#ifndef TURINGPROBE_ENABLE_HOST_MEMORY_TEST
#define TURINGPROBE_ENABLE_HOST_MEMORY_TEST 0
#endif

namespace td {
namespace {

constexpr vm_size_t kHostMemoryPageSize = 4096U;
constexpr vm_size_t kHostMemoryGuardSize = kHostMemoryPageSize;
constexpr vm_size_t kHostMemoryPayloadSize = kHostMemoryPageSize;
constexpr vm_size_t kHostMemoryAllocationSize =
    kHostMemoryGuardSize + kHostMemoryPayloadSize + kHostMemoryGuardSize;
constexpr vm_size_t kHostMemoryAlignment = kHostMemoryPageSize;
constexpr UInt8 kPrefixCanary = 0xA5U;
constexpr UInt8 kSuffixCanary = 0x5AU;
constexpr UInt64 kFnvOffsetBasis = 0xCBF29CE484222325ULL;
constexpr UInt64 kFnvPrime = 0x00000100000001B3ULL;
constexpr UInt64 kExpectedPayloadChecksum = 0xACAC786CC2682325ULL;

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
    for (vm_size_t index = 0; index < kHostMemoryPayloadSize; ++index) {
        payload[index] = payloadByte(index);
    }
}

bool verifyPayload(const UInt8 *payload) {
    if (payload == nullptr) return false;
    for (vm_size_t index = 0; index < kHostMemoryPayloadSize; ++index) {
        if (payload[index] != payloadByte(index)) return false;
    }
    return true;
}

UInt64 checksumPayload(const UInt8 *payload) {
    if (payload == nullptr) return 0U;
    UInt64 checksum = kFnvOffsetBasis;
    for (vm_size_t index = 0; index < kHostMemoryPayloadSize; ++index) {
        checksum ^= static_cast<UInt64>(payload[index]);
        checksum *= kFnvPrime;
    }
    return checksum;
}

} // namespace

bool performHostMemorySelfTest(IOService *owner) {
#if TURINGPROBE_ENABLE_HOST_MEMORY_TEST != 1
    if (owner != nullptr) {
        publishBoolean(owner, "TPHostMemoryCompileGateEnabled", false);
    }
    return false;
#else
    if (owner == nullptr) return false;

    publishBoolean(owner, "TPHostMemoryCompileGateEnabled", true);
    publishBoolean(owner, "TPHostMemoryRequested", true);
    publishNumber(owner, "TPHostMemoryPageSize", kHostMemoryPageSize, 32);
    publishNumber(owner, "TPHostMemoryGuardSize", kHostMemoryGuardSize, 32);
    publishNumber(owner, "TPHostMemoryPayloadSize", kHostMemoryPayloadSize, 32);
    publishNumber(owner, "TPHostMemoryAllocationSize", kHostMemoryAllocationSize, 32);
    publishNumber(owner, "TPHostMemoryAlignment", kHostMemoryAlignment, 32);
    publishNumber(owner, "TPHostMemoryExpectedChecksum",
                  kExpectedPayloadChecksum, 64);
    owner->setProperty("TPHostMemoryAllocator", "IOMallocAligned/IOFreeAligned");
    owner->setProperty("TPHostMemoryAddressProvenance", "CPU virtual only");
    publishBoolean(owner, "TPHostMemoryPhysicalAddressQueried", false);
    publishBoolean(owner, "TPHostMemoryDeviceAccessible", false);

    void *allocation = IOMallocAligned(kHostMemoryAllocationSize,
                                       kHostMemoryAlignment);
    UInt8 *base = static_cast<UInt8 *>(allocation);
    UInt8 *prefix = base;
    UInt8 *payload = base == nullptr ? nullptr : base + kHostMemoryGuardSize;
    UInt8 *suffix = payload == nullptr ? nullptr : payload + kHostMemoryPayloadSize;

    const bool allocationSucceeded = allocation != nullptr;
    const bool alignmentValid = allocationSucceeded &&
        ((reinterpret_cast<uintptr_t>(allocation) &
          (static_cast<uintptr_t>(kHostMemoryAlignment) - 1U)) == 0U);

    bool initialZeroVerified = false;
    bool prefixValidAfterWrite = false;
    bool suffixValidAfterWrite = false;
    bool payloadReadbackMatched = false;
    bool checksumMatched = false;
    bool payloadZeroized = false;
    bool prefixValidAfterZeroize = false;
    bool suffixValidAfterZeroize = false;
    bool entireAllocationZeroBeforeFree = false;
    bool allocationFreed = false;
    UInt64 payloadChecksum = 0U;
    const char *failure = nullptr;

    if (!allocationSucceeded) {
        failure = "IOMallocAligned returned null";
    } else if (!alignmentValid) {
        failure = "allocation is not 4096-byte aligned";
    } else {
        fillBytes(base, kHostMemoryAllocationSize, 0U);
        initialZeroVerified = bytesEqual(base, kHostMemoryAllocationSize, 0U);
        if (!initialZeroVerified) {
            failure = "initial zero verification failed";
        }
    }

    if (failure == nullptr) {
        fillBytes(prefix, kHostMemoryGuardSize, kPrefixCanary);
        fillBytes(suffix, kHostMemoryGuardSize, kSuffixCanary);
        writePayload(payload);

        payloadReadbackMatched = verifyPayload(payload);
        payloadChecksum = checksumPayload(payload);
        checksumMatched = payloadChecksum == kExpectedPayloadChecksum;
        prefixValidAfterWrite = bytesEqual(prefix, kHostMemoryGuardSize,
                                           kPrefixCanary);
        suffixValidAfterWrite = bytesEqual(suffix, kHostMemoryGuardSize,
                                           kSuffixCanary);

        if (!payloadReadbackMatched) {
            failure = "payload readback mismatch";
        } else if (!checksumMatched) {
            failure = "payload checksum mismatch";
        } else if (!prefixValidAfterWrite || !suffixValidAfterWrite) {
            failure = "guard canary changed during payload write";
        }
    }

    if (allocationSucceeded) {
        fillBytes(payload, kHostMemoryPayloadSize, 0U);
        payloadZeroized = bytesEqual(payload, kHostMemoryPayloadSize, 0U);
        prefixValidAfterZeroize = bytesEqual(prefix, kHostMemoryGuardSize,
                                             kPrefixCanary);
        suffixValidAfterZeroize = bytesEqual(suffix, kHostMemoryGuardSize,
                                             kSuffixCanary);
        if (failure == nullptr && !payloadZeroized) {
            failure = "payload zeroization verification failed";
        }
        if (failure == nullptr &&
            (!prefixValidAfterZeroize || !suffixValidAfterZeroize)) {
            failure = "guard canary changed during payload zeroization";
        }

        fillBytes(base, kHostMemoryAllocationSize, 0U);
        entireAllocationZeroBeforeFree =
            bytesEqual(base, kHostMemoryAllocationSize, 0U);
        if (failure == nullptr && !entireAllocationZeroBeforeFree) {
            failure = "full allocation cleanup verification failed";
        }

        IOFreeAligned(allocation, kHostMemoryAllocationSize);
        allocation = nullptr;
        base = nullptr;
        prefix = nullptr;
        payload = nullptr;
        suffix = nullptr;
        allocationFreed = true;
    }

    const bool completed = failure == nullptr && allocationFreed;
    publishBoolean(owner, "TPHostMemoryAllocationSucceeded", allocationSucceeded);
    publishBoolean(owner, "TPHostMemoryAlignmentValid", alignmentValid);
    publishBoolean(owner, "TPHostMemoryInitialZeroVerified", initialZeroVerified);
    publishNumber(owner, "TPHostMemoryPayloadBytesWritten",
                  payloadReadbackMatched ? kHostMemoryPayloadSize : 0U, 32);
    publishNumber(owner, "TPHostMemoryPayloadBytesReadBack",
                  payloadReadbackMatched ? kHostMemoryPayloadSize : 0U, 32);
    publishNumber(owner, "TPHostMemoryPayloadChecksum", payloadChecksum, 64);
    publishBoolean(owner, "TPHostMemoryChecksumMatched", checksumMatched);
    publishBoolean(owner, "TPHostMemoryPayloadReadbackMatched",
                   payloadReadbackMatched);
    publishBoolean(owner, "TPHostMemoryPrefixCanaryValidAfterWrite",
                   prefixValidAfterWrite);
    publishBoolean(owner, "TPHostMemorySuffixCanaryValidAfterWrite",
                   suffixValidAfterWrite);
    publishBoolean(owner, "TPHostMemoryPayloadZeroized", payloadZeroized);
    publishBoolean(owner, "TPHostMemoryPrefixCanaryValidAfterZeroize",
                   prefixValidAfterZeroize);
    publishBoolean(owner, "TPHostMemorySuffixCanaryValidAfterZeroize",
                   suffixValidAfterZeroize);
    publishBoolean(owner, "TPHostMemoryEntireAllocationZeroBeforeFree",
                   entireAllocationZeroBeforeFree);
    publishBoolean(owner, "TPHostMemoryAllocationFreed", allocationFreed);
    publishBoolean(owner, "TPHostMemoryCompleted", completed);
    if (failure != nullptr) {
        owner->setProperty("TPHostMemoryFailureReason", failure);
    }

    TD_LOG("host-memory self-test allocation=%s aligned=%s readback=%s checksum=%016llx zeroized=%s freed=%s",
           allocationSucceeded ? "yes" : "no",
           alignmentValid ? "yes" : "no",
           payloadReadbackMatched ? "yes" : "no",
           static_cast<unsigned long long>(payloadChecksum),
           payloadZeroized ? "yes" : "no",
           allocationFreed ? "yes" : "no");
    return completed;
#endif
}

} // namespace td
