# LaunchLab Mini for M5StickS3

**Optical profile: the existing 80-count / 0.70 TCRT5000 settings.** The original
three-pull release is preserved as
[0.2.0-sticks3-tcrt5000](../releases/0.2.0-sticks3-tcrt5000/README.md).
This update puts RPM and the level in portrait without retuning optical detection. QRE1113
also produced accepted bursts with that profile, but its annotated pull-count
acceptance and a separate tuned QRE release remain open.

Version `0.2.3-sticks3-portrait`, for StickS3 K150 (ESP32-S3,
8 MB flash, 8 MB OPI PSRAM). Uses the installed Arduino ESP32 3.3.0,
M5Unified 0.2.23 and M5GFX 0.2.30 dependencies. This is a separate board
application; the Waveshare binary cannot be installed on the M5.

## Acquisition and performance

`acquisition.h` owns all ADC calls, detector state and recorder writes in one
priority-3 task on core 0. M5Unified, screen drawing, buttons, USB and
Preferences remain on Arduino core 1. The UI exchanges commands and immutable
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
  polled every 20 ms on the UI core, with 200-ms smoothing. Display changes are
  limited to 10 Hz and meaningful dot/angle changes. The dot is cyan within
  2 degrees and orange beyond; 30 degrees reaches the rim. The screen plane is
  the reference, not a calibrated launcher mounting plane or launch trajectory.
  Bubble directions follow the portrait screen orientation.
- Accelerations outside 0.75–1.25 g show "Hold still" with no bubble. Missing
  or stale (>250 ms) samples show "--". Acceleration within that interval can
  still affect tilt, so use level while holding still. Normal display updates
  remain frozen during accepted RPM bursts. IMU calls cannot block the
  independent ADC owner.
- A pauses/resumes measurement; B toggles signal diagnostics.
- Side Power/Reset: double-click off, single-click on/reset. Long press enters
  download mode; these are built-in hardware controls.
- USB `p`: status, detector profile and performance.
- `LEVEL_STATUS` reports IMU readiness/type, fresh sample count, rejected
  samples, angle, acceleration and worst poll duration.
- `a`: pause/resume; `d`: signal display.
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

## Build and validation

```sh
bash firmware/setup-m5.sh
bash firmware/build-m5.sh
clang++ -std=c++17 -O2 -Ifirmware/LaunchLabRpm firmware/tests/test_sticks3.cpp -o /tmp/test-sticks3
/tmp/test-sticks3
clang++ -std=c++17 -O2 firmware/tests/test_sticks3_level.cpp -o /tmp/test-sticks3-level
/tmp/test-sticks3-level
clang++ -std=c++17 -O2 -Ifirmware/LaunchLabRpm firmware/tests/replay_sticks3.cpp -o /tmp/replay-sticks3
python3 firmware/tests/check_sticks3_replays.py /tmp/replay-sticks3
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
and the portrait update in `firmware/evidence/sticks3-0.2.2-portrait/`. Flash hash
verification proves installed bytes; USB status/stress checks prove acquisition
behavior. Repeated annotated live pulls establish detection reliability.
Independent known-speed shaft/tachometer testing is still needed for absolute
RPM accuracy. Battery-only sampling/power endurance also needs separate testing.

Official references:
- https://docs.m5stack.com/en/core/StickS3
- https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/adc_continuous.html
