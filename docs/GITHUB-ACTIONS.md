# GitHub Actions build

GitHub Actions can compile the read-only `TuringProbe.kext` on a hosted macOS
runner. CI compilation does not prove that the kext is safe to load and does not
replace the separate test-EFI procedure.

## Runner and toolchain

The workflow uses:

- `macos-15` GitHub-hosted runner;
- `/Applications/Xcode_16.2.app`;
- macOS SDK 15.2;
- cross-compilation to `x86_64`;
- Acidanthera MacKernelSDK;
- Debug by default.

The workflow resolves the requested MacKernelSDK ref, records the resulting
40-character commit in `MacKernelSDK.lock`, and includes it in the build
manifest. For a strictly reproducible rerun, launch the workflow again and put
that recorded commit SHA into the `mac_kernel_sdk_ref` field instead of
`master`.

## First build

1. Create an empty GitHub repository.
2. Upload the contents of `TuringDarwin-v0.1` to the repository root. The
   `.github` folder must remain present.
3. Open the repository's **Actions** tab.
4. Select **Build TuringProbe kext**.
5. Select **Run workflow**.
6. Keep `Debug` and `master` for the first compile-only attempt.
7. Open the completed run and download the artifact named approximately
   `TuringProbe-v0.1-Debug-x86_64`.

The artifact contains:

- `TuringProbe-v0.1-Debug-x86_64.kext.zip`;
- build log;
- build manifest;
- SHA-256 file.

## What CI verifies

- Xcode 16.2 and SDK 15.2 are actually selected;
- the source safety audit passes;
- source and generated Info.plist files parse;
- Xcode successfully links a kext bundle;
- the Mach-O payload exists and is `x86_64` only;
- output hashes and build metadata are recorded.

CI does not verify:

- loading on the target Hackintosh;
- IOService matching against the physical TU116;
- IORegistry properties;
- behavior during boot;
- absence of target-specific firmware or hardware faults.

## Failure handling

When the build fails, the workflow uploads a separate failed-build artifact
containing every build log that exists. Do not put a partially built bundle in
OpenCore.

## Security note

A CI-produced kext is unsigned. This project is intended to be injected from a
separate OpenCore test EFI under the documented development configuration. Do
not weaken the stable EFI merely to load an unreviewed build.
