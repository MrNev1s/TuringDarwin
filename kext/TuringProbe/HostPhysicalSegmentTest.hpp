#pragma once

#include <IOKit/IOService.h>

namespace td {

// Allocates one wired, kernel-mapped IOBufferMemoryDescriptor page, performs
// bounded CPU write/readback, retrieves one raw host physical segment, then
// zeroizes and releases the descriptor. The function has no GPU or DMA input.
bool performHostPhysicalSegmentTest(IOService *owner);

} // namespace td
