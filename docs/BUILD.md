# Build a LaunchLab Mini

Use M5StickS3 **K150**, which has ESP32-S3, 8 MB flash, integrated display and battery. M5StickC/C Plus/C Plus2 use different hardware and are not supported by these images. The small sensor is the **analog QRE1113 breakout**; a digital-output board is not interchangeable.

## Parts and wiring

- One intact M5StickS3 K150 and one analog QRE1113 breakout.
- Three short signal/power wires, sized for your board/header. Confirm the physical connector pin labels before attaching power.
- Six printed parts from the v0.40 plate.
- Two M2×6 screws for the M5 platform, inserted from underneath.
- Two M2×5 countersunk screws for the latch crossbar.
- Two M2×4 pan-head screws for the sensor pressure plate.

| Sensor | M5StickS3 Hat |
| --- | --- |
| OUT / analog AO | G1 / GPIO1 |
| VCC | 3V3 / 3V3_L2 |
| GND | GND |

Do not use GPIO0 for analog sampling. Do not use Grove red as a 3.3 V supply; it supplies 5 V. The firmware defaults to GPIO1 and does not automatically change the sensor supply or pin selection. Confirm your breakout's actual pin order and keep its output within 3.3 V logic limits.

## Printing and assembly

Open `hardware/LaunchLab_v040_ALL_ITEMS_PRINT/bambu/LaunchLab_v040_P1S_PLA_ALL_ITEMS_ONE_PLATE.3mf`. It contains the v0.40 M5 platform, v0.33 QRE base, v0.32 thicker crossbar, centered pressure plate, and both launcher latches. If upgrading an existing sensor attachment, only the M5 platform needs replacement.

The saved profile targets a P1S, PLA, 0.4 mm nozzle, 0.2 mm layers, Arachne walls, and 5 mm outer brims. Tree Slim support is enabled except on the upright pressure plate. Re-slice and review the plate for your own printer and filament. The original profile's AMS filament assignment is local metadata; select your own loaded filament. Estimate: 1h 15m 59s, 18.04 g.

Use the included exploded CAD/assembly references and per-part STLs. Keep the attachment removable, preserve the factory M5 enclosure, and inspect cable strain relief, sensor alignment, button/USB access and screw engagement before use. Check the printed launcher retention by hand before any pull. Digital checks do not establish physical fit or launch-load strength.

## Firmware and controls

Use the [USB updater](https://shadohead.github.io/launchlab-mini/) in desktop Chrome or Edge. A USB data cable is required. Hold the side Power/Reset button about two seconds to enter download mode, close serial monitors, then connect through the page. Firmware installation begins only after clicking Connect & update/install and choosing a device.

Update checks for the expected partition table and writes only `0x10000`. First install replaces bootloader `0x0`, partitions `0x8000`, OTA selection `0xe000`, and application `0x10000`, without erase-all. Back up factory firmware before first install if you need to restore it. A full 8 MB backup contains personal settings/data and should stay private.

Short A recalls the latest recap. Short B opens history. In history, A cycles views. Hold A for one second to start a new session on the next accepted pull. Motion/Recreate pages have reference selection controls described in [the firmware guide](../firmware/LaunchLabMini/README.md). Automatic power-off occurs after ten minutes without a measured pull, button use or interactive USB command.

When moving from older three-turn peak firmware to 0.7.0, hold A on the live page to start a fresh session; previous records retain their original metric. Single-turn timing is more sensitive to optical jitter and needs physical calibration.

## Troubleshooting

If no USB port appears, try a known data cable, re-enter download mode, and close apps using the serial port. If an update reports a partition mismatch, do not bypass the check: back up the device and use First install. If flashing fails, remain in download mode and retry the same install mode. A successful message requires the flasher's device MD5 verification. Press Power/Reset if the verified firmware does not restart automatically.
