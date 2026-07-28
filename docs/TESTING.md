# TuringProbe 0.1.1 live test

0.1.0 already passed its real-hardware acceptance test. This test verifies only
the 0.1.1 diagnostic improvements; it does not authorise MMIO.

## Build gate

Run the GitHub Actions workflow using:

- Configuration: `Debug`;
- MacKernelSDK ref: leave the pinned default
  `05094e5e88cec7caedbfb35e8449ed0db94bf95b`.

Require a green workflow and retain the artifact, manifest, build log, and
SHA-256 file.

## Test EFI

Replace only the old `TuringProbe.kext` in the already-tested separate EFI.
Keep `-tdprobe`. Do not add `-tdmmio-read` or `-tdunsafe`.

## Capture

```bash
mkdir -p ~/Desktop/TuringProbe-v0.1.1-logs
kmutil showloaded | grep -i TuringProbe \
  > ~/Desktop/TuringProbe-v0.1.1-logs/kmutil.txt
ioreg -r -c TuringProbe -l -w0 \
  > ~/Desktop/TuringProbe-v0.1.1-logs/ioreg-turingprobe.txt
ioreg -l -w0 -p IOService \
  > ~/Desktop/TuringProbe-v0.1.1-logs/ioreg-full.txt
log show --last boot --style compact \
  --predicate 'eventMessage CONTAINS[c] "TuringProbe"' \
  > ~/Desktop/TuringProbe-v0.1.1-logs/kernel-log.txt
system_profiler SPDisplaysDataType \
  > ~/Desktop/TuringProbe-v0.1.1-logs/displays.txt
sw_vers > ~/Desktop/TuringProbe-v0.1.1-logs/sw-vers.txt
cd ~/Desktop && zip -r TuringProbe-v0.1.1-logs.zip TuringProbe-v0.1.1-logs
```

## Acceptance criteria

- version `0.1.1` is loaded and active;
- desktop/display behaviour is unchanged;
- `TuringProbeProbeCompleted = Yes`;
- `TPCommandBeforeProbe = 3`;
- `TPCommandAfterProbe = 3`;
- `TPCommandUnchanged = Yes`;
- both bus-master before/after properties are `No`;
- raw BAR/header values no longer appear sign-extended;
- conventional and extended entries contain correct names;
- `TPResizableBARDecodeValid = Yes`;
- `TPResizableBARDecodedEntryCount = 3`;
- no panic, fan/power anomaly, or display change occurs.
