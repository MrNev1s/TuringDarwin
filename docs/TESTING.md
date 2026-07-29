# TuringProbe 0.5.1 testing

## Scope

0.5.1 is an offline research/CI release. There is no new hardware test.

## Complete local suite

```bash
bash tools/run-offline-validation.sh
```

The suite runs:

1. source safety audit;
2. PCI/ReBAR decoder contract;
3. MMIO ownership and whitelist contract;
4. bounded PTOP contract;
5. one-register FB contract;
6. randomized MMU model tests;
7. byte-exact page-table image tests;
8. fixed golden vectors;
9. multi-page/mixed-page address-space tests;
10. transaction/rollback state-machine tests;
11. Python, plist and shell syntax checks.

Expected final line:

```text
OFFLINE VALIDATION SUITE PASSED
```

## GitHub build gate

A green workflow must include `build-source-validation.txt`. Confirm that it
contains PASS output for all ten contracts above before considering the build
artifact valid.

The build artifact still requires a Mach-O audit for version, exact matching,
existing read helpers, release path and absence of writes. It does not require a
real-hardware boot because 0.5.1 contains no new hardware path.

## Hardware policy

Keep `-tdprobe` only. Do not enable the historical one-shot MMIO/PTOP/FB modes.
No MMU hardware test is defined by this release.
