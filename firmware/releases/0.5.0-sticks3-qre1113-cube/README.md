# M5StickS3 + QRE1113: 3D cube launch recap

Runtime `0.5.0-sticks3-cube`, based on the preserved
[0.4.3 recap](../0.4.3-sticks3-qre1113-recap/README.md).
See `manifest.json` for installation status and validation evidence.

The main recap shows peak RPM and a rectangular launcher moving and rotating
inside an isometric, equal-sided cube. The cube fits the complete estimated
trace and rotated glyph, centers the starting height vertically, and marks the
start on the right face facing the viewer. The rectangle replays once over
1.4 seconds, then holds its end pose until the five-second recap expires.
A recalls the latest recap; B opens history. Recorded Start/End tilt circles
remain frozen below the cube. The Motion history page shows the final cube view;
Recreate retains its RPM difference and recorded motion comparison graphs.

The travel trail is experimental: it integrates recorded acceleration change
between optical onset and end, with zero assumed initial velocity. Gravity
defines up; screen-top at onset defines horizontal forward. The rectangle's
rotation is relative to the recorded onset pose. The glyph is illustrative,
not a measured launcher dimension. A moving baseline, sensor bias, unknown
initial velocity and integration drift can distort height and displacement.
The screen labels it "Estimated path" and displays no distance or height.
Physical motion accuracy has not been validated against an external reference.
Normal moving starts are still accepted; no hold-still requirement is added.

The optical profile remains GPIO1, 3.3 V, 50 kS/s, 80-count minimum mark,
0.70 reversal hysteresis and a 1,000-RPM launch floor. Acquisition runs on its
existing dedicated task; cube drawing and cached geometry run on the UI core.
History/reference formats, ten-minute inactivity shutdown and battery page
remain available. The old TCRT5000 sensor release is preserved separately.

`LaunchLabMini.ino.bin` is the application image at `0x10000`, not address zero.
`source/` contains the matching firmware, build scripts and native tests.
`evidence/` contains build and sanitizer checks, plus device evidence when
installation is possible. USB `q` shows a labeled RAM-only recap demo; `e`
exports recorded motion and derived `REPLAY_POINT` estimates without adding
synthetic practice records.
