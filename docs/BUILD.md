# Build instructions

## Exact baseline

For the first reproducible build use:

- macOS Sequoia 15.x on the target machine;
- Xcode 16.2;
- macOS 15.2 SDK bundled with Xcode 16.2;
- architecture `x86_64`;
- Debug configuration for the first live test;
- MacKernelSDK pinned to one full 40-character commit in `MacKernelSDK.lock`.

The source package intentionally does not invent a MacKernelSDK commit. A branch
name such as `master` is not reproducible, so `bootstrap-sdk.sh` refuses it.
Choose and record the exact commit before accepting the build for testing.

## Commands

```bash
cd TuringDarwin-v0.1
cp MacKernelSDK.lock.example MacKernelSDK.lock
# Replace the zero hash with a reviewed full MacKernelSDK commit.
./tools/bootstrap-sdk.sh
./tools/build.sh Debug
```

Expected product:

```text
build/Debug/TuringProbe.kext
```

The build script records macOS, Xcode, SDK, MacKernelSDK commit and binary
SHA-256 in `build/build-Debug.manifest.txt`.

## Mandatory checks

```bash
./tools/safety-audit.py
plutil -lint kext/TuringProbe/Info.plist
xcodebuild -project TuringProbe.xcodeproj -target TuringProbe \
  -configuration Debug ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES build
```

A generated archive without a successful Xcode log is source only, not a tested
kext.

## Cloud build through GitHub Actions

A ready workflow is included at `.github/workflows/build-kext.yml`. It selects
Xcode 16.2 explicitly, verifies macOS SDK 15.2, resolves MacKernelSDK, invokes
the same `tools/build.sh` used locally, verifies the output architecture, and
uploads the zipped kext with logs and hashes. Full steps are in
`docs/GITHUB-ACTIONS.md`.
