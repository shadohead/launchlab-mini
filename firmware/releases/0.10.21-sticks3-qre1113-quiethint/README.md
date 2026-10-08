# Firmware 0.10.21 — Sensor profiles, new controls and display flip

For M5StickS3 K150 with an analog reflective sensor on GPIO1: SparkFun QRE1113 analog or a TCRT5000 module. Runs at 80 MHz with unchanged 50 kS/s optical sampling.

This release brings everything since 0.10.14 to the updater:

- **Sensor profile setting:** one firmware for both sensors. QRE / Standard keeps the 80-count mark floor; TCRT5000 uses 60 counts for its weaker marks. The choice is saved and applies at the next idle point.
- **New controls:** A opens or applies, B moves to the next choice, hold B goes back or cancels. Menus stay open while launches keep recording.
- **Display flip:** a saved 180-degree screen orientation. Brightness and flip preview immediately and revert on cancel. The live level, Start/End dots and 3D tilt recap follow the flipped screen.
- **Clearer setting editors:** each value is centred with a faint `B next option ->` hint beneath it.
- **Sleep:** 3-minute default, adjustable 1–10 minutes.

Launch detection, three-turn confirmation, fused tilt, history storage and shake wake keep their existing behaviour.

Build, 24 sanitizer-enabled native suites and seven production harnesses pass on this public source. The frozen application was installed with complete native readback verification; NVS, bootloader and partitions were preserved and all 128 history records matched. Actual device frames of the setting editors were checked, and the user reports the installed firmware working. A TCRT5000 setup recorded six of six physical pulls on the 60-count profile (0.10.17).

This is a prototype release. Long-session reliability, absolute RPM/angle calibration, battery endurance, physical browser transfer, first install/rollback of this revision and stock recovery remain separate checks. Older QRE and the old TCRT5000 builds remain preserved.

Production code and firmware bytes match the private frozen build. Public test harnesses use a synthetic playback fixture instead of private saved practice traces. The README is a public guide without private development or practice details. Device readbacks, backups and practice exports are excluded.
