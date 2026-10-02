# LaunchLab Mini for M5StickS3

**Working combination: M5StickS3 K150 + SparkFun QRE1113 analog.** The user
confirmed on 2026-10-01 that the installed firmware "works pretty well".
The confirmed baseline binary and source are saved as
[0.3.0-sticks3-qre1113](../releases/0.3.0-sticks3-qre1113/README.md); its runtime
version is `0.3.0-sticks3-practice`. The existing 80-count / 0.70 optical
profile is unchanged. The original old-sensor three-pull release is preserved as
[0.2.0-sticks3-tcrt5000](../releases/0.2.0-sticks3-tcrt5000/README.md).
The QRE confirmation is a qualitative live-use result; an annotated exact
pull-count trial, absolute RPM calibration and battery power-cycle retention
are separate checks.

The current motion/recreate update is saved as
[0.4.2-sticks3-qre1113-feedback](../releases/0.4.2-sticks3-qre1113-feedback/README.md).
The prior [power update](../releases/0.3.1-sticks3-qre1113-power/README.md) is preserved.
Version `0.4.2-sticks3-feedback`, for StickS3 K150 (ESP32-S3,
8 MB flash, 8 MB OPI PSRAM). Uses the installed Arduino ESP32 3.3.0,
M5Unified 0.2.23 and M5GFX 0.2.30 dependencies. This is a separate board
application; the Waveshare binary cannot be installed on the M5.

## Acquisition and performance

`acquisition.h` owns all ADC calls, detector state and recorder writes in one
priority-3 task on core 0. M5Unified, screen drawing, buttons, USB and
Preferences remain on Arduino core 1. The IMU also runs on core 0, at
lower priority than the ADC owner; it never owns the ADC. The UI exchanges commands and immutable
snapshots through queues and short critical sections. It never reads the live
detector or changes the ADC handle directly. Results/state changes use a
bounded event queue, with loss explicitly counted in diagnostics.

Sampling uses ADC1 continuous DMA, 50,000 samples/s, 12-bit, 12 dB attenuation,
TYPE2 output, 1,024-byte frames and a 32,768-byte driver pool. GPIO mapping is
queried from the installed driver. AO has no pull-up or pull-down. Each sample
advances detector time by 20 us regardless of UI or USB delays. All samples in
a frame must match the selected unit/channel; malformed frames and DMA
loss invalidate the detector sequence and recorder continuity. ADC read errors
and overflow trigger recovery in the owning task. Setup failures are retried
once per second.

The recorder retains 60 seconds (6 MB) in PSRAM. A wrapping cursor replaces
64-bit modulo in the per-sample write path. Absence of PSRAM recording does
not stop RPM acquisition and is reported as `recorder_s=0`.

`PERF` reports sample-processing wall time as a fraction of the acquisition
window, worst batch duration, worst read interval, task stack headroom,
invalid frames, lost events, display duration and available memory. Processing
percentage excludes blocking ADC reads and snapshot/driver overhead; it is
not a measurement of total CPU utilization. One 256-sample batch has a
5,120-us time budget. Keep batch duration comfortably below this budget and
verify zero ADC loss under UI/USB load.

## M5 sensor profile

The shared detector retains its original Waveshare defaults: 300-count mark
floor and 30% reversal hysteresis. `sensor_profile.h` applies **M5-only**
settings: **80-count minimum mark**, **70% of repeated mark swing** for reversal
hysteresis. This change is based on the confirmed 2026-09-30 TCRT5000 pull:
89–130 count marks contain subsidiary peaks that the original detector counted
as extra cycles. Lowering the mark floor alone does not decode that capture.

One cycle/revolution, the 1,000-RPM start floor, three consistent revolutions,
first-burst peak selection and quiet/rewind rearm rules are preserved. The M5
profile reproduces one provisional ~4,945 RPM result in the saved pull and
rejects the available weak idle/handling negatives. It remains an initial
measured profile, not proof of repeatable mounted detection or absolute RPM
accuracy. A different sensor, distance or reflective mark may need a different
profile. Do not remove the amplitude floor or notch 60 Hz: 60 Hz is also a
legitimate 3,600 RPM optical signal.

The normal screen stays still during an accepted burst. Screen start/end
boundaries are retained in recorder bits 15/14, on the first consumed ADC batch
after each UI boundary (about 5 ms resolution). They are evidence markers;
**the Waveshare's measured 2.5–14 ms blanking interval does not apply here**.
M5 exports report `display_blanking=false`. Replay with `replay_sticks3.cpp`,
which ignores display markers for counting, rather than the Waveshare replay
which applies its own blanking when bit 15 appears.

