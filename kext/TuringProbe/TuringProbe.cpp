#include "TuringProbe.hpp"

#include <pexpert/pexpert.h>

#include "BARInspector.hpp"
#include "CapabilityParser.hpp"
#include "Logging.hpp"
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

    if (bootArgumentPresent("-tdmmio-read") || bootArgumentPresent("-tdunsafe")) {
        TD_LOG("v0.1.1 rejects modes beyond the read-only PCI probe");
        return false;
    }

    if (!bootArgumentPresent("-tdprobe")) {
        TD_LOG("not attaching because -tdprobe is absent");
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

    setProperty("TuringProbeSafeReadOnly", kOSBooleanTrue);
    setProperty("TuringProbeProbeCompleted", kOSBooleanTrue);
    setProperty("TuringProbeProbeSchemaVersion", "2");
    setProperty("TuringProbeVersion", "0.1.1");
    setProperty("TuringProbeBootMode", "-tdprobe");
    setProperty("TuringProbeMilestone", "PCI-CONFIG-READ-ONLY-V0.1.1");
    setProperty("TuringProbeTarget", "NVIDIA TU116 10DE:2182 / ASUS 1043:8854");
    setProperty("TuringProbePCIConfigWrites", kOSBooleanFalse);
    setProperty("TuringProbeMMIOAccess", kOSBooleanFalse);
    setProperty("TuringProbeDMAAccess", kOSBooleanFalse);
    setProperty("TuringProbeFirmwareAccess", kOSBooleanFalse);
    setProperty("TuringProbeInterruptAccess", kOSBooleanFalse);
    setProperty("TuringProbePowerStateChanges", kOSBooleanFalse);
    setProperty("TuringProbeUserClient", kOSBooleanFalse);

    registerService();
    TD_LOG("attached read-only to %02x:%02x.%x %04x:%04x subsystem %04x:%04x",
           pciDevice_->getBusNumber(), pciDevice_->getDeviceNumber(),
           pciDevice_->getFunctionNumber(), identity.vendor, identity.device,
           identity.subsystemVendor, identity.subsystemDevice);
    return true;
}

void TuringProbe::stop(IOService *provider) {
    TD_LOG("stop; no hardware state was changed by v0.1.1");
    if (pciDevice_ != nullptr) {
        pciDevice_->release();
        pciDevice_ = nullptr;
    }
    super::stop(provider);
}
