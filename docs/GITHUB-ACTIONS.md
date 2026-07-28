# GitHub Actions build

GitHub Actions compiles the read-only `TuringProbe.kext` on a hosted macOS
runner. CI compilation does not replace the separate test-EFI procedure.

## Runner and pinned toolchain

The workflow uses:

- `macos-15` GitHub-hosted runner;
- `/Applications/Xcode_16.2.app`;
- macOS SDK 15.2;
- `x86_64` only;
- MacKernelSDK commit
  `05094e5e88cec7caedbfb35e8449ed0db94bf95b` by default;
- Debug configuration by default.

The SDK commit is the exact revision used by the successful 0.1.0 build. The
resolved commit is written to `MacKernelSDK.lock` and the build manifest.

## Build 0.1.1

1. Replace the repository files with the 0.1.1 source tree while preserving the
   `.github` directory.
2. Open **Actions**.
3. Select **Build TuringProbe kext**.
4. Select **Run workflow**.
5. Keep `Debug` and the pre-filled full MacKernelSDK SHA.
6. Download `TuringProbe-v0.1.1-Debug-x86_64` after a green run.

The artifact contains:

- `TuringProbe-v0.1.1-Debug-x86_64.kext.zip`;
- build log;
- build manifest;
- SHA-256 file.

## CI gates

- source safety audit;
- TU116 ReBAR decoder contract test;
- plist and Xcode project validation;
- Xcode compilation and linking;
- `x86_64` architecture check;
- undefined-symbol report;
- output hashes and manifest.

CI does not verify real attachment, IORegistry output, boot stability, or
hardware behavior. Those require the controlled test-EFI boot in `TESTING.md`.
