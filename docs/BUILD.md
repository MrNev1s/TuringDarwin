# Build instructions for TuringProbe 0.2.1

## Pinned toolchain

- Xcode 16.2;
- macOS 15.2 SDK;
- `x86_64`;
- Debug for the first test;
- MacKernelSDK commit
  `05094e5e88cec7caedbfb35e8449ed0db94bf95b`.

## Local commands

```bash
cd TuringDarwin-v0.2.1
printf '%s\n' 05094e5e88cec7caedbfb35e8449ed0db94bf95b > MacKernelSDK.lock
./tools/bootstrap-sdk.sh
./tools/build.sh Debug
```

Expected product:

```text
build/Debug/TuringProbe.kext
```

Mandatory pre-build checks:

```bash
python3 tools/safety-audit.py
python3 tools/test-decoder-contract.py
python3 tools/test-mmio-contract.py
plutil -lint kext/TuringProbe/Info.plist
plutil -lint TuringProbe.xcodeproj/project.pbxproj
```

A source ZIP is not a built kext. A green Xcode log still does not prove safe
hardware behavior; the artifact must be audited before any EFI change.
