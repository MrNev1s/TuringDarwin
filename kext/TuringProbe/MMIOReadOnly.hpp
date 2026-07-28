#pragma once

#include <IOKit/IOService.h>
#include <IOKit/pci/IOPCIDevice.h>

namespace td {

// Maps BAR0 read-only, performs the fixed three-register whitelist, publishes
// results, and destroys the mapping before returning. No mapping is retained.
bool performReadOnlyBar0Probe(IOPCIDevice *device, IOService *owner);

} // namespace td
