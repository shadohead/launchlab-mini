# LaunchLab Mini

An open source launcher-shaft RPM meter for **M5StickS3 K150 + analog QRE1113**. Print a removable launcher attachment, connect three sensor wires, and review optical peak RPM, practice history, and measured tilt replays on the built-in screen.

**[USB firmware updater](https://shadohead.github.io/launchlab-mini/) · [Releases](https://github.com/shadohead/launchlab-mini/releases) · [Build & wiring](docs/BUILD.md)**

![M5 mount CAD preview](site/public/images/m5-mount.png)

Current firmware: **0.7.0**, single-turn peak after three-turn pull confirmation. Current print package: **v0.40**, six parts on one P1S PLA plate. These version numbers track firmware and CAD separately.

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
