#pragma once

#include <IOKit/IOLib.h>

#define TD_LOG(format, ...) IOLog("TuringProbe: " format "\n", ##__VA_ARGS__)
