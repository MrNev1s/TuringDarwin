# TuringDarwin / TuringProbe 0.1.0

`TuringProbe.kext` is the first, deliberately read-only diagnostic component
for one specific board:

- NVIDIA vendor/device: `10DE:2182`
- ASUS subsystem: `1043:8854`
- PCI personality uses both `IOPCIPrimaryMatch` and `IOPCISecondaryMatch`,
  followed by an exact in-code identity gate
- Board family: ASUS TUF Gaming GeForce GTX 1660 Ti EVO TOP / TU116

## Scope

Version 0.1 reads PCI configuration space and publishes a structured snapshot
in IORegistry. It does not map BAR memory, access GPU MMIO, enable bus mastering,
submit commands, create DMA mappings, install interrupt handlers, load firmware,
or alter PCI power state.

The service is fail-closed:

- `-tdprobe` is required to attach.
- `-tdoff` prevents attachment.
- `-tdmmio-read` and `-tdunsafe` are rejected by this version.

## Verification status

- Supplied PC-DATA, stable EFI and VBIOS were inspected offline.
- The source passed the included static safety audit and plist parsing checks.
- This package was generated on Linux, so it has **not** been compiled by Xcode,
  loaded on the target Mac, or validated against a live IORegistry dump.
- A build is not considered valid until `tools/build.sh` succeeds on the target
  macOS installation and the resulting build manifest is retained.

Read `docs/SAFETY.md`, `docs/BUILD.md`, `docs/EFI-INSTALL.md`,
`docs/PCI-CAPABILITIES.md`, `docs/RESULT-MATRIX.md`, and `docs/TESTING.md`
before using it.

## GitHub Actions build

The repository includes `.github/workflows/build-kext.yml`. It builds the
x86_64 diagnostic kext on a GitHub-hosted macOS runner, runs the read-only
safety audit, records the resolved MacKernelSDK commit, and uploads a ZIP
artifact. See [`docs/GITHUB-ACTIONS.md`](docs/GITHUB-ACTIONS.md).
