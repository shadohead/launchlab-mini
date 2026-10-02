# M5StickS3 + QRE1113 — battery page and automatic power-off

**Saved release: `0.3.1-sticks3-qre1113-power`.** Runtime version:
`0.3.1-sticks3-power`. Based on the user-confirmed
[QRE1113 practice firmware](../0.3.0-sticks3-qre1113/README.md).
The optical profile and portrait RPM/bubble UI remain the same.

Automatic power-off is enabled after **10 minutes without use**. Buttons,
active measured pulls and interactive USB commands reset the timer. Background
level/battery updates, optical noise and USB status polling do not reset it.
The ADC owner checks again before stopping, protecting active bursts and pulls
that complete at the timeout boundary. Pending practice data is saved before
shutdown. A failed save keeps the device awake and retries after one minute.
The native PM1 power-off path is used. Press the side Power/Reset button once
to turn on/reset again.

From live, **tap B, then tap A until Battery appears**. A cycles
recent launches → pull chart → session chart → battery. B returns to live.
The page shows estimated charge percentage, voltage, charging status and the
inactivity countdown. The percentage follows M5Unified's voltage-based estimate;
it does not claim measured hours remaining. Missing/stale battery reads show
"--". PM1 readings use I2C on the UI core every five seconds, avoiding the
optical ADC. Ordinary display updates remain frozen through measured bursts.

Wiring: QRE1113 analog VCC → 3V3_L2 / 3V3, GND → GND, OUT/AO → G1 / GPIO1.
The existing 80-count / 0.70 profile, 50 kS/s active sampling and 1,000-RPM start
floor are retained. The old TCRT5000 release remains separately preserved.

The application was flashed only at `0x10000` and its hash verified. All
28 prior launch records and four complete session summaries matched the
pre-update export exactly afterward. Native power/history/storage tests pass
with address/undefined-behavior sanitizers. Optical and level tests and all
13 saved M5 capture cases pass. The battery framebuffer was reviewed, and a
30-second, 20 Hz battery-page stress test with twelve 200 ms UI stalls had no
ADC/sample/event loss. `manifest.json` contains exact values and remaining
physical-validation gaps, including the full ten-minute idle shutdown trial.

`source/LaunchLabMini/` contains the exact compiled self-contained sketch;
`source/tests/` contains native tests, and `evidence/` contains installation,
battery, retention and runtime receipts. `SHA256SUMS` covers the packaged files.
The pre-update application/NVS backup is retained locally and excluded from Git.

For an existing LaunchLab M5 partition layout, restore only
`LaunchLabMini.ino.bin` at `0x10000`. Follow the
[current target instructions](../../LaunchLabMini/README.md) for dependency
setup, initial installation and detailed controls.