## Wiring and controls

AO defaults to Hat G1, ADC1 channel 0. Sensor VCC uses 3V3_L2/3V3, and ground
uses GND. GPIO0/BOOT is not an ADC input. Use analog AO/OUT. Grove red is 5 V;
do not treat it as a 3.3 V sensor supply. The current user's sensor-end supply
was measured at 3.3 V. The firmware does not automatically alter sensor power,
ADC attenuation, or GPIO selection.

- Portrait screen with USB-C / Grove down (rotation 0, 135×240 pixels).
  Main screen retains peak RPM and detector state above the bubble, without
  a divider or "LEVEL" label. Large
  RPM numbers automatically use a smaller font if needed to fit the width.
- A circular level and tilt angle appear below RPM on the main screen. The
  built-in BMI270 is initialized through M5Unified; fresh acceleration is
  sampled by a dedicated priority-2 task on core 0, polling every 5 ms,
  with 200-ms level smoothing. Display changes are
  limited to 10 Hz and meaningful dot/angle changes. The dot is cyan within
  2 degrees and orange beyond; 30 degrees reaches the rim. The screen plane is
  the reference, not a calibrated launcher mounting plane or launch trajectory.
  Both bubble directions are reversed from 0.3.1 following the user
  report that left/right and up/down were mirrored on the mounted device.
- Accelerations outside 0.75–1.25 g hide the bubble and show "--". Missing
  or stale (>250 ms) samples show "--". Acceleration within that interval can
  still affect tilt, so use level while holding still. Normal display updates
  remain frozen during accepted RPM bursts. IMU calls cannot block the
  independent ADC owner.
- Measurement stays enabled. On the main page, short A toggles between
  live and recent launch feedback; short B opens history
  or returns to live. In history, short A cycles recent launches, pull trend,
  session trend, battery, Motion, and Recreate. Hold B for one second to browse older history
  windows; on live,
  hold B opens signal diagnostics. Hold A for one second starts a new session
  on the next accepted launch without creating an empty session, except on
  Motion/Recreate where hold A selects the current usable pull as the reference.
  Hold B on either motion page arms the next usable pull as a new reference.
- Side Power/Reset: double-click off, single-click on/reset. Long press enters
  download mode; these are built-in hardware controls.
- Automatic power-off is enabled after 10 minutes without a measured pull,
  button use or an interactive USB command. Background level/battery updates,
  raw optical noise and status polling do not reset the timer. Active measured
  bursts are protected by the ADC owner. Pending history and reference data are saved before
  shutdown; a failed save defers shutdown and retries after a minute.
- The battery page is after session trend: tap B from live, then tap A to
  cycle to it. It shows approximate charge percentage, battery voltage,
  charging status and the inactivity countdown. PM1 I2C battery/status reads
  run at most once every five seconds on the UI core. There are no battery ADC
  calls and no claimed hours remaining. Missing/stale reads show "--".
- USB `p`: status, detector profile and performance.
- `m` / `r`: open Motion / Recreate; `k`: select current usable reference;
  `l`: use next usable pull as reference; `e`: export real motion points.
  `f`: clearly labeled RAM-only motion preview, with no practice/reference writes.
  `z`: guarded reference storage bench: 16 saves/reopens in `ll-mot-qa`,
  cleaning only its own scratch keys.
- `MOTION_STATUS` reports fresh paired samples, task timing/stack, capture quality,
  reference state and dropped pending captures.
- `LEVEL_STATUS` reports IMU readiness/type, fresh sample count, rejected
  samples, angle, acceleration and worst poll duration.
- `a`: recent/live toggle; `d`: signal display.
- `h`: toggle history; `c`: next history view; `b`: older window; `n`: new session;
  `u`: export retained launches and full session summaries to USB.
- `t`: clearly labeled RAM-only demo preview. It cannot add synthetic data to
  the actual practice history or storage. Toggle it off or press B to return.
- `y`: USB-only storage diagnostic, requiring no active burst or pending capture.
  The ADC owner rechecks the launch counter, pauses only for the scratch writes
  and resumes automatically.
  It writes/reopens 36 snapshots in the dedicated `ll-prac-qa` namespace and
  removes only those scratch keys. Actual practice records are untouched.
- `v`: export the last displayed 135×240 RGB565 frame. A 16-bit canvas permits
  one display transfer per frame and diagnostic readback. Allocation failure
  falls back to direct display drawing without stopping RPM or level sensing.
