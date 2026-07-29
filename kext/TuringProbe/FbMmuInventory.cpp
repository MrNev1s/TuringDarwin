#include "FbMmuInventory.hpp"

#include <libkern/OSByteOrder.h>
#include <libkern/c++/OSData.h>

#include "Logging.hpp"
#include "PCIConfig.hpp"
#include "../../include/TuringRegisters.hpp"

#ifndef TURINGPROBE_ENABLE_FB_READ
#define TURINGPROBE_ENABLE_FB_READ 0
#endif

namespace td {
namespace {

UInt32 readFbCapacity32(const void *bar0) {
    return OSReadLittleInt32(bar0, kNvPfbVidmemSizeOffset);
}

} // namespace

bool performReadOnlyFbMmuInventory(const void *bar0, IOService *owner) {
#if TURINGPROBE_ENABLE_FB_READ != 1
    if (owner != nullptr) {
        publishBoolean(owner, "TPFBInventoryCompileGateEnabled", false);
    }
    return false;
#else
    if (bar0 == nullptr || owner == nullptr) return false;
    publishBoolean(owner, "TPFBInventoryCompileGateEnabled", true);

    // Nouveau's TU102/TU116 framebuffer path inherits gp102_fb_vidmem_size(),
    // which performs one plain read of 0x100CE0 and decodes magnitude/scale.
    const UInt32 raw = readFbCapacity32(bar0);
    const UInt32 magnitude =
        (raw & kPfbVidmemMagnitudeMask) >> kPfbVidmemMagnitudeShift;
    const UInt32 scale = raw & kPfbVidmemScaleMask;
    const bool reducedByOneSixteenth =
        (raw & kPfbVidmemReducedCapacityBit) != 0U;

    const UInt32 shift = scale + 20U;
    UInt64 nominalBytes = 0U;
    if (magnitude != 0U && shift < 64U) {
        nominalBytes = static_cast<UInt64>(magnitude) << shift;
    }
    const UInt64 decodedBytes = reducedByOneSixteenth ?
        (nominalBytes / 16U) * 15U : nominalBytes;
    const bool decodeValid =
        raw != 0U && raw != 0xFFFFFFFFU &&
        magnitude != 0U && shift < 64U &&
        decodedBytes != 0U;
    const bool matchesTarget =
        decodeValid && decodedBytes == kExpectedTargetVidmemBytes;

    publishNumber(owner, "TPFBVidmemSizeRaw", static_cast<UInt64>(raw), 64);
    publishNumber(owner, "TPFBVidmemMagnitude", magnitude, 8);
    publishNumber(owner, "TPFBVidmemScale", scale, 8);
    publishNumber(owner, "TPFBVidmemShift", shift, 8);
    publishBoolean(owner, "TPFBVidmemReducedByOneSixteenth",
                   reducedByOneSixteenth);
    publishNumber(owner, "TPFBVidmemNominalBytes", nominalBytes, 64);
    publishNumber(owner, "TPFBVidmemDecodedBytes", decodedBytes, 64);
    publishNumber(owner, "TPFBVidmemDecodedMiB", decodedBytes >> 20U, 64);
    publishBoolean(owner, "TPFBVidmemDecodeValid", decodeValid);
    publishBoolean(owner, "TPFBVidmemMatchesExpected6GiB", matchesTarget);
    publishNumber(owner, "TPFBInventoryMMIOReadCount",
                  kFbMmuInventoryMmioReadCount, 32);
    owner->setProperty("TPFBInventorySource",
        "Linux Nouveau gp102_fb_vidmem_size: one read at BAR0+0x100CE0");

    // These MMU values are architecture metadata from Nouveau's tu102_mmu
    // definition, not additional hardware register reads.
    publishNumber(owner, "TPMMUSourceDmaAddressBits",
                  kTu102MmuDmaAddressBits, 8);
    publishNumber(owner, "TPMMUSourceVirtualAddressBits",
                  kTu102MmuVirtualAddressBits, 8);
    publishNumber(owner, "TPMMUSourceKindCount", kTu102MmuKindCount, 8);
    publishNumber(owner, "TPMMUSourceInvalidKind", kTu102MmuInvalidKind, 8);
    publishBoolean(owner, "TPMMUSourceKindSystemMemory", true);
    publishNumber(owner, "TPMMUSourceSmallPageShift",
                  kTu102SmallPageShift, 8);
    publishNumber(owner, "TPMMUSourceSmallPageKiB",
                  kTu102SmallPageKiB, 16);
    publishNumber(owner, "TPMMUSourceBigPageShift",
                  kTu102BigPageShift, 8);
    publishNumber(owner, "TPMMUSourceBigPageKiB",
                  kTu102BigPageKiB, 16);
    // Compatibility property retained with the corrected value. v0.4.0
    // incorrectly confused page shift 16 with 16 KiB; shift 16 is 64 KiB.
    publishNumber(owner, "TPMMUSourceDefaultBigPageKiB",
                  kTu102BigPageKiB, 16);
    owner->setProperty("TPMMUSourceMmuClass", "NVIF_CLASS_MMU_GF100");
    owner->setProperty("TPMMUSourceMemoryClass", "NVIF_CLASS_MEM_GF100");
    owner->setProperty("TPMMUSourceVmmClass", "NVIF_CLASS_VMM_GP100");
    owner->setProperty("TPMMUSourceProfile",
        "Linux Nouveau TU102: 47-bit DMA, derived 49-bit VA, 4K/64K pages");

    OSData *kindMap = OSData::withBytes(kTu102MmuKindMap,
                                       sizeof(kTu102MmuKindMap));
    if (kindMap != nullptr) {
        owner->setProperty("TPMMUSourceKindMap", kindMap);
        kindMap->release();
    }

    TD_LOG("FB/MMU read-only inventory raw=%08x magnitude=%u scale=%u bytes=%llu target=%s",
           raw, magnitude, scale,
           static_cast<unsigned long long>(decodedBytes),
           matchesTarget ? "yes" : "no");
    return matchesTarget;
#endif
}

} // namespace td
