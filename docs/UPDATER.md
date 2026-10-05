# Update, repair and rollback

The recommended QRE release is **0.10.7**, runtime `0.10.7-sticks3-navigation`. The previous **0.10.1** remains selectable. These files target M5StickS3 K150 with the analog QRE1113; TCRT5000 uses its separate saved firmware.

1. Save important history/settings and a private full-device backup before flashing. There is no automatic browser backup. Do not upload a full flash dump to an issue.
2. Open the USB updater in desktop Chrome or Edge with a data cable. Read the selected target version and confirm K150.
3. Choose **Update existing LaunchLab** for a normal application update. Enter download mode using the side Power/Reset button and close other serial apps.
4. Connect. The updater checks every downloaded file's SHA-256, the actual partition and boot-selection bytes, and the installed application identity plus complete device MD5.
5. An older target is blocked. An unknown or incomplete application is blocked. If the selected exact application is already installed, no flash is written.
6. After a verified write/no-op, restart automatically or use the side button when prompted. Check the runtime version, history/settings, references, READY state and an ordinary pull afterward.

## Repair or intentional rollback

Use **Repair / rollback** only after backup and a deliberate version choice. The checkbox names the selected target; changing the version or mode, or completing an attempt, clears consent. Repair can rewrite an interrupted application or intentionally install the previous 0.10.1. It writes **only the application at 0x10000**, retaining the data and boot areas; it cannot guarantee that older firmware understands newer data.

Both Update and Repair stop for a different partition layout or boot selection. This updater only supports its original app0 boot layout. It does not guess which slot an external OTA tool selected. Do not use First install merely to bypass these checks.

If USB disconnects during a write, success is not reported. Re-enter download mode and reconnect. Normal Update will stop if the application is incomplete; deliberately confirm Repair for the intended target. Each attempt releases its connection before retry. Keep USB connected through device verification. A device MD5 failure is an error, not success.

## First install

First install requires a separate explicit backup/factory-overwrite confirmation. It writes bootloader **0x0**, partitions **0x8000**, boot support **0xe000**, and application **0x10000**. No mode uses erase-all. It changes the layout and can make prior factory applications/data inaccessible even though these write ranges do not directly address the new NVS region.

## Verification scope

The frozen 735,456-byte 0.10.7 application matches SHA-256 `54fe847cc82ac11b8f50669c424498267e079dfe967020271763e24ba5c808d2` and the saved staged build. Existing saved evidence verifies its application-only flash, runtime and unchanged 20 KB NVS. Its three support images are byte-identical to the prior 0.10.1 native first-install/readback bundle.

Software tests cover target selection, downgrade refusal, same-version no-op, corrupted images, interrupted/repeated attempts, explicit repair, partition/boot mismatches, device verification failure and cleanup. **Physical browser transfer, four-image 0.10.7 first install and physical rollback remain unverified.** Successful byte checks do not calibrate launcher RPM, tilt, battery charge or mechanical fit.

0.10.1/0.10.7 practice and motion storage code is unchanged in the static comparison. This is compatibility evidence, not a tested rollback guarantee. Older 0.10.1 lacks the newer Brightness row, power report and page hints. Preserve your backup until the intended release passes a real check.
