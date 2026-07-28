#pragma once

#include <IOKit/IOService.h>
#include <IOKit/pci/IOPCIDevice.h>

namespace td {

// Maps BAR0 read-only, performs the fixed identity whitelist and optionally
// one separately gated inventory (bounded PTOP or one-register FB/MMU profile),
// publishes results, and destroys the mapping before returning. No mapping is
// retained.
bool performReadOnlyBar0Probe(IOPCIDevice *device, IOService *owner,
                              bool topInventoryRequested,
                              bool fbMmuInventoryRequested);

} // namespace td
