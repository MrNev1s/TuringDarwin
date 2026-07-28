#pragma once

#include <libkern/OSTypes.h>

namespace td {
struct PciIdentity {
    UInt16 vendor;
    UInt16 device;
    UInt16 subsystemVendor;
    UInt16 subsystemDevice;
};
}
