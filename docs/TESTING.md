# TuringProbe 0.2.0 controlled test procedure

Status: source implemented; Xcode build, binary audit, and real-hardware test
remain pending.

## Gate A — GitHub build

Use the included workflow with:

- Configuration: `Debug`;
- MacKernelSDK ref:
  `05094e5e88cec7caedbfb35e8449ed0db94bf95b`.

Require a green workflow and retain the kext ZIP, manifest, build log,
undefined-symbol report, and SHA-256 file.

Do not proceed directly from a green workflow to boot. Upload the complete
artifact for source-to-binary and forbidden-call-site audit first.

## Gate B — PCI-only compatibility boot

Replace only `TuringProbe.kext` in the already-tested separate EFI and retain:

```text
-tdprobe
```

This proves the 0.2.0 binary can reproduce the 0.1.1 PCI-only behavior without
mapping BAR0.

Required observations:

- kext version `0.2.0` loaded and active;
- `TuringProbeBootMode = -tdprobe`;
- `TuringProbeMMIOAccess = No`;
- PCI Command unchanged and Bus Master Enable clear;
- display behavior unchanged.

## Gate C — first BAR0 read-only boot

Only after Gate B passes, use the separate test EFI with:

```text
-tdprobe -tdmmio-read
```

Use one monitor, retain physical access to power/reset, and keep the untouched
fallback EFI available. Do not repeat a failed boot without first reviewing the
panic/photo/logs.

## Log capture

```bash
mkdir -p ~/Desktop/TuringProbe-v0.2.0-logs
kmutil showloaded | grep -i TuringProbe \
  > ~/Desktop/TuringProbe-v0.2.0-logs/kmutil.txt
ioreg -r -c TuringProbe -l -w0 \
  > ~/Desktop/TuringProbe-v0.2.0-logs/ioreg-turingprobe.txt
ioreg -l -w0 -p IOService \
  > ~/Desktop/TuringProbe-v0.2.0-logs/ioreg-full.txt
log show --last boot --style compact \
  --predicate 'eventMessage CONTAINS[c] "TuringProbe"' \
  > ~/Desktop/TuringProbe-v0.2.0-logs/kernel-log.txt
system_profiler SPDisplaysDataType \
  > ~/Desktop/TuringProbe-v0.2.0-logs/displays.txt
sw_vers > ~/Desktop/TuringProbe-v0.2.0-logs/sw-vers.txt
nvram boot-args > ~/Desktop/TuringProbe-v0.2.0-logs/boot-args.txt 2>&1 || true
cd ~/Desktop && zip -r TuringProbe-v0.2.0-logs.zip TuringProbe-v0.2.0-logs
```

The bundled `tools/collect-macos.sh` performs the same collection.

## BAR0 acceptance criteria

All of the following must be present:

- `TuringProbeVersion = 0.2.0`;
- `TuringProbeBootMode = -tdprobe -tdmmio-read`;
- `TuringProbeMMIOAccess = Yes`;
- `TuringProbeMMIOWrites = No`;
- `TPBAR0MappingCreated = Yes`;
- `TPBAR0MappingReadOnlyRequested = Yes`;
- `TPBAR0MappingRetainedAfterProbe = No`;
- `TPBAR0MappingReleased = Yes`;
- `TPBAR0MappingLength = 16777216`;
- `TPMMIOReadCount = 3`;
- `TPMMIOReadCompleted = Yes`;
- `TPMMIOChipset = 0x168` and `TPMMIOChipsetIsTU116 = Yes`;
- `TPMMIOCrystalDecodeValid = Yes`;
- `TPMMIOVgpuBits = 0`;
- PCI Command values before map, after map, after reads, and after the full probe
  are identical;
- all Bus Master properties remain `No`;
- no panic, hang, fan/power anomaly, or display corruption occurs.

A successful read-only result does not authorise any MMIO write or later GPU
initialisation step.
