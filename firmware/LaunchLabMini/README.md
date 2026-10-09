# LaunchLab Mini for M5StickS3

Current published revision: **0.11.1-sticks3-themes-backup**, for **M5StickS3 K150 (ESP32-S3, 8 MB flash / 8 MB OPI PSRAM)** with an analog reflective sensor: **SparkFun QRE1113 analog** or a **TCRT5000** module. [Frozen release and validation](../releases/0.11.1-sticks3-qre1113-themesbackup/README.md).

Settings › Theme (Classic, Mint, Amber, Violet) tints the UI, and Settings › Best effect plays an effect on the recap of a new personal best for the active sensor profile and RPM method. Over USB, `K` exports a backup of history, sessions, personal bests, appearance, the saved recap and user settings as one checksummed container, and `R` restores one; the device validates the whole backup before writing anything, then restarts. 0.11.0 was withdrawn: it overflowed the loop task's 8 KB stack and restarted after boot. 0.11.1 keeps large buffers off that stack, and the build fails if a frame exceeds its budget.

## Wiring

Sensor VCC → Hat 3.3 V; GND → GND; analog OUT → Hat G1 / GPIO1. The Grove red wire supplies 5 V and must not be used as the sensor supply. Use the analog output; leave any digital output unused. See [assembly guide](../../docs/BUILD.md).

## Sensor profile

One firmware supports both sensors. Choose **Menu → Settings → Sensor profile**:

- **QRE / Standard** (default): 80-count minimum optical mark.
- **TCRT5000**: 60-count minimum, for the weaker marks a TCRT5000 module produces.

Both keep 0.70 hysteresis, 50 kS/s acquisition and three consistent turns to confirm a launch. A profile change waits until the device is idle and starts a new practice session on the next accepted pull; history is kept. The choice survives restart and shake wake.

## Controls

USB-C end down by default. Measurement stays on on every screen.

- **Main:** A shows the latest launch recap; B opens the menu. Hold A for one second to enter tournament mode.
- **Menus:** A opens or applies the highlighted item; B moves to the next choice; hold B goes back one level or cancels an edit. Every list has a Back choice.
- **Menu items:** History, New session, Battery, Settings, Tournament and Back. History offers Launches, Pull trend and Session trend. New session starts on the next accepted pull and keeps earlier launches.
- **Settings:** Sleep after, RPM method, Brightness, Flip display and Sensor profile. In an editor the value is centred, with a faint `B next option ->` hint beneath it: B cycles the value, A applies, hold B cancels.
  - Sleep after: 1–10 minutes, 3-minute default.
  - RPM method: 3-turn average (default) or 1-turn peak. The launch floor is 1,000 RPM.
  - Brightness: 10–100% in 10% steps.
  - Flip display: rotates the screen 180°. Brightness and flip preview immediately and revert if you cancel. Physical A/B buttons keep their roles when flipped.
- **Tournament:** starts in Recording Only; B cycles Recording Only / RPM; hold A exits. The selected view resumes after shake wake.

Accepted pulls show a five-second recap from Main. Menus, history and setting drafts stay open while launches keep recording. The battery page shows percentage, icon, voltage and charging status; the voltage-based percentage is not a calibrated capacity measurement.

## Acquisition and replay

A dedicated core-0 task owns continuous ADC1 DMA acquisition at **50,000 samples/s**. Detector time advances by sample count (20 µs per sample), independent of screen/USB delays. ADC losses invalidate sequence continuity and are reported in diagnostics. A separate lower-priority IMU task performs measured-time six-axis VQF fusion; screen/buttons/USB run on core 1.

The CPU starts at **80 MHz**; startup clock readback failure falls back to 240 MHz. Startup verifies fresh paired accelerometer/gyro data, makes up to three attempts, and retries a missing IMU owner every five seconds while idle.

After a pull, the recap shows RPM, frozen Start/End level dots and a rotation replay. With the display flipped, the live level, the Start/End dots and the 3D recap all follow the flipped screen; recorded data is unchanged. The IMU measures gravity-relative tilt and relative rotation, not travel distance or compass heading. RPM describes launcher-shaft speed, not stadium/release RPM.

History retains up to 128 launches and 24 sessions. Automatic checkpoints wait for ten quiet seconds after the last accepted pull. Standby flushes pending history; abrupt power loss can lose the pending bout.

## Power

Measured launches, button use and interactive USB commands refresh the inactivity timer. A detected USB computer keeps the device awake even without a serial reader. Battery sleep uses IMU shake wake. An unfinished setting edit is cancelled before sleep. Wait for the screen before pulling after wake.

## Build and verification

Run `bash scripts/build-firmware.sh` from the repo root with Arduino CLI installed. Dependencies: ESP32 3.3.0, M5Unified 0.2.23, M5GFX 0.2.30. Host/toolchain differences can change rebuilt bytes; use the frozen archive for exact binary restoration.

Run `bash scripts/test-firmware.sh`: 26 sanitizer-enabled native suites and seven production harnesses, including controls, display flip, sensor-profile storage, appearance and device backup, with a synthetic playback fixture instead of personal practice records. These software checks do not establish physical battery, recovery or calibration acceptance.

The frozen 0.11.1 application was installed app-only on the owner's M5StickS3 K150: no restarts in a 120 s soak, all 128 history records kept, a backup and restore round trip identical, and the screen, themes and pulls confirmed. Earlier, the 0.10.21 application was installed with complete native readback verification, with NVS, bootloader and partitions preserved. Actual device frames of the Flip and Sensor editors were checked. The user reports the installed firmware working on their device. Earlier revisions in this line had three-pull QRE1113 checks (0.10.14) and a six-pull TCRT5000 check (0.10.17). This is qualitative device acceptance, not long-session or absolute RPM/angle calibration.

[USB update and backup scope](../../docs/UPDATER.md) · [Recovery](../../docs/RECOVERY.md). Battery endurance, physical browser transfer, first install/rollback of this revision and stock recovery remain separate checks. Previous QRE and old TCRT binaries stay preserved.
