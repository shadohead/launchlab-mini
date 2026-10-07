# Firmware 0.10.14 — Prompt tilt recaps and focused screens

For M5StickS3 K150 with analog QRE1113 on GPIO1. Runs at 80 MHz with unchanged 50 kS/s optical sampling and the existing launch/RPM rules.

Consecutive practice pulls defer automatic checkpoints until ten quiet seconds and the recap has finished. Tilt capture accepts a shorter valid pre-roll and uses 150 ms post-roll. Actual pull gaps, clipping and unsettled poses remain rejected. Startup verifies fresh paired IMU data, retries failed startup and can start a missing owner again while idle. Normal pulling does not require holding still first.

Main, recap, history and Settings hide routine saving/status captions. Main keeps its title, recap says Last launch and history navigation remains visible. The level, tilt replay, RPM choices, two tournament views, brightness, three-minute default sleep and shake wake remain available.

Build, 20 native suites and six production harnesses cover acquisition, VQF, startup failure/retry, timing, storage, UI and USB behavior. Complete native application readback and pre-boot NVS retention passed. Three consecutive QRE1113 pulls each produced valid tilt, with first recap presentation 202–216 ms after the detected pull end; the user confirmed prompt playback.

This is a prototype release. The MusRock board's advertised digital output is not qualified by the earlier QRE trial, and this build does not add capacitor-timing acquisition. Battery savings, long-session reliability, absolute RPM/angle calibration, physical browser transfer, four-image first install/rollback and stock recovery remain separate checks. Older QRE and the old TCRT5000 builds remain preserved.

Production code and firmware bytes match the private frozen build. Public test harnesses use a synthetic playback fixture in place of the private saved practice trace. Its README was replaced by this public guide to omit private development/practice details. Device readbacks, backups and practice exports are excluded.
