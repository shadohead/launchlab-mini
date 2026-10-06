# Build a LaunchLab Mini — small QRE1113 sensor

[Parts list, quantities and purchase links](../README.md#parts-list--build-your-own) are at the top of the README.

Use M5StickS3 **K150**, which has ESP32-S3, 8 MB flash, integrated display and battery. M5StickC/C Plus/C Plus2 use different hardware and are not supported by these images. The small sensor is the **analog QRE1113 breakout**; a digital-output board is not interchangeable.

For the **old TCRT5000 / LM393 module**, use [TCRT5000.md](TCRT5000.md). [Hardware versions](HARDWARE_VERSIONS.md) covers the preferred independent M5 v0.68 carrier and its unverified seating/fastener engagement. The original v0.40 plate below retains its earlier carrier.

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

## Preferred M5 carrier and cable routing

The [v0.68 separate M5 carrier](../hardware/M5_cable_hook_v068/README.md) replaces
the original M5 platform; reuse your sensor attachment. Print its supplied single
carrier [P1S PLA project](../hardware/M5_cable_hook_v068/bambu/LaunchLab_v068_P1S_PLA_M5_ATTACHMENT_PROTOTYPE.3mf)
with the wire groove open upward and its WIRE GROOVE SUPPORT BLOCKER retained.
The saved slice is 43m33s / 8.38 g. Re-slice for your own printer and filament.

With M5 removed, lay the three leads into the 34 × 3 mm side-open groove, keeping
DuPont housings outside its ends. The shortened 6 mm underside hook accepts three
nominal 1.3 mm leads in a staggered arrangement, loaded separately. Keep the plugs
outside the hook. Choose cable length after a dry fit with relaxed bends.

Check seating on the two support humps and actual screw engagement before
remounting M5. M2×6 is a nominal reference; the retained pad geometry overlaps the
older nominal M5 underside, so do not force seating or tighten against rocking.
Printed hook strength, wire retention and launcher clearance remain unverified.

## Firmware and controls

Use the [USB updater](https://shadohead.github.io/launchlab-mini/) in desktop Chrome or Edge. A USB data cable is required. Connect USB, then hold the side Power/Reset button until the internal green LED flashes. Close serial monitors, then connect through the page. Firmware installation begins only after clicking Connect & update/install and choosing a device. See [update instructions](UPDATER.md) for current firmware release gates; this prototype has the limits recorded below.

Update checks for the expected partition table and writes only `0x10000`. First install replaces bootloader `0x0`, partitions `0x8000`, OTA selection `0xe000`, and application `0x10000`, without erase-all. Back up factory firmware before first install if you need to restore it. A full 8 MB backup contains personal settings/data and should stay private.

Short A recalls the latest recap. Short B opens history. In history, A cycles Recent/Pulls/Sessions/Battery/Settings and B returns to main. Hold A for one second to start a new session on the next accepted pull, except in Settings; see [the firmware guide](../firmware/LaunchLabMini/README.md). Automatic power-off uses a 3-minute default with saved 1–10 minute choices; measured pulls, buttons and interactive USB commands refresh it. A detected USB computer keeps it awake, including with no serial reader. Battery shake-wake at 80 MHz remains unverified.

Current 0.10.11 and the preserved 0.10.7/0.10.1 default to the peak of three-consecutive-turn elapsed-time
averages. Settings offers a persistent 1-turn peak alternative. On Settings,
hold B selects Sleep/RPM/Brightness; hold A changes/saves the selected row. Changing the
metric starts the next accepted pull in a new session. The default sleep is
3 minutes; saved 1–10 minute choices remain. Hold A on main toggles tournament;
B cycles Recording Only/RPM. Auto-sleep restores the selected mode/view.

A fresh K150 needs **First install**, which writes bootloader, partition table,
boot_app0 and application. Update writes the application only and requires a
matching partition table. Both paths verify downloads and device MD5 without
an erase-all. First install replaces the factory app/layout; back up first.

## Troubleshooting

If no USB port appears, try a known data cable, re-enter download mode, and close apps using the serial port. A partition or boot-selection mismatch means stop and back up; do not use First install to bypass it. After an interrupted app-only update, deliberately select Repair / rollback for the intended version. An interrupted First install may also need boot/layout recovery. Follow the [recovery and stock reinstall guide](RECOVERY.md) for the correct route. A successful message requires device MD5 verification. Press Power/Reset if verified firmware does not restart automatically.

## Current qualification

**0.10.11** is the installed, user-checked prototype revision: the app hash/NVS preservation, normal pulls and visible replays were checked. It includes recap/storage repairs and computer USB keep-awake, with an 80 MHz default and 240 MHz startup fallback. Battery endurance/current comparison, absolute RPM/angle calibration, a battery shake-wake cycle at 80 MHz, physical browser first install/rollback and stock recovery remain unverified. Post-pull flash writes still cause rejected IMU gaps. These results do not establish buyer/pilot qualification.
