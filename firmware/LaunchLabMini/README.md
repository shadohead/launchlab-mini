# LaunchLab Mini for M5StickS3

Current published revision: **0.10.11-sticks3-lowcpu**, for **M5StickS3 K150 (ESP32-S3, 8 MB flash / 8 MB OPI PSRAM) + SparkFun QRE1113 analog**. [Frozen release and validation](../releases/0.10.11-sticks3-qre1113-lowcpu/README.md).

## Wiring

QRE VCC → Hat 3.3 V; GND → GND; analog OUT → Hat G1 / GPIO1. The Grove red wire supplies 5 V and must not be used as the sensor supply. Use the analog board/output; leave digital output unused. See [assembly guide](../../docs/BUILD.md).

## Controls

USB-C end down. Main is always ready. A recalls the latest launch recap; B opens history. A cycles Recent → Pulls → Sessions → Battery → Settings; B returns to main. Hold B on history to browse earlier windows; hold A starts a new session on the next accepted pull, except in Settings.

Hold A on main toggles tournament mode. B cycles **Recording Only / RPM**. Tournament hides the level and recap. Sleep/wake restores the previous mode/view.

Settings: hold B selects Sleep / RPM / Brightness; hold A changes/saves it. Sleep defaults to 3 minutes, configurable from 1–10. Brightness is 10–100% in 10% steps. RPM defaults to the peak three-consecutive-turn elapsed-time average; validated single-turn peak is selectable. Both require three consistent turns to confirm a launch; the launch floor is 1,000 RPM.

The battery page shows percentage, icon, voltage and charging status. There is no clock, idle countdown or approximate-charge caption. The voltage-based percentage is not a calibrated capacity measurement.

## Acquisition and replay

A dedicated core-0 task owns continuous ADC1 DMA acquisition at **50,000 samples/s**. Detector time advances by sample count (20 µs per sample), independent of screen/USB delays. ADC losses invalidate sequence continuity and are reported in diagnostics. A separate lower-priority IMU task performs measured-time six-axis VQF fusion; screen/buttons/USB run on core 1.

The CPU starts at **80 MHz** before M5 initialization and acquisition. The peripheral clock remains 80 MHz. Startup clock/APB readback failure falls back to 240 MHz. No runtime clock switching occurs. Optical thresholds, selected estimator and IMU configuration are unchanged from 0.10.10. Battery diagnostics record CPU frequency; whole-device battery savings are unmeasured.

After a pull, the recap shows RPM, frozen Start/End level dots and a rotation replay. It plays measured pre/pull/post context at 1× from the first completed display frame, then returns to main. A recalls it. Motion/Recreate pages have been removed. The IMU measures gravity-relative tilt and relative rotation, not travel distance, height change or absolute compass heading. RPM describes launcher-shaft speed, not stadium/release RPM.

History retains up to 128 launches and 24 sessions. Pending records show “Unsaved launch”. Saves coalesce after pulls and defer during capture/replay; standby flushes pending records and stays awake if the flush fails. Abrupt power loss can lose unsaved records. Real flash stalls still create IMU gaps; discontinuous tilt is rejected until fusion/pre-roll recover.

## Power

Measured launches, button use and interactive USB commands refresh the inactivity timer. A detected USB computer keeps the device awake even without a serial reader. Battery sleep uses IMU shake wake; A does not wake it. The green LED and boost stay off while awake. No one-hour hard-off policy is enabled. Wait for the screen before pulling after wake.

## Build and verification

Run `bash scripts/build-firmware.sh` from the repo root with Arduino CLI installed. Dependencies: ESP32 3.3.0, M5Unified 0.2.23, M5GFX 0.2.30. Host/toolchain differences can change rebuilt bytes; use the frozen archive for exact binary restoration.

Run `bash scripts/test-firmware.sh`: 20 sanitizer-enabled native suites and five production harnesses. These software checks do not establish physical battery/recovery/calibration acceptance.

The installed 0.10.11 app hash and pre-boot NVS preservation were checked. The user confirmed normal pulls/replays looked good; latest exported tilt was valid and fused. ADC batches and recap drawing fit their budgets in the measured 80 MHz trials. A battery shake-wake cycle at 80 MHz, endurance/current comparison, absolute RPM/angle calibration, physical browser transfer, first install/rollback of this revision and stock recovery remain open. Post-pull storage still causes rejected IMU gaps.

[USB update and backup scope](../../docs/UPDATER.md) · [Recovery](../../docs/RECOVERY.md). This is a prototype revision with qualitative device acceptance; buyer/pilot qualification remains open. Previous QRE and old TCRT binaries stay preserved.
