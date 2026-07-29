# Changelog — TuringProbe 0.5.1

## Added

- fixed MMU golden vectors;
- deterministic multi-page/mixed-page address-space builder;
- boundary tests for leaf, PD0 and root-index transitions;
- explicit physical-alias policy and virtual-overlap rejection;
- 4 KiB to 2 MiB promotion and demotion model;
- offline transaction/rollback state machine;
- complete validation runner used by local builds and GitHub Actions;
- MMU transaction and rollback documentation.

## Fixed

- GitHub Actions now runs the MMU model and page-table image suites;
- research and documentation changes now trigger CI;
- local build and CI validation no longer use different test subsets;
- unsupported `kextutil -n` validation was removed;
- build manifest now states that the MMU hardware whitelist is empty.

## Hardware boundary

No new MMIO access or write path was added. No real-hardware boot is required or
authorised for this release.
