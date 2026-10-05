# LaunchLab Mini for M5StickS3

Current update: [0.10.7 clearer navigation](../releases/0.10.7-sticks3-qre1113-navigation/README.md). History, battery, motion and Settings pages say `A next page  B main`: tap A cycles the pages; tap B returns to the main launch screen. The battery page shows percentage, icon, voltage and charging status; no clock, countdown or approximate-charge caption. Settings brightness is saved in 10–100% steps; hold B selects Sleep/RPM/Brightness, hold A changes it. Shake-only standby, green LED off while awake and saved power diagnostics remain from 0.10.2.

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

The refined single-sensor orientation recap is built offline and saved as
[0.10.1-sticks3-qre1113-tiltreplay](../releases/0.10.1-sticks3-qre1113-tiltreplay/README.md).
The former [estimated-travel recap](../releases/0.5.1-sticks3-qre1113-front/README.md) is preserved.
The prior [cube recap](../releases/0.5.0-sticks3-qre1113-cube/README.md) is preserved.
The prior [frozen level recap](../releases/0.4.3-sticks3-qre1113-recap/README.md) is preserved.
The prior [motion/recreate update](../releases/0.4.2-sticks3-qre1113-feedback/README.md) is preserved.
The prior [power update](../releases/0.3.1-sticks3-qre1113-power/README.md) is preserved.
Version `0.10.1-sticks3-tiltreplay`, for StickS3 K150 (ESP32-S3,
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

One cycle/revolution, the 1,000-RPM start floor, three consistent revolutions
to confirm a pull, first-burst selection and quiet/rewind rearm remain.
The default result is the maximum valid **three-consecutive-turn elapsed-time
average**: `180000000 / (period1_us + period2_us + period3_us)`.
This restores the frozen 0.6.2 algorithm, not an arithmetic mean of RPMs or three
nonadjacent fastest turns. Settings also offers **1-turn peak**: after confirmation,
one complete valid revolution can set its peak, without requiring that faster
speed to repeat. Its timing, duty, amplitude and neighboring mark must match
established optical shape. The arrival mark is checked after the 0.5-ms optical
mean settles, without another full revolution. Both metrics are calculated from
the same stream; the three-turn control path governs confirmation, slowdown and
quiet/rearm timing for both selections. Tracking the alternative cannot extend
quiet/rearm timing. Other boards retain their original detector defaults.

The existing timing ceiling is 30,000 RPM (2-ms periods), a measurement bound,
not a scientifically established human limit. Detector edge timestamps have
100-us resolution; a single-turn peak is more sensitive to quantization and
optical jitter than the former average. It remains an average over one turn,
not instantaneous speed within that turn or directly measured release RPM.
`RPM_ESTIMATORS` reports both metrics and the selected method; `LAUNCH_METRICS`
logs both and the selected result for each accepted shot in RPM units. No magnetometer/IMU speed estimate
is substituted for optical speed.

Saved traces reproduce ~4,945 RPM three-turn and ~5,128 RPM single-turn estimates
for the confirmed old-sensor pull. The 14-trace comparison matches frozen 0.6.2
three-turn results and prior single-turn peak values. Several traces are from
another board or lack individual pull annotations; these are software evidence,
not absolute RPM calibration or proof of mounted repeatability. The 100-us edge
grid and optical shape can affect results. No 60-Hz notch is applied, since it
could remove a legitimate 3,600 RPM signal.

The new versioned `launchlab-mini/rpm_method` key persists the selector; missing
means three-turn default and corrupt bytes are retained with a default fallback.
Valid sleep/GPIO settings and existing history/reference images are preserved.
Changing method starts a new session on the next accepted pull and clears the
live number until then. Boot also starts a fresh session. Existing history stores
only its original scalar RPM: older records have no encoded estimator identity,
and neither historical values nor trend labels are rewritten. Paired metrics
are in RAM and USB logs, not added to the persistent history schema. Therefore
cross-session trends can still span different estimators; compare sessions with
the same selected method. The single-turn figure is not instantaneous release
speed, and this measurement is not official Shoot Power.

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
  session trend, battery, Motion, Recreate, and Settings. Hold B for one second to browse older history
  windows; on live,
  hold B opens signal diagnostics. Hold A for one second on the main page
  toggles **tournament mode**, starting with a static red RECORDING ONLY card.
  Short B cycles **recording only → RPM → recording only**.
  Every view keeps recording launches; titles, status, hints and automatic
  recap stay hidden. Short A and hold B are ignored; hold A for one second exits.
  Acquisition, history, motion recording, power controls and auto-off continue.
  Tournament mode and its selected view resume after automatic sleep.
  A normal restart returns to normal; toggling modes does not write flash.
  The resume record is saved only before sleep and consumed once at startup.
  On Settings, hold B selects Sleep or RPM method; hold A changes and saves the
  selected row. Sleep choices are 1–10 minutes; RPM choices are 3-turn average
  (default) or 1-turn peak. Short A cycles pages; short B returns to main.
  Hold A in other history views starts a new session on the next accepted launch without
  creating an empty session, except on
  Motion/Recreate where hold A selects the current usable pull as the reference.
  Hold B on either motion page arms the next usable pull as a new reference.
- Side Power/Reset: double-click off, single-click on/reset. Long press enters
  download mode; these are built-in hardware controls.
- Automatic IMU-only sleep is enabled after a configurable timeout (default 3 minutes) without a measured pull,
  button use or an interactive USB command. Background level/battery updates,
  raw optical noise and status polling do not reset the timer. Active measured
  bursts are protected by the ADC owner. Pending history and reference data are saved before
  sleep; a failed save defers sleep and retries after a minute.
  A shake wakes the device through BMI270 any-motion and M5PM1 GPIO4.
  Only the accelerometer/IMU rail is held on; the sensor's 3V3_L2 rail turns off.
  Initial shake threshold is approximately 983 mg for 120 ms on any axis.
  Ordinary IMU movement while awake does not extend the selected timeout.
  Wake restarts the firmware and restores the previous mode/page; wait for the screen before pulling. The normal
  VQF startup settling period still applies to motion feedback, not optical RPM.
  A manual side-button power-off remains manual; it does not arm shake wake.
  USB command `i` arms, reads back and restores the wake configuration without sleeping.
  Current draw, wake latency and shake sensitivity require physical validation.
- The battery page is after session trend: tap B from live, then tap A to
  cycle to it. It shows approximate charge percentage, battery voltage,
  charging status and the inactivity countdown. PM1 I2C battery/status reads
  run at most once every five seconds on the UI core. There are no battery ADC
  calls and no claimed hours remaining. Missing/stale reads show "--".
- USB `p`: status, detector profile and performance.
- `m` / `r`: open Motion / Recreate; `k`: select current usable reference;
  `l`: use next usable pull as reference; `e`: export real motion points.
  `f`: clearly labeled RAM-only motion preview, with no practice/reference writes.
  `q`: labeled five-second recap preview, also RAM-only, with no real-record writes.
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

Every accepted pull opens five seconds of feedback: RPM, a fixed-center
launcher rotating in an isometric cube, and frozen Start/End tilt circles.
The launcher stays in one location. There is no travel trail, height estimate,
velocity, displacement, or compass heading. Cube and body size are constant
across captures and have no physical distance units. The 1.8-second replay
shows optical onset through optical end, then holds the end pose. A progress
marker identifies playback time. Pre/post samples are retained in the capture
for comparison/storage; they are not played as part of the pull. The replay preserves measured gravity-relative tilt. Only arbitrary heading is
reset at optical onset; it does not flatten the initial pose.
The circles record gravity-relative tilt at optical onset/end; they never follow
the current sensor. Recap omits numeric angles and is labeled "Tilt replay". The portrait body
has a blue screen, violet back, dark sides, screen inset and white USB-C cap.
A quieter, tighter cage and fixed middle-height reference make tilt easier to
interpret. The automatic recap shows one body; gray reference endpoint remains
on the dedicated Motion page. Missing/pending tilt has a plain status label.
Its neutral heading faces the viewer midway between the two front cube walls,
aligned with the nearest vertical edge, instead of following the left wall.
This fixed 45-degree display-heading offset does not change measured tilt,
relative rotation, or Start/End dots. The rectangle remains centered in the cube.
An unknown board-to-launcher mounting rotation is not silently assumed calibrated.
A recalls the recap; B opens history. RPM acquisition is always enabled.

`orientation_estimator.h` continuously runs the upstream VQF 6D filter, using
fresh paired acceleration/gyro readings. Timestamp-based trapezoidal gyro
resampling preserves measured elapsed time on a 100 Hz filter grid. Acceleration
is interpolated onto the same grid. Gyro units are converted to rad/s and
acceleration to m/s² before VQF. The algorithm estimates gyro bias during natural
rest and motion, and filters acceleration in an approximately inertial frame
for inclination correction. No magnetometer or external sensor is used.
The pinned MIT-licensed C++ source and provenance are in `src/vqf/`.
`build-m5.sh` compiles it in single precision, while the upstream Butterworth
filters retain double precision. Filter parameters are upstream defaults.

Fusion runs before capture and chart reduction. Start/End poses are interpolated
from full-rate fused samples at their exact optical timestamps. The 48-point
trace dedicates up to 24 points to the optical interval, including onset/end,
and retains pre/post-roll. It does not infer additional motion from additional
chart points. The live level uses the continuously fused gravity direction.
M5Unified's mounted-device axis mapping and the user-confirmed dot directions
are preserved. Sensor-to-launcher mounting calibration is not inferred.

Rotation comparison uses `inverse(onset) * pose` in each launch's initial sensor
axes. Arbitrary heading and different starting tilt do not become artificial
rotation errors. The frozen circles show starting/ending tilt separately.
Recreate shows peak RPM difference, relative-rotation RMS difference in degrees,
a rotation-difference curve, angular-speed overlays, and pull-time difference.
Curves share real elapsed time with zero at optical onset; neither pull is
stretched to match the other. This compares measured rotational behavior, not
travel or force. The optical DMA and IMU polling clocks are approximately
aligned, not hardware synchronized; very fast pulls have limited IMU samples.

Tap B, then A through the tabs to Motion or Recreate. The first usable pull in
Recreate becomes the reference. Hold A to select the current usable capture,
or hold B to arm the next one. Alternating checksummed `ll-motion` NVS slots
retain the reference. Schema 4 marks fused captures; older schemas remain
readable and their bytes are retained, but they cannot be compared as if they
were captured by the new estimator. Choose a fresh reference. The image remains
1124 bytes. No motion is invented for older RPM records; latest motion remains
in RAM unless it is the saved reference.

The single IMU owner runs at priority 2 on core 0, below the priority-3 ADC
owner. It shares an I2C mutex with M5 button/power operations and never owns the
ADC. `ORIENTATION_STATUS` reports readiness, bias/uncertainty, rest detection,
resets, update count, and worst fusion duration. Every gap over 35 ms resets
orientation while retaining learned gyro bias; captures overlapping gaps are
rejected. The filter settles for 1.5 seconds after startup/reset. There is no
per-launch hold-still requirement. Naturally occurring rest improves bias.
Clipping near 8 g / 2000 deg/s, missing coverage and optical bursts over 2.5
seconds also make motion unavailable. RPM/history still record independently.
Capture waits for fused-sample post-roll coverage, not the newer raw-poll
timestamp. Saving history waits for the motion post-roll; guarded flash writes can cause
IMU gaps outside the finished capture. Failed saves retain prior durable data.

This provides a bounded orientation estimate, not a calibrated motion-capture
system. Sustained linear acceleration can bias inclination; unreferenced yaw
can drift. Relative heading is reset for each short capture, not established
against north. Synthetic known-angle tests check the algorithm and timing,
and device readbacks check installation/performance. Real launch angle accuracy
and repeatability still require a physical reference-angle trial; no such
accuracy is claimed from software tests. No camera is required by this firmware.

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
clang++ -std=c++17 -O1 -g -DVQF_SINGLE_PRECISION -fsanitize=address,undefined firmware/tests/test_orientation_estimator.cpp firmware/LaunchLabMini/src/vqf/vqf.cpp -o /tmp/test-orientation
/tmp/test-orientation
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined firmware/tests/test_motion_replay.cpp -o /tmp/test-motion-replay
/tmp/test-motion-replay
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
`firmware/evidence/sticks3-0.4.2-feedback/`; the frozen start/end recap update is
in `firmware/evidence/sticks3-0.4.3-recap/`. Flash hash
verification proves installed bytes; USB status/stress checks prove acquisition
behavior. Repeated annotated live pulls establish detection reliability.
Independent known-speed shaft/tachometer testing is still needed for absolute
RPM accuracy. Battery-only sampling/power endurance also needs separate testing.

Official references:
- https://arxiv.org/abs/2203.17024
- https://vqf.readthedocs.io/en/stable/
- https://docs.m5stack.com/en/core/StickS3
- https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/adc_continuous.html
