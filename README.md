# LaunchLab Mini for Beyblade X

**A removable launch-practice meter for Beyblade X string launchers.** LaunchLab Mini uses an optical sensor to measure the launcher's shaft speed, then shows your peak RPM, launch history, and a replay of the device's tilt and rotation on an M5StickS3 screen. Use it to compare pulls, track consistency across practice sessions, and try to repeat a chosen launch.

Built around **M5StickS3 K150 + the small analog QRE1113 sensor**, with a six-piece printed attachment. The M5 keeps its factory case, display, controller and battery; you do not need a phone to view your results. The mount is designed to be removable. Check the supplied launcher interface and printed fit before using it on your launcher.

**[USB firmware updater](https://shadohead.github.io/launchlab-mini/) · [Firmware & print releases](https://github.com/shadohead/launchlab-mini/releases) · [Build & wiring](docs/BUILD.md)**

![LaunchLab Mini M5StickS3 mount, rendered from the published CAD](site/public/images/m5-mount.png)

Current firmware: **0.7.0**. Current print package: **v0.40**, six pieces on one P1S PLA plate. Firmware and hardware versions are tracked separately.

## What it does

| Feature | What you see or do |
| --- | --- |
| Optical peak RPM | See the fastest validated complete shaft revolution in an accepted pull. Three consistent turns confirm the pull before a peak is recorded. |
| Live level | Use the bubble and tilt angle while holding still to check the device's orientation before launching. |
| Launch recap | After a pull, see peak RPM, a short rotation replay, and frozen Start/End tilt circles. Press A to recall the latest recap. |
| Launch history | Review recent pulls and the current session's pull count, average, and best RPM. Retains up to 128 launches and 24 sessions on the device. |
| Pull and session trends | Compare individual pulls, a trailing five-pull average, and session averages to follow your practice consistency. |
| Motion & Recreate | Save a chosen pull as a reference, compare its relative rotation with a later pull, and inspect RPM, turn difference, rotation-speed traces and pull duration. |
| Battery and auto-off | Check approximate charge, voltage and charging status. Powers down after ten minutes without a measured pull, button use or interactive USB command. |
| Browser firmware updates | Install over USB in desktop Chrome or Edge. Updates write only the application after checking the partition layout. |

RPM is **launcher-shaft speed**, not a direct measurement of the Beyblade's release RPM or its spin in the stadium. Motion replay shows rotation and gravity-relative tilt; it does not measure travel distance or absolute compass heading. The live level references the screen plane until the mounting orientation is calibrated.

## Device UI

These are saved device-framebuffer screenshots, not concept UI. Screens marked **DEMO** use synthetic sample data. The live/recap images are from firmware 0.6.2, whose screen layout is retained in 0.7.0; history/trend images are from the 0.3.0 baseline and battery from 0.3.1. [Image provenance](docs/assets/ui/provenance.json) records their sources.

<table>
<tr><th>Live RPM & level</th><th>Launch recap</th><th>Launch history</th></tr>
<tr>
<td align="center"><img src="docs/assets/ui/live-rpm-level.png" width="200" alt="Idle live screen showing READY, RPM placeholder and bubble level"></td>
<td align="center"><img src="docs/assets/ui/launch-recap.png" width="200" alt="Demo launch recap showing 6500 RPM, a rotation replay and frozen start/end tilt circles"></td>
<td align="center"><img src="docs/assets/ui/launch-history.png" width="200" alt="Demo launch history listing pull RPM with session count, mean and best"></td>
</tr>
<tr><td>Ready state, held RPM result and level.</td><td>Recall the latest pull with A.</td><td>Browse pulls and session summaries.</td></tr>
</table>

<table>
<tr><th>Pull trend</th><th>Session trend</th><th>Battery</th></tr>
<tr>
<td align="center"><img src="docs/assets/ui/pull-trend.png" width="200" alt="Demo pull trend with individual measurements and a five-pull average"></td>
<td align="center"><img src="docs/assets/ui/session-trend.png" width="200" alt="Demo session trend plotting session-average RPM"></td>
<td align="center"><img src="docs/assets/ui/battery.png" width="200" alt="Battery page showing approximate charge, voltage, charging state and auto-off countdown"></td>
</tr>
<tr><td>See variation across recent pulls.</td><td>Compare averages across sessions.</td><td>Check power before practice.</td></tr>
</table>

From the live screen, **B opens history** and **A recalls the last recap**. In history, A cycles Recent → Pulls → Sessions → Battery → Motion → Recreate. Hold B to browse older history windows; hold A on the live/history pages to start a fresh session on the next accepted pull. Motion and Recreate have their own reference-selection controls; see the [firmware guide](firmware/LaunchLabMini/README.md).

## Exploded assemblies

The Beyblade X attachment has **two independent assemblies**: the M5 display mount and the QRE optical sensor attachment. The views below use the exact published CAD meshes, separated for illustration. They do not assert a measured combined mounting position on a complete launcher. Electronics and screws are reference envelopes, not printed parts.

### M5StickS3 display mount

![Exploded M5StickS3 assembly showing printed part 1, the intact M5StickS3 and underside screws](docs/assets/hardware/m5-exploded.png)

**1 — M5 platform:** supports the intact M5StickS3. Two M2×6 screws install from underneath into the device's existing mounts. The factory device, screen and soft-liner references are lifted for visibility in this view.

### Small QRE1113 sensor attachment

![Exploded QRE1113 assembly showing the sensor base, latch crossbar, pressure plate, both launcher latches, sensor and fasteners](docs/assets/hardware/qre-exploded.png)

| No. | Printed piece | Purpose | Fasteners |
| --- | --- | --- | --- |
| 2 | QRE sensor base | Locates the small analog board and retains the launcher-facing interface. | Receives the crossbar and pressure-plate screws. |
| 3 | Latch crossbar | Retains the launcher latch assembly. | 2 × M2×5 countersunk. |
| 4 | Sensor pressure plate | Holds the QRE board against its seat. | 2 × M2×4 pan-head. |
| 5 | Left launcher latch | One side of the removable launcher attachment. | Retained by the base/crossbar assembly. |
| 6 | Right launcher latch | Opposite side of the removable launcher attachment. | Retained by the base/crossbar assembly. |

### Each printed piece

All six pieces are included in the complete v0.40 plate. The views below show their actual mesh geometry; each build uses one of each.

<table>
<tr><th>1 · M5 platform</th><th>2 · QRE sensor base</th><th>3 · Latch crossbar</th></tr>
<tr>
<td><img src="docs/assets/hardware/part-01.png" width="240" alt="Individual M5StickS3 stepped mounting platform"></td>
<td><img src="docs/assets/hardware/part-02.png" width="240" alt="Individual QRE1113 sensor base"></td>
<td><img src="docs/assets/hardware/part-03.png" width="240" alt="Individual printed latch crossbar"></td>
</tr>
<tr><th>4 · Pressure plate</th><th>5 · Left launcher latch</th><th>6 · Right launcher latch</th></tr>
<tr>
<td><img src="docs/assets/hardware/part-04.png" width="240" alt="Individual QRE1113 sensor pressure plate"></td>
<td><img src="docs/assets/hardware/part-05.png" width="240" alt="Individual left launcher latch"></td>
<td><img src="docs/assets/hardware/part-06.png" width="240" alt="Individual right launcher latch"></td>
</tr>
</table>

If your five-piece sensor attachment is already built, only the **v0.40 M5 platform** needs replacement. [Download the combined 3MF](hardware/LaunchLab_v040_ALL_ITEMS_PRINT/bambu/LaunchLab_v040_P1S_PLA_ALL_ITEMS_ONE_PLATE.3mf) or the [full print package](hardware/LaunchLab_v040_ALL_ITEMS_PRINT_package.zip). Physical fit, button/thumb access and launch-load retention still need checking after printing. [Render provenance](docs/assets/hardware/provenance.json) identifies the source meshes; `scripts/render-readme-hardware.py` reproduces these illustrations in Blender.

## Get started

1. Download the [complete v0.40 print package](hardware/LaunchLab_v040_ALL_ITEMS_PRINT_package.zip) or open [the combined 3MF](hardware/LaunchLab_v040_ALL_ITEMS_PRINT/bambu/LaunchLab_v040_P1S_PLA_ALL_ITEMS_ONE_PLATE.3mf) in Bambu Studio.
2. Assemble with an intact M5StickS3 K150 and analog QRE1113. Read [BUILD.md](docs/BUILD.md) for wiring, fasteners and print settings.
3. Open the [updater](https://shadohead.github.io/launchlab-mini/) in desktop Chrome or Edge, choose Update or First install, enter download mode, and select the device.

Update writes only the application at `0x10000` after checking the installed partition table. First install replaces the factory firmware and partition table and requires an explicit checkbox. Neither flow erases all flash. Every downloaded image is SHA-256 checked and writes use esptool's device MD5 verification. Chip identity alone cannot distinguish every ESP32-S3 board, so confirm your device is specifically an M5StickS3 K150.

## Hardware files

- [v0.40 complete plate](hardware/LaunchLab_v040_ALL_ITEMS_PRINT/): all six prints, source STLs, QRE STEP files, profiles and digital verification.
- [v0.40 M5 mount](hardware/LaunchLab_v040_right_block_print/): editable Blender mesh and GLB, independent 3MF, dimensions and CAD reports.
- [v0.33 QRE base](hardware/LaunchLab_v033_flush_QRE/): editable Blender and STEP assembly for the current sensor seat. Other sensor parts are frozen in the complete package.

The CAD includes original launcher attachment geometry derived from Migbello's BP Gear Port Connector. Preserve its attribution and share-alike notice when distributing changes.

## Develop

Install Arduino CLI, then run `bash scripts/build-firmware.sh`. It installs the pinned ESP32 3.3.0, M5Unified 0.2.23 and M5GFX 0.2.30 dependencies into a project-local cache and compiles the 8 MB flash / OPI PSRAM target. Source builds may differ byte-for-byte from the archived binary across hosts/toolchains. The published binary is the exact saved release, with recorded checksum.

Run `bash scripts/test-firmware.sh` for 11 native C++ suites with address/undefined sanitizers. Website development requires Node 24+:

```sh
cd site
npm ci
npm test
npm run dev
npm run build
```

`python3 scripts/verify-artifacts.py` verifies published checksums and 3MF ZIP integrity. GitHub Actions runs the native tests, updater tests and artifact checks before deploying Pages from `main`.

Fifteen frozen M5 firmware versions are in [firmware/releases](firmware/releases/catalog.json), including the working 0.3.0 QRE baseline and the separate 0.2.0 old TCRT5000 variant. Only current QRE firmware is offered by the web updater. Historical source snapshots retain their original layouts and notes; use each release's source rather than mixing headers across versions. Device backups, personal practice exports and factory flash dumps are excluded.

## Validation scope

The current firmware passed native tests and 13 saved optical waveform replays, and was installed with a verified flash hash. A prior QRE baseline was reported to work well in live use. Fresh physical acceptance of the single-turn peak algorithm, independent absolute RPM calibration, and printed v0.40 fit/strength remain pending. Browser flashing is covered by mocked-loader tests and browser UI checks; a physical browser-flash trial is still required.

RPM measures launcher-shaft revolutions, not direct Beyblade release RPM. Tilt replay has no measured travel distance or compass heading. Digital CAD/slicing checks establish file consistency, not printed fit or safe launch-load retention.

Software: MIT with upstream component licenses. Hardware: preserved Creative Commons Attribution Share Alike notices. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
