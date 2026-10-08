# Hardware and sensor versions

LaunchLab Mini is a removable Beyblade X launcher-shaft RPM meter. **QRE1113** is the small analog sensor; **TCRT5000 / LM393** is the older, larger analog module. Their mounts and detector thresholds differ. The M5StickS3 carrier is a separate part with its own version history.

## Choose a sensor and firmware

| Sensor | Mount | Firmware | Status |
| --- | --- | --- | --- |
| Small analog QRE1113 | v0.33 sensor geometry / v0.40 complete six-piece plate | [0.10.21 firmware](../firmware/releases/0.10.21-sticks3-qre1113-quiethint/README.md), QRE / Standard profile | User-checked prototype: 80 MHz, latest-launch tilt recap, history, trends, battery and display flip; endurance and recovery unverified. |
| Old TCRT5000 / LM393 analog AO | Latest v0.43 separate sensor attachment; v0.19 historical integrated mount | [0.10.21 firmware](../firmware/releases/0.10.21-sticks3-qre1113-quiethint/README.md), TCRT5000 profile; frozen [0.2.0 TCRT firmware](https://github.com/shadohead/launchlab-mini/releases/tag/firmware-tcrt5000-v0.2.0) | 0.10.21 with the 60-count TCRT5000 profile is recommended; a TCRT5000 setup detected six of six pulls on that profile. 0.2.0 remains the earlier acquisition build. |

The web updater selects **0.10.21** for either sensor, with **0.10.14**, **0.10.11**, **0.10.7** and **0.10.1** retained for deliberate rollback. [Update and qualification details](UPDATER.md). Choose the Sensor profile in Settings after installing. The updater does not restore the old TCRT 0.2.0 build. Old firmware is an application-only restore at `0x10000` on an M5StickS3 already provisioned with the LaunchLab partition layout. Its exact binary retains runtime string `0.2.0-sticks3-acquisition`. See [TCRT wiring and restore guide](TCRT5000.md).

## Current downloads

- **Preferred separate M5 v0.68 carrier:** [assembly and source](../hardware/M5_cable_hook_v068/README.md), [complete package](../hardware/M5_cable_hook_v068_package.zip), [sliced P1S PLA 3MF](../hardware/M5_cable_hook_v068/bambu/LaunchLab_v068_P1S_PLA_M5_ATTACHMENT_PROTOTYPE.3mf), [carrier STL](../hardware/M5_cable_hook_v068/stl/01_M5_channel_two_humps_cable_hook.stl), [editable Blender model](../hardware/M5_cable_hook_v068/LaunchLab_v068_M5_underside_cable_hook.blend).

v0.68 is the project owner's preferred separate M5 carrier. It combines the
side-open wire channel, two older support humps and a downward-opening underside
hook shortened from 8 to 6 mm, retaining its 4.8 mm height. Its P1S PLA slice is
43m33s / 8.38 g. Three nominal 1.3 mm leads fit staggered in two rows and load
separately; connector housings stay outside. Physical seating, screw engagement,
hook strength, retention and launcher clearance remain unverified. The older
nominal M5 underside overlap is retained; dry-fit the actual device. This is a
single-carrier replacement, separate from the sensor mount and stacked layouts.

Earlier published options:

- [M5 v0.50 release](https://github.com/shadohead/launchlab-mini/releases/tag/hardware-m5-v0.50): [complete package](../hardware/M5_equal_supports_v050_package.zip), [sliced P1S PLA 3MF](../hardware/M5_equal_supports_v050/bambu/LaunchLab_v050_P1S_PLA_M5_EQUAL_SUPPORTS_TREE_SLIM.3mf), [unsliced project](../hardware/M5_equal_supports_v050/M5_equal_supports_v050_UNSLICED.3mf), [carrier STL](../hardware/M5_equal_supports_v050/stl/01_M5_equal_supports_platform.stl).
- [TCRT v0.43 release](https://github.com/shadohead/launchlab-mini/releases/tag/hardware-tcrt5000-v0.43): [six-piece package](../hardware/minimal_TCRT_split_keepers_v043_package.zip), [per-part STLs](../hardware/minimal_TCRT_split_keepers_v043/stl/), [full STEP assembly](../hardware/minimal_TCRT_split_keepers_v043/TCRT_split_keepers_v043.step). Unsliced CAD prototype; no saved 3MF exists for this revision.
- [QRE v0.40 complete plate](../hardware/LaunchLab_v040_ALL_ITEMS_PRINT/bambu/LaunchLab_v040_P1S_PLA_ALL_ITEMS_ONE_PLATE.3mf): existing six prints with the v0.40 M5 carrier. The v0.68 and v0.50 carriers are separate replacements, not included on that older plate.

**M5 v0.50 is a prototype:** its two supports rise from 0.5 to 2.3 mm to match the screw standoffs. The original nominal device reference has a stepped underside and overlaps these raised pads. Physical seating and leveling remain unverified. Its saved slice is 43m18s / 9.24 g PLA, Tree Slim supports; this is a slicing result, not proof of printing or fit. Re-slice for your printer and loaded filament. M2 screw length/insert engagement must be checked; the v0.45 counterbores changed the engagement of the earlier M2×6 reference. Do not infer a confirmed screw length from that reference.

**TCRT v0.43 is a prototype:** its PCB measurements are 31×13×1 mm, with provisional header/solder/head envelopes. Sensor alignment, solder clearance, screw preload and removable launcher retention require physical checks. The M5 mount remains separate. These newer mounts do not inherit the old firmware trial's physical validation.

## Revision history

Every row links to a frozen local snapshot with source files, manufacturing STLs, reference meshes, original README, attribution and digital reports. Whole M5 carriers are mesh geometry: their STEP files contain only the added pads, cutters or ramp named in that revision, not the entire carrier. TCRT v0.43 includes full per-part STEP files.

| Version | Family | Changes | Saved print state |
| --- | --- | --- | --- |
| [v0.19](../hardware/LaunchLab_v019_tcrt5000_open_stack/) | Old TCRT5000 | Historical open-stack integrated sensor/M5 mount. | Historical slice; physical fit unverified. |
| [v0.33](../hardware/LaunchLab_v033_flush_QRE/) | Small QRE1113 | Flush sensor base and preserved optical seat. | Included in v0.40 plate. |
| [v0.40](../hardware/LaunchLab_v040_ALL_ITEMS_PRINT/) | QRE + M5 | Complete six-piece plate with right-block M5 carrier. | Saved P1S PLA slice. |
| [v0.41](../hardware/minimal_TCRT_stack_v041/) | Old TCRT5000 | Minimal stacked cradle with removable sensor keeper/M5 dock. | Unsliced CAD prototype. |
| [v0.42](../hardware/minimal_TCRT_sensor_only_v042/) | Old TCRT5000 | Separate sensor-only attachment; M5 kept on its own carrier. | Unsliced CAD prototype. |
| [v0.43](../hardware/minimal_TCRT_split_keepers_v043/) | Old TCRT5000 | Independent left/right screw-on clip caps; smooth narrow lower plate. Six printed pieces. | Unsliced CAD prototype. |
| [v0.44](../hardware/M5_level_support_v044/) | M5 carrier | Opposite-end 0.5 mm supports for stepped device underside. | Unsliced STL. |
| [v0.45](../hardware/M5_recessed_screws_v045/) | M5 carrier | Underside screw-head counterbores, 4.2 mm diameter / 1.4 mm depth. | Unsliced 3MF/STL. |
| [v0.46](../hardware/M5_raised_rectangle_v046/) | M5 carrier | Center locating rectangle projection increased to 1.25 mm. | Unsliced 3MF/STL. |
| [v0.47](../hardware/M5_rotated_rectangle_v047/) | M5 carrier | Center rectangle rotated 90°, length extended. | Unsliced 3MF/STL. |
| [v0.48](../hardware/M5_smooth_rectangle_v048/) | M5 carrier | Sloped center rectangle with 0.3 mm rounded transitions. | Unsliced 3MF/STL. |
| [v0.49](../hardware/M5_soft_ramp_v049/) | M5 carrier | Broader center ramp with 0.8 mm fillets. | Unsliced 3MF/STL. |
| [v0.50](../hardware/M5_equal_supports_v050/) | M5 carrier | Opposite-end supports raised to 2.3 mm; v0.49 geometry retained. | Saved P1S PLA slice; seating unverified. |
| [v0.68](../hardware/M5_cable_hook_v068/) | M5 carrier | Preferred separate carrier: side-open channel, two older humps and 6 mm underside cable hook. | Saved P1S PLA slice; physical fit and strength unverified. |

[Machine-readable inventory and SHA-256 hashes](../hardware/versions.json) identify all newly published files. Older versions remain available; no published firmware binary or existing v0.40 geometry was replaced. One v0.42 render had a stale local checksum; its original checksum list is preserved under `provenance/`, and the publication list records the final saved render. All original CAD/STL/STEP hashes matched.

The [README exploded views](../README.md#exploded-assemblies) are rendered directly from these frozen STL meshes. Explosion distances and electronics/fastener references are illustrative. Digital CAD, archive and slicing checks do not establish printed fit, absolute RPM accuracy or launch-load retention.
