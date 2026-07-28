#pragma once

#include <libkern/OSTypes.h>

namespace td {

// TuringProbe v0.2.1 authorises exactly three 32-bit BAR0 reads.
// Adding an offset requires a source review, safety analysis, and a new build.
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

constexpr UInt32 kExpectedBar0Length = 0x01000000U; // 16 MiB, real-hardware verified.
constexpr UInt32 kMmioWhitelistReadCount = 3U;

struct MmioRegisterDefinition {
    const char *name;
    UInt32 offset;
    UInt8 widthBytes;
};

constexpr MmioRegisterDefinition kMmioWhitelist[] = {
    {"NV_PMC_BOOT_1", kNvPmcBoot1Offset, 4U},
    {"NV_PMC_BOOT_0", kNvPmcBoot0Offset, 4U},
    {"NV_PEXTDEV_BOOT_0_STRAP", kNvPextdevBoot0StrapOffset, 4U},
};

static_assert(sizeof(kMmioWhitelist) / sizeof(kMmioWhitelist[0]) ==
                  kMmioWhitelistReadCount,
              "MMIO whitelist count mismatch");
static_assert(kNvPextdevBoot0StrapOffset + 4U <= kExpectedBar0Length,
              "whitelisted register is outside BAR0");

} // namespace td
