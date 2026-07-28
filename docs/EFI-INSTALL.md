# Add to a separate test EFI

Do not alter the known-good `EFI_STABLE` copy.

1. Duplicate the stable EFI onto a second USB EFI partition.
2. Copy the built bundle to:
   `EFI/OC/Kexts/TuringProbe.kext`
3. Add this entry as the last item in `Kernel -> Add`:

```xml
<dict>
  <key>Arch</key><string>x86_64</string>
  <key>BundlePath</key><string>TuringProbe.kext</string>
  <key>Comment</key><string>TuringProbe 0.1 read-only PCI probe</string>
  <key>Enabled</key><true/>
  <key>ExecutablePath</key><string>Contents/MacOS/TuringProbe</string>
  <key>MaxKernel</key><string>24.99.99</string>
  <key>MinKernel</key><string>24.0.0</string>
  <key>PlistPath</key><string>Contents/Info.plist</string>
</dict>
```

4. Append `-tdprobe` to the test EFI's `NVRAM -> Add ->
   7C436110-AB2A-4BBB-A880-FE41995C9F82 -> boot-args`.
5. Run the matching `ocvalidate` from the OpenCore release used by that EFI.
6. Boot the USB explicitly from the motherboard boot menu.

Do not add `-tdmmio-read` or `-tdunsafe`; v0.1.1 rejects them. Keep `-tdoff`
available as the emergency disable argument.
