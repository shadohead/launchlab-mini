# Firmware 0.11.1 - Themes, personal-best effects and USB backup

For M5StickS3 K150 with an analog reflective sensor on GPIO1: SparkFun QRE1113 analog or a TCRT5000 module.

Fixes 0.11.0, which restarted about once a second after boot.
Its main loop overflowed its 8 KB stack: the new backup code had put about 5 KB of buffers into the loop's stack frame.
0.11.1 keeps those buffers off the stack and cuts the loop's frame from 6,864 to 800 bytes (0.10.22: 3,984).
Every build now fails if a frame exceeds its budget, and the `p` status reports the loop's lowest free stack.

Themes: Settings gains Theme (Classic, Mint, Amber, Violet), which tints the live readout, accents, level, recap, history and battery pages.
Classic keeps the existing look.

Personal-best effects: Settings gains Best effect (Orbit, Flames, Sparkles, Shockwave, Crown, Off).
A new personal best for the active sensor profile and RPM method plays the effect once on its recap.
Bests start from the first pull after updating; older history has no profile or method record and is not migrated.

USB backup and restore: the web updater can save your history, sessions, personal bests, theme, effect, last recap and settings to a file, and restore that file to this or another M5StickS3 running 0.11.1 or newer.
A restore is checked in full before anything is written, then the device restarts.

The detector, estimators, sampling, thresholds, wake policies and saved history format are unchanged from 0.10.22, and updating keeps your settings and history.

Build, stack budget check, 26 sanitizer-enabled native suites and seven production harnesses pass.

This is a prototype release.
Installed on the owner's M5StickS3 K150 (app-only): no restarts in a 120 s soak, history kept, a backup and restore round trip identical, and the screen, themes and pulls confirmed by the owner.
