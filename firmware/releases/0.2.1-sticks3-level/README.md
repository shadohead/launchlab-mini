# M5StickS3 0.2.1 — restored level display

Adds the circular bubble and tilt angle beside RPM on the main screen. The
onboard BMI270 supplies gravity readings; the screen plane is the reference.
Hold the device still when using the level. Cyan means within 2 degrees;
orange means tilted. The rim represents 30 degrees. Missing or stale readings
hide the bubble and show `--`; acceleration outside the gravity range shows
`Hold still`. The normal screen stays still during a measured RPM burst.

A still pauses/resumes measurement; B toggles signal diagnostics. The side
Power/Reset button retains its built-in double-click off / single-click on
behavior. USB `p` includes level readiness, angle and performance; `v` exports
the last displayed frame for diagnostics.

The 80-count / 0.70 optical profile, GPIO1, 50 kS/s ADC owner, recorder,
1,000-RPM floor and three-revolution detection rule are unchanged. QRE-specific
tuning was not applied. The exact original TCRT5000 release remains preserved
in `../0.2.0-sticks3-tcrt5000/`.

The application was installed at `0x10000` and flash hash verification passed.
The bootloader, partitions and existing preferences were retained. See
`manifest.json` for the binary hash and validation boundaries, and
`../../evidence/sticks3-0.2.1-level/` for build, flash, monitor and display
readback evidence. Native level tests and all 13 M5 capture regressions passed.

A user tilt-direction check, independent angle calibration and fresh annotated
pull testing remain separate from build/flash/runtime proof.

To restore this release on an existing LaunchLab M5, write only the application
`LaunchLabMini.ino.bin` at `0x10000` with the local esptool environment. The
self-contained Arduino source is in `source/LaunchLabMini/`; native tests are
in `source/tests/`. Use the same pinned dependencies listed in the manifest.
