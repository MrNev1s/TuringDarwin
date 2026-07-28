# Complete rollback

1. Power off the machine if the boot hangs; do not repeatedly warm-reset it.
2. Select the untouched stable USB EFI from the BIOS boot menu.
3. On the test EFI, either disable the `Kernel -> Add` entry or remove
   `TuringProbe.kext`.
4. Remove `-tdprobe`; optionally add `-tdoff` while diagnosing configuration
   selection.
5. Run OpenCore `Reset NVRAM` once if stale boot arguments are suspected.
6. Reboot with the stable EFI and collect a post-rollback log.

Because v0.1 has no authorised device writes, there is no software GPU-reset or
hardware-state restoration routine. The rollback boundary is selecting the
known-good EFI and performing a cold boot.