- `g1\n` through `g10\n`: select/persist an exposed ADC1 GPIO. Invalid input is rejected.
- `x`: explicitly toggle/persist external 5 V output (default off).
- `s`: toggle a 20 Hz diagnostic display stress mode, including during bursts.
  Disable it after testing. `j`: deliberately pause the UI for 200 ms without
  blocking acquisition. Both are diagnostic commands, not normal controls.
- `w`: export the newest contiguous raw recorder segment. The owning task
  stops acquisition and acknowledges before the UI accesses recorder memory.
  After ACK/FNV-checked transfer, the owner flushes/restarts acquisition and
  resets detector history. Sampling is intentionally paused during export.
  Use `firmware/tools/flight_recorder.py`, not the plain console for `w`.

## Launch motion and recreate practice

Every new accepted pull opens five seconds of feedback on the main page,
showing RPM, the relative turn path, final relative roll/pitch/yaw and a small
live level. After capture finishes, the full five-second display starts, then
returns to live automatically. A tap on A recalls the latest launch for another
five seconds; tapping A again returns immediately. Measurement remains enabled
in both views. A newer pull replaces the feedback and restarts the timer.
After reboot, A can show the latest saved RPM; its motion is available only
when that same pull was the saved reference. Otherwise the page explicitly
requires fresh motion data. The most recent in-memory trace is kept after the
five-second display ends. B still opens the history and practice pages.

Tap B from live, then A through the tabs to Motion or Recreate. There is no
hold-still requirement; capture runs during normal handling and pulls. Motion draws the launcher's relative tilt
path in degrees. The first usable pull in Recreate becomes the reference;
subsequent pulls compare against it. Hold A to select the latest usable pull,
or hold B to use the next usable pull as a new reference. The reference is
saved across reboot in separate alternating checksummed `ll-motion` NVS slots.
Schema 2 records whether automatic stationary bias was used; existing schema-1
references remain readable.
No historical motion is invented for earlier RPM-only records. The latest
attempt stays in RAM; this version retains one reference, not every motion trace.

Gray is the reference; cyan is the latest attempt. Recreate displays actual
peak RPM and its signed difference/percentage, a full 3D relative-rotation RMS
error in degrees, acceleration-change and angular-speed overlays, acceleration
RMS error and pull-duration difference. Each overlay shares the same scale and
elapsed time, with zero at optical burst onset. Comparisons interpolate the
reference over shared time without stretching either pull to match duration.
Errors use all three axes, even though the two graphs show vector magnitudes.
The Motion tilt path projects the device normal, so twisting around that normal
is represented in the gyro/rotation error rather than the two-dimensional path.

Fresh paired acceleration/gyro samples come from one dedicated IMU owner
on core 0 at priority 2, below the priority-3 optical ADC owner.
M5 button/power/battery operations share its I2C mutex. UI drawing and USB
stalls on core 1 do not own the task. Flash/cache stalls can still produce
counted gaps; captures overlapping them are rejected. A 1024-sample ring keeps
pre-launch data; captures
cover 500 ms before optical onset to 250 ms after burst end, reduced to at most
48 points with their actual timestamps. A 250-ms baseline ending 600 ms before
onset provides the
pre-launch acceleration vector. Only a naturally stable baseline estimates gyro
bias; a moving baseline uses the SDK gyro values directly and is accepted.
Gyro integration produces relative orientation. Acceleration change is the
rotated measured vector minus that pre-launch baseline, not guaranteed isolated
linear acceleration when the baseline itself was moving. This measures relative
turns and acceleration, not distance or
absolute spatial position. Optical/IMU clock alignment is approximate at the
DMA-frame and polling resolution, rather than hardware synchronized.

Missing coverage, gaps over 35 ms during integration, clipping near the SDK's
8 g / 2000 deg/s limits, and bursts over 2.5 seconds are shown
as unusable captures. They cannot replace the reference. Movement before a pull
never rejects it. RPM/history still
work when motion is unusable. Drawing waits until the burst finishes, preserving
the existing optical acquisition behavior. Saving history waits for the 250-ms
motion post-roll; flash writes remain guarded ADC checkpoints and can produce
IMU gaps outside the finished capture. A save failure remains visible and the
previous durable reference is preserved. Recreate with too little shared time
shows a retry message instead of a misleading zero error.

## Practice history

Accepted peak RPM is the practice metric. Failed, cancelled and duplicate result
events are excluded. Retains the latest 128 individual launches and 24 session
summaries. Every session's mean and best include all of its accepted launches,
even after its oldest individual readings leave the ring. A session starts on
the first pull after boot, after 10 minutes without an accepted pull, or after
the manual new-session gesture. Older windows are browsable with hold B.

