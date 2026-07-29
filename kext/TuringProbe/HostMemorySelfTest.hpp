#pragma once

#include <IOKit/IOService.h>

namespace td {

// Performs one bounded CPU-only test using ordinary wired kernel memory.
// This function accepts only the registry owner and cannot touch GPU memory.
bool performHostMemorySelfTest(IOService *owner);

} // namespace td
