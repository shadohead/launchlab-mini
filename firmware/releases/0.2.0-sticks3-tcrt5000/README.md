# M5StickS3 + old TCRT5000 sensor — saved working release

**Release: `0.2.0-sticks3-tcrt5000`.** This is the old TCRT5000/LM393
analog AO sensor version. The exact installed binary still reports runtime
version `0.2.0-sticks3-acquisition`; the sensor-specific release name labels
that verified binary without rebuilding or changing what was tested.

- Board: M5StickS3 K150, ESP32-S3, 8 MB flash / 8 MB OPI PSRAM.
- Sensor: old TCRT5000/LM393 analog module; AO → GPIO1, VCC → 3.3 V, GND → GND.
- Profile: 80-count minimum mark, 70% repeated-swing reversal hysteresis.
- Measurement: 50 kS/s, one cycle/revolution, 1,000-RPM start floor,
  three consistent revolutions, quiet/rewind rearm.
- Independent acquisition task; screen and USB stress test had zero sample loss.
- Initial live check: **three user-confirmed working pulls, three device
  launches, three saved-waveform replay results**. Latest live RPM: **6,406**.
  Absolute shaft RPM has not been independently calibrated.

The binary SHA256 is
`8f60898d0a4fd3e9e6cf16c741ada3ac50949d21f52ab84574b8c54e09a5dec6`.
`manifest.json` records target, sensor, profile, provenance and validation.
`source/LaunchLabMini/` is a self-contained saved Arduino sketch; `tests/`
contains the M5 native tests/replay tool. `evidence/` retains build/flash
receipts, performance logs and the checksum-verified three-pull raw capture.
`SHA256SUMS` covers all packaged files.

## Keep the new sensor separate

The **new sensor is the SparkFun QRE1113 analog breakout**. Its version is
planned separately. This release's pulse thresholds, waveform acceptance and
three-pull result apply to the old TCRT5000 setup. Do not replace or retune this
saved release while developing the QRE version. Give that version its own
sensor label, source/profile, binary and annotated live tests.

## Restore this exact build

For an M5 that already has the LaunchLab partition layout, from the repository
root with the connected port substituted as needed:

```sh
firmware/.venv/bin/python -m esptool --chip esp32s3 --port /dev/cu.usbmodem1101 \
  --baud 460800 --before default_reset --after hard_reset write_flash \
  0x10000 firmware/releases/0.2.0-sticks3-tcrt5000/LaunchLabMini.ino.bin
```

Only the application is written. Preserve settings/bootloader/partition layout.
For a factory board, follow initial setup and backup instructions in the main
`firmware/LaunchLabMini/README.md`; this application-only command is not initial
factory provisioning.

## Check the saved source and pull waveform

From the repository root:

```sh
clang++ -std=c++17 -O2 -Ifirmware/releases/0.2.0-sticks3-tcrt5000/source/LaunchLabMini \
  firmware/releases/0.2.0-sticks3-tcrt5000/tests/test_sticks3.cpp -o /tmp/test-sticks3-saved
/tmp/test-sticks3-saved
clang++ -std=c++17 -O2 -Ifirmware/releases/0.2.0-sticks3-tcrt5000/source/LaunchLabMini \
  firmware/releases/0.2.0-sticks3-tcrt5000/tests/replay_sticks3.cpp -o /tmp/replay-sticks3-saved
/tmp/replay-sticks3-saved firmware/releases/0.2.0-sticks3-tcrt5000/evidence/confirmed-three-pulls/export-01/samples.u16le
```

No device reflash was performed to create this saved release. The currently
installed old-sensor firmware remains the physically tested binary above.
