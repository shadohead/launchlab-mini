# Update, repair and rollback

The latest QRE release is **0.10.11**, runtime `0.10.11-sticks3-lowcpu`. Previous **0.10.7** and **0.10.1** remain selectable. These files target M5StickS3 K150 with analog QRE1113; TCRT5000 uses its separate saved firmware. **0.10.11** is the installed, user-checked prototype revision: the app hash/NVS preservation, normal pulls and visible replays were checked. It includes recap/storage repairs and computer USB keep-awake, with an 80 MHz default and 240 MHz startup fallback. Battery endurance/current comparison, absolute RPM/angle calibration, a battery shake-wake cycle at 80 MHz, physical browser first install/rollback and stock recovery remain unverified. Post-pull flash writes still cause rejected IMU gaps. These results do not establish buyer/pilot qualification. See [recovery guidance](RECOVERY.md).

1. Save important history/settings and a private full-device backup before flashing. There is no automatic browser backup. Do not upload a full flash dump to an issue.
2. Open the USB updater in desktop Chrome or Edge with a data cable. Read the selected target version and confirm K150.
3. Choose **Update existing LaunchLab** for a normal application update. Connect USB with the M5 powered on and close other serial apps. The updater attempts to enter download mode automatically. If connection fails, hold the side Power/Reset button with USB connected until the green LED flashes, release it, then retry and select the download-mode port.
4. Connect. The updater checks every downloaded file's SHA-256, the bundle's fixed partition map, the detected chip and 8 MB flash capacity, the actual device partition and boot-selection bytes, and the installed application identity plus complete device MD5. The device label remains necessary for K150 confirmation.
5. An older target is blocked. An unknown or incomplete application is blocked. If the selected exact application is already installed, no flash is written.
6. After a verified write/no-op, restart automatically or use the side button when prompted. Check the runtime version, history/settings, references, READY state and an ordinary pull afterward.

## Repair or intentional rollback

Use **Repair / rollback** only after backup and a deliberate version choice. The checkbox names the selected target; changing the version or mode, or completing an attempt, clears consent. Repair can rewrite an interrupted application or intentionally install the previous 0.10.1. It writes **only the application at 0x10000**, retaining the data and boot areas; it cannot guarantee that older firmware understands newer data.

Both Update and Repair stop for a different partition layout or boot selection. This updater only supports its original app0 boot layout. It does not guess which slot an external OTA tool selected. Do not use First install merely to bypass these checks.

If USB disconnects during an app-only write, success is not reported. Re-enter download mode and reconnect. Normal Update will stop if the application is incomplete; deliberately confirm Repair for the intended target. Each attempt releases its connection before retry. Keep USB connected through device verification. A device MD5 failure is an error, not success. For an interrupted First install or persistent layout/connection failure, follow the [recovery guide](RECOVERY.md).

## First install

First install requires a separate explicit backup/factory-overwrite confirmation. It writes bootloader **0x0**, partitions **0x8000**, boot support **0xe000**, and application **0x10000**. No mode uses erase-all. It changes the layout and can make prior factory applications/data inaccessible even though these write ranges do not directly address the new NVS region.

The partition-table image is limited to its 4 KB slot ending at `0x9000`; the gap before boot support contains NVS and is not a writable part of that slot. The downloaded map and its embedded MD5 must match the reviewed 8 MB layout. Detected capacity must be exactly 8 MB in every mode. Checksums and capacity checks cannot prove the board model or guarantee interruption recovery.

## Return to M5Stack software

Follow [Recovery and M5Stack software reinstall](RECOVERY.md) for the official M5Burner/StickS3 route, backup limits and failed-update steps. Vendor software reinstall does not restore original data/settings/calibration or identify the exact as-shipped demo. No vendor binary is hosted here; physical stock reinstall remains unverified.

## Verification scope

The frozen 729,264-byte application matches SHA-256 `4a49e2fc663efd89dca3ed527d1ba493c2cd5c39e03717fed2be263906751aaf`. Native app-only flash/hash, pre-boot NVS preservation, saved settings and subsequent launch storage were checked. User confirmed normal pulls and replays looked good. The three supporting install images are byte-identical to the prior 0.10.7/0.10.1 bundle.

Twenty native suites, five production harnesses and updater software tests cover acquisition, replay/storage scheduling, USB policy, target selection, downgrade refusal, same-version no-op, corrupted images, interrupted/repeated attempts, explicit repair, partition/boot mismatches, capacity refusal, verification failure and cleanup. **Physical browser transfer, four-image 0.10.11 first install and rollback remain unverified.** Byte checks do not calibrate launcher RPM, tilt, battery charge or mechanical fit. Battery savings and an 80 MHz battery shake-wake cycle remain unmeasured.

The browser connection now uses esptool-js's automatic reset selection, including native USB-Serial/JTAG reset, instead of requiring an already-running ROM bootloader. Native esptool and the deployed browser both successfully connected to the affected device, started the stub and detected ESP32-S3 with 8 MB flash. The browser's subsequent partition read timed out without writing flash. Preflight reads now request 256-byte packets with one unacknowledged packet at a time and consume/verify the trailing MD5 described in [Espressif's protocol](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/serial-protocol.html#reading-flash). Tests cover truncated/oversized packets, missing or corrupt digests, timeouts and consecutive reads. Physical acceptance of this read adjustment is pending. Software tests also require automatic reset before inspection/writes and release the port after failure.

The current storage schema identifiers remain unchanged, while save/validation behavior has changed since 0.10.7. This is static compatibility evidence, not a physical rollback guarantee. Older releases lack the current reliability repairs and CPU policy. Preserve your backup until the intended release passes a real check.
