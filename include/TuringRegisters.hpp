#pragma once

#include <libkern/OSTypes.h>

namespace td {

// Identity whitelist inherited from the real-hardware-verified v0.2.1 stage.
constexpr UInt32 kNvPmcBoot0Offset = 0x000000U;
constexpr UInt32 kNvPmcBoot1Offset = 0x000004U;
constexpr UInt32 kNvPextdevBoot0StrapOffset = 0x101000U;

constexpr UInt32 kTu116ChipsetId = 0x168U;
constexpr UInt32 kBoot0ChipsetMask = 0x1FF00000U;
constexpr UInt32 kBoot0ChipsetShift = 20U;
constexpr UInt32 kBoot0RevisionMask = 0x000000FFU;
constexpr UInt32 kBoot1VgpuMask = 0x00030000U;
constexpr UInt32 kBoot1BigEndianValue = 0x01000001U;
constexpr UInt32 kCrystalSelectMask = 0x00400040U;

// TU116 uses Nouveau's gk104_top_parse implementation. That implementation
// performs a bounded read of exactly 64 dwords beginning at 0x022700.
constexpr UInt32 kTopTableBaseOffset = 0x022700U;
constexpr UInt32 kTopTableWordCount = 64U;
constexpr UInt32 kTopTableByteLength = kTopTableWordCount * 4U;

constexpr UInt32 kTopWordKindMask = 0x00000003U;
constexpr UInt32 kTopWordKindNotValid = 0x00000000U;
constexpr UInt32 kTopWordKindData = 0x00000001U;
constexpr UInt32 kTopWordKindEnum = 0x00000002U;
constexpr UInt32 kTopWordKindEngineType = 0x00000003U;
constexpr UInt32 kTopWordContinuationBit = 0x80000000U;

constexpr UInt32 kTopDataInstanceMask = 0x3C000000U;
constexpr UInt32 kTopDataInstanceShift = 26U;
constexpr UInt32 kTopDataAddressMask = 0x00FFF000U;
constexpr UInt32 kTopDataFaultValidBit = 0x00000004U;
constexpr UInt32 kTopDataFaultMask = 0x000003F8U;
constexpr UInt32 kTopDataFaultShift = 3U;

constexpr UInt32 kTopEnumEngineValidBit = 0x00000020U;
constexpr UInt32 kTopEnumEngineMask = 0x3C000000U;
constexpr UInt32 kTopEnumEngineShift = 26U;
constexpr UInt32 kTopEnumRunlistValidBit = 0x00000010U;
constexpr UInt32 kTopEnumRunlistMask = 0x01E00000U;
constexpr UInt32 kTopEnumRunlistShift = 21U;
constexpr UInt32 kTopEnumInterruptValidBit = 0x00000008U;
constexpr UInt32 kTopEnumInterruptMask = 0x000F8000U;
constexpr UInt32 kTopEnumInterruptShift = 15U;
constexpr UInt32 kTopEnumResetValidBit = 0x00000004U;
constexpr UInt32 kTopEnumResetMask = 0x00003E00U;
constexpr UInt32 kTopEnumResetShift = 9U;

constexpr UInt32 kTopEngineTypeMask = 0x7FFFFFFCU;
constexpr UInt32 kTopEngineTypeShift = 2U;

constexpr UInt32 kExpectedBar0Length = 0x01000000U; // 16 MiB, real-hardware verified.
constexpr UInt32 kIdentityMmioReadCount = 3U;
constexpr UInt32 kTopInventoryMmioReadCount = kTopTableWordCount;
constexpr UInt32 kExpandedMmioReadCount =
    kIdentityMmioReadCount + kTopInventoryMmioReadCount;

struct MmioRegisterDefinition {
    const char *name;
    UInt32 offset;
    UInt8 widthBytes;
};

constexpr MmioRegisterDefinition kIdentityMmioWhitelist[] = {
    {"NV_PMC_BOOT_1", kNvPmcBoot1Offset, 4U},
    {"NV_PMC_BOOT_0", kNvPmcBoot0Offset, 4U},
    {"NV_PEXTDEV_BOOT_0_STRAP", kNvPextdevBoot0StrapOffset, 4U},
};

static_assert(sizeof(kIdentityMmioWhitelist) /
                  sizeof(kIdentityMmioWhitelist[0]) ==
                  kIdentityMmioReadCount,
              "identity MMIO whitelist count mismatch");
static_assert(kNvPextdevBoot0StrapOffset + 4U <= kExpectedBar0Length,
              "identity register is outside BAR0");
static_assert(kTopTableBaseOffset + kTopTableByteLength <=
                  kExpectedBar0Length,
              "TOP table is outside BAR0");
static_assert(kExpandedMmioReadCount == 67U,
              "expanded MMIO read count must remain exactly 67");

} // namespace td
