# M5StickS3 0.2.3 — portrait UI cleanup

Removes the horizontal divider and the word "LEVEL". RPM, the level bubble,
the angle and the USB-C-down portrait orientation remain in place.

Only these two drawing calls and the version string changed. Level calculations,
optical detection, 50 kS/s acquisition, buttons and power controls are unchanged.
The application was installed at `0x10000`; flash hash verification passed.
The device framebuffer confirms both requested elements are gone, and the
six-second status check has zero ADC read errors, overflows, invalid frames or
lost events. Build, flash, monitor and display evidence is saved in `evidence/`.

The preceding releases, including the original old-sensor build, are preserved.
For restore on an existing LaunchLab M5, write `LaunchLabMini.ino.bin` only at
`0x10000`. The exact binary hash and pinned toolchain are in `manifest.json`.
