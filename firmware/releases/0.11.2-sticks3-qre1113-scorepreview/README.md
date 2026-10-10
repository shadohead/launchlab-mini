# Firmware 0.11.2 — High score effect preview

M5StickS3 K150, ESP32-S3, 8 MB flash, QRE1113 analog or TCRT5000 through the saved sensor profile.

Settings and its High score effect editor show a bounded preview using the existing native renderer. The Settings row uses the saved effect; B cycles the editor draft, A applies once, hold B cancels. The labeled 8120 RPM sample creates no measurement, history or personal best. Flames, Sparkles and Off retain a clear numeric result. Active optical capture, pending motion and USB restore pause the preview; real celebrations still require a captured valid new personal best and do not block the next pull.

Themes, sensor/calibration settings, RPM estimators, detector thresholds, sampling, history/best formats and power policies are unchanged. The 0.11.1 stack fix is retained.

Validation: 27 sanitizer-enabled native suites, seven exact production harnesses, ESP32-S3 target build and stack budgets passed. loop() is 816 bytes against a 1536-byte budget; every other sketch frame is at most 2560 bytes. Sixty public updater tests and its production build pass, including same-version build recognition and post-write MD5 failure. The three supporting installation images are byte-identical to 0.11.1. Updates and repair write only app0 at 0x10000 with eraseAll false after layout/boot-selection checks, preserving NVS, calibration, settings and history.

Device evidence: at 2026-10-10 03:14 UTC the owner said “it works, lets get this updated on gh and our site” after testing local candidate 39ce90a7fbc81aaa8d4f78e5f0a69a216b63e998 (runtime 0.11.1-sticks3-effectpreview-dev). Every compiled source file in this release equals that candidate except the runtime version string. The final 0.11.2 binary has not been installed again; Device install pending for that exact binary. This is not new physical flash, soak, accuracy, battery or rollback evidence.

The distinct candidate and released 0.11.1 identities are recognized by the updater. 0.11.1 remains preserved for deliberate recovery. Sensor labels QRE / Standard and TCRT5000 retain their existing wording; consumer Standard/Compact naming is a separate issue.
