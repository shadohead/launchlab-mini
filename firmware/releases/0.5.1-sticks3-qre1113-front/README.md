# M5StickS3 + QRE1113: fixed front-edge start

Runtime `0.5.1-sticks3-front`, based on the preserved
[0.5.0 cube replay](../0.5.0-sticks3-qre1113-cube/README.md).
Every replay now starts on screen at the midpoint of the front vertical cube
edge nearest the viewer. The cube retains equal sides and encloses the entire
estimated motion and every rotated rectangle pose.

The cube is positioned along the isometric viewing direction so that the
recorded zero-origin pose projects onto that edge midpoint. This changes the
display framing without translating, folding, mirroring or scaling individual
motion coordinates. The zero-origin pose is physically inside the bounds;
its projection coincides with the fixed front-edge landmark. Mid-height cube
guides cross that landmark. Recorded motion estimates and gyro poses are
unchanged from 0.5.0. The experimental travel estimate still assumes zero
initial velocity and is not calibrated height or distance.

The replay runs once over 1.4 seconds, then holds its last pose. The recap
returns to live after five seconds. A recalls it; B opens history. RPM,
frozen Start/End tilt circles, ten-minute auto-off, battery page, history and
sensor settings remain available. The reference/storage formats are unchanged.

See `manifest.json` and `evidence/` for build, native geometry checks, flash,
retained-history comparison and device frame readbacks. Application image
`LaunchLabMini.ino.bin` belongs at `0x10000`. The prior cube and old TCRT5000
sensor releases are preserved separately.
