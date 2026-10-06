# 0.10.11 — Lower active CPU clock

For M5StickS3 K150 with the SparkFun QRE1113 analog sensor. Runtime: `0.10.11-sticks3-lowcpu`.

Runs at **80 MHz** instead of 240 MHz, set once before acquisition starts. A startup clock/readback failure falls back to 240 MHz. The peripheral clock stays at 80 MHz and optical sampling stays at **50 kS/s**, with the same sample-count RPM timebase. The selected RPM estimator, detector thresholds, IMU/VQF settings, brightness and sleep/wake policy are unchanged from 0.10.10.

Includes the preceding recap/storage repairs and computer USB keep-awake. The latest launch recap plays the measured pre/pull/post rotation at 1× and can be recalled with A. Separate Motion/Recreate pages are removed; history and tilt recording remain. History saves defer during capture/replay, pending records show “Unsaved launch”, and a failed standby flush keeps the device awake.

## Verification

- Application-only flash and device hash verified; 20 KB NVS was identical before boot. Saved settings and subsequent launch storage were checked.
- Twenty native suites and five production harnesses passed.
- Three labeled synthetic replays at each CPU frequency maintained 50 kS/s optical sampling, zero new ADC losses and approximately 100 Hz paired IMU sampling.
- At 80 MHz the largest ADC batch was 1.548 ms against a 5.120 ms budget. Largest synthetic draw was 33.230 ms against a 50 ms recap frame budget; largest observed physical draw was 34.432 ms.
- User confirmed normal pulls and replays looked good. The latest exported tilt trace was valid and fused.

One transient IMU gap/reset occurred in each controlled frequency trial. Post-pull flash checkpoints still cause rejected IMU gaps; no gap-free claim. Physical browser transfer, a four-image first install/rollback of this revision, stock recovery and a battery shake-wake cycle at 80 MHz remain unverified. Absolute RPM and angle calibration remain open.

**Battery savings are unmeasured.** Lowering the CPU clock by two thirds does not mean whole-device drain drops by two thirds. Persistent power diagnostics retain CPU frequency for the next battery-session comparison.

Application: 729,264 bytes at `0x10000`.
SHA-256: `4a49e2fc663efd89dca3ed527d1ba493c2cd5c39e03717fed2be263906751aaf`.

This is an installed, user-checked prototype revision. Public publication status is recorded in the manifest; this preparation does not establish buyer/pilot or recovery qualification.
