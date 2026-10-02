# M5StickS3 + QRE1113: single-sensor orientation

Runtime `0.6.1-sticks3-rotation`. Replaces the experimental travel trail with
continuous VQF 6D orientation fusion and a fixed-center, fixed-scale replay.
The rectangle preserves measured tilt; only unreferenced heading is reset.
Its white short-edge mark identifies the USB-C end. Forward recedes toward the
upper right. Start/End circles are frozen recorded tilt, not the current level.
No position, height, velocity, distance, force or compass direction is inferred.

The new capture waits for the fused post-roll timestamp, fixing blank recaps
caused by the raw poll arriving before the resampled endpoint. Gaps/clipping
still invalidate motion, with RPM recording independently. No per-launch
hold-still requirement is imposed. Natural rest improves gyro bias automatically.

A recalls five seconds of feedback; B opens history. Recreate compares
onset-relative rotation and angular speed with a fresh reference. Older
references remain stored/readable but are not mixed with new fused captures.
All 87 pre-update launches and 13 sessions were retained byte-for-byte in the
export comparison. Optical profile, battery page and ten-minute auto-off remain.

See `manifest.json` and `evidence/` for the installed binary hash, source,
algorithm provenance, native tests, device frames and performance checks.
Synthetic tests and USB readbacks do not establish physical angle accuracy.
The initial 0.6.0 development build is preserved with its known defects, as
are the earlier QRE and old TCRT5000 releases. Flash only the application at
`0x10000` on an existing LaunchLab installation.
