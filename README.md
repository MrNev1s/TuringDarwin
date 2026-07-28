# TuringDarwin / TuringProbe 0.1.1

TuringProbe is the deliberately read-only diagnostic component for the exact
ASUS TU116 board `10DE:2182 / 1043:8854`.

## Verified baseline

Version 0.1.0 was built with Xcode 16.2 / macOS SDK 15.2, injected by OpenCore,
and successfully attached to the target GPU on macOS 15.7.7. The system reached
the desktop, the GOP/IONDRV framebuffer remained active, and the PCI Command
Register showed bus mastering disabled.

Read [`PROJECT_STATE.md`](PROJECT_STATE.md) first. It is the canonical project
hand-off and contains the verified BARs, PCI capability chain, hashes, safety
contract, and current acceptance gates.

## 0.1.1 scope

0.1.1 remains PCI-configuration read-only. It adds unsigned raw-value
publication, named capabilities, bounded full ReBAR decoding, and before/after
Command Register evidence. It still does not map BAR memory, access MMIO,
enable bus mastering, submit DMA, install interrupts, load firmware, change
power state, or create an IOUserClient.

Fail-closed boot controls:

- `-tdprobe` is required;
- `-tdoff` disables attachment;
- `-tdmmio-read` and `-tdunsafe` are rejected.

## Build

The GitHub Actions workflow uses Xcode 16.2, macOS SDK 15.2, x86_64, and pins
MacKernelSDK to the commit proven by the successful 0.1.0 build:

`05094e5e88cec7caedbfb35e8449ed0db94bf95b`

Run **Build TuringProbe kext** with configuration `Debug`. The 0.1.1 source is
not considered built or hardware-verified until that workflow and the
subsequent controlled boot both pass.
