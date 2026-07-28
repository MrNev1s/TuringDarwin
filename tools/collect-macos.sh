#!/bin/bash
set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${1:-$HOME/Desktop/TuringProbe-$STAMP}"
mkdir -p "$OUT"

sw_vers > "$OUT/sw_vers.txt"
uname -a > "$OUT/uname.txt"
nvram boot-args > "$OUT/nvram-boot-args.txt" 2>&1 || true
kmutil showloaded > "$OUT/kmutil-showloaded.txt" 2>&1 || true
ioreg -p IOService -l -w0 > "$OUT/ioreg-IOService.txt"
ioreg -p IODeviceTree -l -w0 > "$OUT/ioreg-IODeviceTree.txt"
ioreg -r -c TuringProbe -l -w0 > "$OUT/ioreg-TuringProbe.txt" 2>&1 || true
system_profiler SPDisplaysDataType > "$OUT/SPDisplaysDataType.txt"
system_profiler SPPCIDataType > "$OUT/SPPCIDataType.txt" 2>&1 || true
log show --last boot --style syslog \
  --predicate 'eventMessage CONTAINS[c] "TuringProbe"' \
  > "$OUT/TuringProbe-log.txt" 2>&1 || true

/usr/bin/zip -qry "$OUT.zip" "$OUT"
echo "$OUT.zip"
