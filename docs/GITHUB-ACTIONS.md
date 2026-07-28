# GitHub Actions build

The included workflow compiles `TuringProbe.kext` on `macos-15` with Xcode 16.2,
macOS SDK 15.2, `x86_64`, and pinned MacKernelSDK commit
`05094e5e88cec7caedbfb35e8449ed0db94bf95b`.

## Build steps

1. Upload the 0.2.0 update files into the repository root, including `.github`.
2. Commit the changes.
3. Open **Actions -> Build TuringProbe kext -> Run workflow**.
4. Keep `Debug` and the pre-filled full MacKernelSDK SHA.
5. Download `TuringProbe-v0.2.0-Debug-x86_64` after a green run.

The artifact contains the kext ZIP, build log, manifest, and hashes.

## CI gates

- source safety audit;
- PCI/ReBAR decoder contract test;
- MMIO whitelist/read-only mapping contract test;
- plist and Xcode project validation;
- Xcode compilation/linking;
- `x86_64` architecture check;
- undefined-symbol report;
- output hashes and provenance manifest.

CI does not prove target attachment or MMIO behavior. Upload the entire artifact
for static binary review before modifying the test EFI.
