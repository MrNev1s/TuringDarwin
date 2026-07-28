#pragma once

#include <IOKit/IOService.h>

namespace td {

// Reads the fixed 64-word PTOP device-info table used by Nouveau's
// gk104_top_parse path, decodes completed records, and publishes both raw and
// structured results. The caller owns the read-only BAR0 mapping.
bool performReadOnlyTopInventory(const void *bar0, IOService *owner);

} // namespace td
