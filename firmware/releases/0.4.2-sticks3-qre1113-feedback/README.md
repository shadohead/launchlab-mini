# M5StickS3 + QRE1113 main-screen feedback

Runtime `0.4.2-sticks3-feedback`. App-only update at `0x10000`; the existing
80-count / 0.70 optical profile, 1000-RPM floor, history, battery page and
10-minute inactivity shutdown are preserved.

Measurement stays enabled. A new pull shows five seconds of RPM, relative turn
path, final relative roll/pitch/yaw and a small live level. A recalls that latest
feedback, or returns to live immediately. B opens history; A then cycles Recent,
Pulls, Sessions, Battery, Motion and Recreate. Both level directions are reversed
following the mounted-device report; dynamic acceleration hides the level dot.

There is no hold-still requirement. A naturally stable baseline can improve gyro
bias automatically; moving before a pull is accepted. Motion is relative
rotation and acceleration change from a pre-launch baseline, not traveled
position or distance. Missing/clipped/gapped sensor data remains visibly
unavailable without discarding the measured RPM.

In Recreate, the first usable pull becomes the reference; subsequent attempts
show gray/cyan overlays on shared elapsed-time scales, rotation/acceleration
error and signed RPM difference. Hold A on Motion/Recreate to select the latest
usable pull as reference; hold B arms the next one. The reference persists in
two compact checksummed NVS slots. Latest attempt motion stays in RAM; the last
RPM remains available after reboot, along with its path if it was the saved
reference. Earlier RPM-only records have no invented motion.

`manifest.json` records the exact binary and validation scope. `source/` contains
the matching sketch, headers and tests. `evidence/` contains build/install,
retention, motion, framebuffer and runtime checks. Flash readback/NVS backups
stay private locally. Prior power, QRE working baseline and old TCRT5000 releases
are retained separately. Review the manifest for the fresh physical validation
boundary; software tests do not establish absolute spatial or RPM calibration.
