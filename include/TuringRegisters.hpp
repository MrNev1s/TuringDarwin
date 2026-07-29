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


// TU102/TU116 inherits Nouveau's gp102_fb_vidmem_size() decoder. It reads
// one static capacity encoding from BAR0+0x100CE0.
constexpr UInt32 kNvPfbVidmemSizeOffset = 0x100CE0U;
constexpr UInt32 kPfbVidmemMagnitudeMask = 0x000003F0U;
constexpr UInt32 kPfbVidmemMagnitudeShift = 4U;
constexpr UInt32 kPfbVidmemScaleMask = 0x0000000FU;
constexpr UInt32 kPfbVidmemReducedCapacityBit = 0x40000000U;
constexpr UInt64 kExpectedTargetVidmemBytes = 6ULL * 1024ULL * 1024ULL * 1024ULL;

// Source-backed architecture profile from Nouveau's tu102_mmu and
// tu102_vmm/gp100_vmm definitions. These constants are metadata only and do
// not cause extra MMIO reads.
constexpr UInt32 kTu102MmuDmaAddressBits = 47U;
// The descriptor hierarchy covers 2+9+9+8+9+12 = 49 virtual-address bits
// for 4 KiB pages and 2+9+9+8+5+16 = 49 bits for 64 KiB pages.
constexpr UInt32 kTu102MmuVirtualAddressBits = 49U;
constexpr UInt32 kTu102MmuKindCount = 16U;
constexpr UInt32 kTu102MmuInvalidKind = 0x07U;
constexpr UInt32 kTu102SmallPageShift = 12U;
constexpr UInt32 kTu102SmallPageKiB = 4U;
constexpr UInt32 kTu102BigPageShift = 16U;
constexpr UInt32 kTu102BigPageKiB = 64U;
constexpr UInt8 kTu102MmuKindMap[kTu102MmuKindCount] = {
    0x00U, 0x01U, 0x02U, 0x03U, 0x04U, 0x05U, 0x06U, 0x07U,
    0x06U, 0x06U, 0x02U, 0x01U, 0x03U, 0x04U, 0x05U, 0x07U,
};

constexpr UInt32 kExpectedBar0Length = 0x01000000U; // 16 MiB, real-hardware verified.
constexpr UInt32 kIdentityMmioReadCount = 3U;
constexpr UInt32 kTopInventoryMmioReadCount = kTopTableWordCount;
constexpr UInt32 kFbMmuInventoryMmioReadCount = 1U;
constexpr UInt32 kExpandedTopMmioReadCount =
    kIdentityMmioReadCount + kTopInventoryMmioReadCount;
constexpr UInt32 kExpandedFbMmuMmioReadCount =
    kIdentityMmioReadCount + kFbMmuInventoryMmioReadCount;

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
static_assert(kExpandedTopMmioReadCount == 67U,
              "TOP expanded MMIO read count must remain exactly 67");
static_assert(kExpandedFbMmuMmioReadCount == 4U,
              "FB/MMU expanded MMIO read count must remain exactly 4");
static_assert(kNvPfbVidmemSizeOffset + 4U <= kExpectedBar0Length,
              "FB capacity register is outside BAR0");
static_assert(sizeof(kTu102MmuKindMap) == kTu102MmuKindCount,
              "TU102 MMU kind-map size mismatch");

static_assert((1U << (kTu102SmallPageShift - 10U)) == kTu102SmallPageKiB,
              "small-page shift/size mismatch");
static_assert((1U << (kTu102BigPageShift - 10U)) == kTu102BigPageKiB,
              "big-page shift/size mismatch");

} // namespace td
