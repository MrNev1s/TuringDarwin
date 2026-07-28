#pragma once

#include <IOKit/IOService.h>

namespace td {

// Reads one source-backed, static FB capacity register and publishes the
// source-defined TU116 MMU capability profile. The caller owns the read-only
// BAR0 mapping. No MMU control/status registers are touched.
bool performReadOnlyFbMmuInventory(const void *bar0, IOService *owner);

} // namespace td
