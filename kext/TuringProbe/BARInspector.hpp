#pragma once

#include <IOKit/IOService.h>
#include <IOKit/pci/IOPCIDevice.h>

namespace td {
void publishBarAndMemoryDescriptors(IOPCIDevice *device, IOService *owner);
}
