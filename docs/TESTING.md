# First live test

## Baseline capture

Boot the stable EFI without TuringProbe and run:

```bash
./tools/collect-macos.sh ~/Desktop/TuringProbe-baseline
```

## Probe capture

Boot the separate test EFI with `-tdprobe`, then verify:

```bash
kmutil showloaded | grep -i TuringProbe
ioreg -r -c TuringProbe -l -w0
log show --last boot --style syslog \
  --predicate 'eventMessage CONTAINS[c] "TuringProbe"'
./tools/collect-macos.sh ~/Desktop/TuringProbe-v0.1
```

## Acceptance criteria

- macOS reaches the desktop with unchanged display behaviour;
- one `TuringProbe` service attaches to PCI `01:00.0` only;
- IDs are `10DE:2182` and `1043:8854`;
- bus/device/function are `01:00.0`;
- a 256-byte config snapshot is present;
- BAR descriptors and capability arrays are finite and structurally valid;
- no kernel panic, fan/power anomaly or display change occurs;
- a second boot without the test EFI behaves like baseline.

## Required comparison

Record these from both boots:

- `TPCommand` and `TPStatus`;
- all raw BAR values;
- PCIe current/max speed and width;
- MSI/MSI-X enabled state;
- memory descriptor physical bases and lengths;
- display report and boot log.

No discrepancy should be interpreted as harmless until reviewed.
