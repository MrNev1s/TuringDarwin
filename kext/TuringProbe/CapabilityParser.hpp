#pragma once

#include <IOKit/IOService.h>
#include <IOKit/pci/IOPCIDevice.h>

namespace td {
void publishCapabilities(IOPCIDevice *device, IOService *owner);
}