Pull trend shows up to 30 readings as gray points, with a cyan trailing five-pull
mean. Session trend shows up to 12 session means in each window, with that
window's most recent session count and best. Change compares the first and last
five pulls (at least 10 readings), or first and last two session means (at least
four sessions); these groups do not overlap. Axes use pull/session order, not
calendar dates or equal elapsed intervals. Keep the same launcher, sensor setup
and practice conditions when comparing RPM. It is an RPM trend, not calibrated
force or a causal measure of technique improvement.

Two versioned, checksummed NVS snapshots in the separate `ll-practice` namespace
alternate on accepted launches. Saves read back the exact bytes before marking
the data saved. Boot chooses the newest valid copy and retains the previous copy
after a failed write. Unsupported/corrupt storage is reported and never erased
automatically. A save failure is visible on history and in USB status.

The installed ADC driver is not configured for cache-safe interrupts during
flash operations. Therefore the ADC owner acknowledges a guarded checkpoint
in rearm; an explicit reference save may also
checkpoint while ready after the ADC owner rechecks the launch counter. Flash writes briefly pause sampling;
the completed RPM remains visible and fresh quiet is required before rearming.
No checkpoint can interrupt an active measured burst. The raw recorder begins
a new contiguous segment after each checkpoint, just as after other acquisition
gaps; `w` exports that newest segment rather than inventing continuous time
across the save. Do not interpret delivered sample rate as uninterrupted uptime.
Power-off during a save can lose the newest unsaved result; prior saved data
remains available. No older on-device readings are invented when upgrading.

## Build and validation

```sh
bash firmware/setup-m5.sh
bash firmware/build-m5.sh
clang++ -std=c++17 -O2 -Ifirmware/LaunchLabRpm firmware/tests/test_sticks3.cpp -o /tmp/test-sticks3
/tmp/test-sticks3
clang++ -std=c++17 -O2 firmware/tests/test_sticks3_level.cpp -o /tmp/test-sticks3-level
/tmp/test-sticks3-level
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined firmware/tests/test_sticks3_power.cpp -o /tmp/test-sticks3-power
/tmp/test-sticks3-power
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined firmware/tests/test_launch_feedback.cpp -o /tmp/test-launch-feedback
/tmp/test-launch-feedback
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined firmware/tests/test_launch_motion.cpp -o /tmp/test-launch-motion
/tmp/test-launch-motion
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined -Ifirmware/tests/fakes firmware/tests/test_motion_store.cpp -o /tmp/test-motion-store
/tmp/test-motion-store
clang++ -std=c++17 -O2 -Ifirmware/LaunchLabRpm firmware/tests/replay_sticks3.cpp -o /tmp/replay-sticks3
python3 firmware/tests/check_sticks3_replays.py /tmp/replay-sticks3
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined -Ifirmware/LaunchLabRpm firmware/tests/test_practice_history.cpp -o /tmp/test-practice-history
/tmp/test-practice-history
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined -Ifirmware/tests/fakes firmware/tests/test_practice_store.cpp -o /tmp/test-practice-store
/tmp/test-practice-store
```

Also run `test_analog_tachometer.cpp` and `check_analog_replays.py` to verify
the original Waveshare defaults/regressions. Preserve the installed application
before updating. On an existing LaunchLab M5 installation, update **only**
application offset `0x10000`; do not rewrite settings, partitions or bootloader.
`flash-m5.sh` installs the complete initial board layout and is for initial
setup, after preserving the factory image.

The initial installed three-pull check passed: the user confirmed three working
pulls, the device counter advanced to three, and checksum-verified raw replay
accepted all three. Latest live result: 6,406 RPM (not independently calibrated).

Evidence for the acquisition baseline is in `firmware/evidence/sticks3-0.2.0/`;
the original level update is retained in `firmware/evidence/sticks3-0.2.1-level/`,
and the portrait update in `firmware/evidence/sticks3-0.2.2-portrait/`. Practice
history evidence is in `firmware/evidence/sticks3-0.3.0-practice/`; QRE release
metadata records the subsequent user confirmation. Battery/runtime evidence
for the power update is in
`firmware/evidence/sticks3-0.3.1-power/`. Motion/recreate evidence is in
`firmware/evidence/sticks3-0.4.2-feedback/`. Flash hash
verification proves installed bytes; USB status/stress checks prove acquisition
behavior. Repeated annotated live pulls establish detection reliability.
Independent known-speed shaft/tachometer testing is still needed for absolute
RPM accuracy. Battery-only sampling/power endurance also needs separate testing.

Official references:
- https://docs.m5stack.com/en/core/StickS3
- https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/adc_continuous.html
