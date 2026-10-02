# M5StickS3 0.2.2 — portrait with USB-C down

The main screen is now 135×240 in native portrait (rotation 0), with USB-C and
Grove at the bottom. RPM and measurement state are above the level bubble and
tilt angle. Large RPM values fall back to a smaller font to fit the width.
The bubble uses M5Unified's board-normalized axes for this orientation.
The signal diagnostics page also fits portrait.

A pauses/resumes measurement; B toggles signal diagnostics. The side
Power/Reset button keeps its built-in double-click off / single-click on
behavior. Level smoothing, refresh limits and acceleration rejection are
unchanged from 0.2.1.

The 80-count / 0.70 optical profile, GPIO1, 50 kS/s ADC owner, recorder,
1,000-RPM floor and three-revolution detection rule are unchanged. QRE-specific
tuning was not applied. The original TCRT5000 release remains preserved in
`../0.2.0-sticks3-tcrt5000/`, and the landscape level release remains in
`../0.2.1-sticks3-level/`.

Only the application at `0x10000` was updated. Flash hash verification passed
and runtime status confirms version 0.2.2, rotation 0 and a 135×240 display.
The previous installed application was read back before flashing and matched
the archived 0.2.1 SHA-256 exactly. Native level tests passed; main and
diagnostics framebuffer captures were reviewed, with no ADC loss/errors during
the bounded live checks. See `manifest.json` and `evidence/` for exact evidence.

Physical upright orientation and bubble direction require a user check.
Independent angle/RPM calibration and fresh annotated pulls were not performed
for this display-only change.

To restore this release on an existing LaunchLab M5, write only
`LaunchLabMini.ino.bin` at `0x10000` with the local esptool environment.
Self-contained Arduino source is in `source/LaunchLabMini/`, and the level
test is in `source/tests/`. Use the pinned dependencies in the manifest.
