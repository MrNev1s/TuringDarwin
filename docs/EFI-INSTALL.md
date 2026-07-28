# Add TuringProbe 0.2.0 to a separate test EFI

Do not alter the known-good stable EFI. Do not install this kext into the macOS
system volume or `/Library/Extensions`.

## OpenCore entry

Copy the audited build product to:

```text
EFI/OC/Kexts/TuringProbe.kext
```

Add this as the last item in `Kernel -> Add`:

```xml
<dict>
  <key>Arch</key><string>x86_64</string>
  <key>BundlePath</key><string>TuringProbe.kext</string>
  <key>Comment</key><string>TuringProbe 0.2.0 BAR0 read-only diagnostic</string>
  <key>Enabled</key><true/>
  <key>ExecutablePath</key><string>Contents/MacOS/TuringProbe</string>
  <key>MaxKernel</key><string>24.99.99</string>
  <key>MinKernel</key><string>24.0.0</string>
  <key>PlistPath</key><string>Contents/Info.plist</string>
</dict>
```

Run the `ocvalidate` binary from the same OpenCore release as the test EFI.

## Boot modes

PCI-only fallback mode:

```text
-tdprobe
```

BAR0 read-only test mode, only after artifact audit:

```text
-tdprobe -tdmmio-read
```

Never add:

```text
-tdunsafe
```

Emergency disable:

```text
-tdoff
```

`-tdoff` may replace the TuringDarwin arguments when recovering through the
same test EFI. An untouched fallback EFI must still remain available.
