# M5StickS3 + SparkFun QRE1113 analog — working release

**Release: `0.3.0-sticks3-qre1113`.** The user confirmed on 2026-10-01 that
this board and sensor combination "works pretty well". This package saves the
exact installed binary; it still reports runtime `0.3.0-sticks3-practice`.
No executable or detector settings changed when creating this sensor label.

- Board: M5StickS3 K150, ESP32-S3, 8 MB flash / 8 MB OPI PSRAM.
- Sensor: SparkFun QRE1113 **analog** breakout.
- Wiring: VCC → 3V3_L2 / 3V3, GND → GND, OUT/AO → G1 / GPIO1.
- Detection: 80-count minimum mark, 0.70 reversal hysteresis, 50 kS/s while
  acquiring, one cycle/revolution, 1,000-RPM start floor, three consistent
  revolutions and quiet/rewind rearm.
- Portrait display: USB-C down, RPM above the bubble, without a divider or
  the word "LEVEL".
- History: latest 128 launches, 24 session summaries, session average/best
  peak RPM, pull charts and session charts. Sessions separate on boot,
  after 10 minutes without an accepted pull, or with the manual gesture.

**Tap B** to toggle live/history. **Tap A in history** to cycle recent launches,
pull trend and session trend. **Hold B for one second in history** to browse
older windows. **Hold A for one second** to start a session on the next accepted
pull. On live, tap A pauses/resumes and hold B opens diagnostics. The side
Power/Reset button double-clicks off and single-clicks on/reset.

Charts use practice order rather than calendar dates. Pulls show a trailing
five-pull average; session charts show per-session means. An accepted reading
is peak RPM, not calibrated launch force. History uses alternating checksummed
NVS snapshots. Flash saving pauses sampling briefly during rearm or while
manually paused, retains the completed RPM and starts a new contiguous raw
recording segment. It cannot interrupt an active measured burst.

The binary SHA-256 is
`5871bedad295a1f309a397f2b5a0ceffe3606294702d1b6389089a000697d7da`.
`manifest.json` records the wiring, dependencies, validation and confirmation.
`source/LaunchLabMini/` contains the self-contained Arduino sketch;
`source/tests/` contains native tests. `evidence/` copies the existing build,
flash, runtime, storage and UI stress receipts. Charts in demo captures use
labeled synthetic data that never enters real practice history.
`SHA256SUMS` covers every packaged file except the checksum list itself.

The user confirmation establishes qualitative working use. It does not supply
an annotated exact pull count, an independent absolute-RPM calibration or a
battery power-cycle retention result. Those remain separate checks.

The original old TCRT5000/LM393 release is preserved unchanged as
[0.2.0-sticks3-tcrt5000](../0.2.0-sticks3-tcrt5000/README.md).
The earlier [practice-history archive](../0.3.0-sticks3-practice/README.md)
preserves the executable's original build and installation provenance.

## Restore the saved binary

For an M5 already using the LaunchLab partition layout, replace the example
port with the connected device's port and run from the repository root:

```sh
firmware/.venv/bin/python -m esptool --chip esp32s3 --port /dev/cu.usbmodem1101 \
  --baud 460800 --before default_reset --after hard_reset write_flash \
  0x10000 firmware/releases/0.3.0-sticks3-qre1113/LaunchLabMini.ino.bin
```

Preserve the existing device's settings before updating. For a factory board,
follow the [M5 setup instructions](../../LaunchLabMini/README.md).
Creating this package did not reflash the device.
