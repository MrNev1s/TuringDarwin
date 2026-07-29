#include "TuringProbe.hpp"

#include <pexpert/pexpert.h>

#include "BARInspector.hpp"
#include "CapabilityParser.hpp"
#include "Logging.hpp"
#include "HostMemorySelfTest.hpp"
#include "MMIOReadOnly.hpp"
#include "PCIConfig.hpp"

#define super IOService
OSDefineMetaClassAndStructors(TuringProbe, IOService)

namespace {

bool bootArgumentPresent(const char *name) {
    int value = 0;
    return name != nullptr && PE_parse_boot_argn(name, &value, sizeof(value));
}

}

bool TuringProbe::start(IOService *provider) {
    if (bootArgumentPresent("-tdoff")) {
        TD_LOG("disabled by -tdoff");
        return false;
    }

    if (bootArgumentPresent("-tdunsafe")) {
        TD_LOG("v0.6.0 rejects -tdunsafe");
        return false;
    }

    if (!bootArgumentPresent("-tdprobe")) {
        TD_LOG("not attaching because -tdprobe is absent");
        return false;
    }

    const bool mmioRequested = bootArgumentPresent("-tdmmio-read");
    const bool topRequested = bootArgumentPresent("-tdtop-read");
    const bool fbMmuRequested = bootArgumentPresent("-tdfb-read");
    const bool hostMemoryRequested = bootArgumentPresent("-tdhostmem-test");
    if (topRequested && !mmioRequested) {
        TD_LOG("refusing -tdtop-read without -tdmmio-read");
        return false;
    }
    if (fbMmuRequested && !mmioRequested) {
        TD_LOG("refusing -tdfb-read without -tdmmio-read");
        return false;
    }
    if (topRequested && fbMmuRequested) {
        TD_LOG("refusing simultaneous -tdtop-read and -tdfb-read in v0.6.0");
        return false;
    }
    if (hostMemoryRequested && mmioRequested) {
        TD_LOG("refusing -tdhostmem-test with any BAR0/MMIO mode");
        return false;
    }

    IOPCIDevice *candidate = OSDynamicCast(IOPCIDevice, provider);
    if (candidate == nullptr) {
        TD_LOG("provider is not IOPCIDevice");
        return false;
    }

    const td::PciIdentity identity = td::readIdentity(candidate);
    const UInt16 commandBeforeProbe = candidate->configRead16(td::kPciCommandOffset);
    if (!td::isExactTarget(identity)) {
        TD_LOG("refusing PCI function %04x:%04x subsystem %04x:%04x",
               identity.vendor, identity.device,
               identity.subsystemVendor, identity.subsystemDevice);
        return false;
    }

    if (!super::start(provider)) {
        TD_LOG("super::start failed");
        return false;
    }

    pciDevice_ = candidate;
    pciDevice_->retain();

    td::publishPciSnapshot(pciDevice_, this);
    td::publishRegistryPaths(pciDevice_, this);
    td::publishConventionalConfigSnapshot(pciDevice_, this);
    td::publishCapabilities(pciDevice_, this);
    td::publishBarAndMemoryDescriptors(pciDevice_, this);

    bool hostMemoryCompleted = false;
    if (hostMemoryRequested) {
        hostMemoryCompleted = td::performHostMemorySelfTest(this);
        if (!hostMemoryCompleted) {
            TD_LOG("refusing attachment because host-memory self-test failed");
            pciDevice_->release();
            pciDevice_ = nullptr;
            super::stop(provider);
            return false;
        }
    }

    bool mmioCompleted = false;
    if (mmioRequested) {
        mmioCompleted = td::performReadOnlyBar0Probe(
            pciDevice_, this, topRequested, fbMmuRequested);
        if (!mmioCompleted) {
            TD_LOG("refusing attachment because BAR0 read-only gate did not complete");
            pciDevice_->release();
            pciDevice_ = nullptr;
            super::stop(provider);
            return false;
        }
    }

    const UInt16 commandAfterProbe = pciDevice_->configRead16(td::kPciCommandOffset);
    td::publishNumber(this, "TPCommandBeforeProbe", commandBeforeProbe, 16);
    td::publishNumber(this, "TPCommandAfterProbe", commandAfterProbe, 16);
    td::publishBoolean(this, "TPCommandUnchanged",
                       commandBeforeProbe == commandAfterProbe);
    td::publishBoolean(this, "TPBusMasterEnabledBeforeProbe",
                       (commandBeforeProbe & 0x0004U) != 0);
    td::publishBoolean(this, "TPBusMasterEnabledAfterProbe",
                       (commandAfterProbe & 0x0004U) != 0);
    td::publishBoolean(this, "TPIOSpaceEnabled",
                       (commandAfterProbe & 0x0001U) != 0);
    td::publishBoolean(this, "TPMemorySpaceEnabled",
                       (commandAfterProbe & 0x0002U) != 0);

    if (commandBeforeProbe != commandAfterProbe ||
        (commandAfterProbe & 0x0004U) != 0) {
        TD_LOG("refusing attachment because PCI command state is not safe");
        pciDevice_->release();
        pciDevice_ = nullptr;
        super::stop(provider);
        return false;
    }

    setProperty("TuringProbeSafeReadOnly",
                hostMemoryRequested ? kOSBooleanFalse : kOSBooleanTrue);
    setProperty("TuringProbeDeviceAccessReadOnly", kOSBooleanTrue);
    setProperty("TuringProbeProbeCompleted", kOSBooleanTrue);
    setProperty("TuringProbeProbeSchemaVersion", "6");
    setProperty("TuringProbeVersion", "0.6.0");
    setProperty(
        "TuringProbeBootMode",
        hostMemoryRequested ? "-tdprobe -tdhostmem-test" :
        (topRequested ? "-tdprobe -tdmmio-read -tdtop-read" :
        (fbMmuRequested ? "-tdprobe -tdmmio-read -tdfb-read" :
        (mmioRequested ? "-tdprobe -tdmmio-read" : "-tdprobe"))));
    setProperty(
        "TuringProbeMilestone",
        hostMemoryRequested ? "HOST-MEMORY-CPU-WRITE-READBACK-V0.6.0" :
        (topRequested ? "BAR0-TOP-INVENTORY-READ-ONLY-V0.6.0" :
        (fbMmuRequested ? "BAR0-FB-MMU-PROFILE-READ-ONLY-V0.6.0" :
        (mmioRequested ? "BAR0-IDENTITY-READ-ONLY-V0.6.0" :
                         "PCI-CONFIG-READ-ONLY-COMPAT-V0.6.0"))));
    setProperty("TuringProbeTarget", "NVIDIA TU116 10DE:2182 / ASUS 1043:8854");
    setProperty("TuringProbePCIConfigWrites", kOSBooleanFalse);
    setProperty("TuringProbeMMIOAccess", mmioCompleted ? kOSBooleanTrue : kOSBooleanFalse);
    setProperty("TuringProbeMMIOWrites", kOSBooleanFalse);
    setProperty("TuringProbeTopInventoryAccess",
                topRequested && mmioCompleted ?
                    kOSBooleanTrue : kOSBooleanFalse);
    setProperty("TuringProbeFbMmuInventoryAccess",
                fbMmuRequested && mmioCompleted ?
                    kOSBooleanTrue : kOSBooleanFalse);
    setProperty("TuringProbeHostMemoryAccess",
                hostMemoryCompleted ? kOSBooleanTrue : kOSBooleanFalse);
    setProperty("TuringProbeHostMemoryCPUWrites",
                hostMemoryCompleted ? kOSBooleanTrue : kOSBooleanFalse);
    setProperty("TuringProbeDeviceMemoryAccess", kOSBooleanFalse);
    setProperty("TuringProbeDeviceMemoryWrites", kOSBooleanFalse);
    setProperty("TuringProbeDMAAccess", kOSBooleanFalse);
    setProperty("TuringProbeFirmwareAccess", kOSBooleanFalse);
    setProperty("TuringProbeInterruptAccess", kOSBooleanFalse);
    setProperty("TuringProbePowerStateChanges", kOSBooleanFalse);
    setProperty("TuringProbeUserClient", kOSBooleanFalse);

    registerService();
    TD_LOG("attached staged-safe to %02x:%02x.%x %04x:%04x subsystem %04x:%04x mode=%s",
           pciDevice_->getBusNumber(), pciDevice_->getDeviceNumber(),
           pciDevice_->getFunctionNumber(), identity.vendor, identity.device,
           identity.subsystemVendor, identity.subsystemDevice,
           hostMemoryRequested ? "host-memory CPU write/readback" :
           (topRequested ? "BAR0 identity+TOP inventory" :
           (fbMmuRequested ? "BAR0 identity+FB/MMU profile" :
           (mmioRequested ? "BAR0 identity whitelist" : "PCI only"))));
    return true;
}

void TuringProbe::stop(IOService *provider) {
    TD_LOG("stop; no PCI or MMIO writes, DMA, firmware, interrupts, or power changes were performed");
    if (pciDevice_ != nullptr) {
        pciDevice_->release();
        pciDevice_ = nullptr;
    }
    super::stop(provider);
}
