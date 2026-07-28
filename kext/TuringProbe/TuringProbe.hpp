#pragma once

#include <IOKit/IOService.h>
#include <IOKit/pci/IOPCIDevice.h>

class TuringProbe final : public IOService {
    OSDeclareDefaultStructors(TuringProbe)

public:
    bool start(IOService *provider) override;
    void stop(IOService *provider) override;

private:
    IOPCIDevice *pciDevice_ {nullptr};
};
