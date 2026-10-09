# Firmware 0.10.22 - Pulls right after a save are measured

For M5StickS3 K150 with an analog reflective sensor on GPIO1: SparkFun QRE1113 analog or a TCRT5000 module.

Fixes missed pulls.
About ten seconds after a pull, the device saves your history.
In 0.10.21 the detector then needed another second before it was ready, and a pull started in that window was not measured.
Pulling roughly every ten seconds could lose every other pull.
0.10.22 stays ready through the save, and the power log, Settings Apply and auto-off no longer pause measurement while a pull is starting.

Everything else is the same as 0.10.21: one firmware for both sensors (Settings -> Sensor profile), A opens or applies, B advances, hold B goes back, saved display flip, and your settings and history are kept.

Build, 24 sanitizer-enabled native suites and seven production harnesses pass.
Replaying recorded pulls with a save placed at every 0.1 s, 0.10.21 lost a pull at 61 placements and 0.10.22 at 6 (saves inside the flash write itself), with no phantom launches.

This is a prototype release.
Long-session reliability, absolute RPM/angle calibration and battery endurance remain separate checks.
