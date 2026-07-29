# GitHub Actions build — 0.5.1

The workflow builds on `macos-15` with Xcode 16.2, macOS SDK 15.2, `x86_64`, and
pinned MacKernelSDK commit
`05094e5e88cec7caedbfb35e8449ed0db94bf95b`.

## Improvements in 0.5.1

- changes under `research/**` and `docs/**` now trigger CI;
- the workflow invokes `tools/run-offline-validation.sh`;
- MMU model, page-table image, golden-vector, address-space and rollback suites
  are mandatory before Xcode runs;
- `tools/build.sh` invokes the same complete suite, avoiding local/CI drift;
- the unsupported `kextutil -n` invocation was removed;
- the manifest explicitly records `mmu_hardware_whitelist=EMPTY`;
- validation output is included in successful and failed artifacts.

## Build procedure

1. Upload the 0.5.1 update into the repository root, including `.github`.
2. Commit with `TuringProbe 0.5.1 complete offline MMU validation`.
3. Open **Actions → Build TuringProbe kext → Run workflow**.
4. Use `Debug` and the pinned MacKernelSDK SHA.
5. Download `TuringProbe-v0.5.1-Debug-x86_64` after a green run.

The artifact contains the kext ZIP, build log, provenance manifest, complete
source-validation log, architecture report, undefined-symbol report, optional
codesign report and SHA-256 list.

A green build proves compilation and offline contracts. It does not authorise a
hardware boot or any MMU write.
