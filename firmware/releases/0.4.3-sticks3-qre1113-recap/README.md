# M5StickS3 + QRE1113 frozen launch recap

Runtime `0.4.3-sticks3-recap`. App-only update at `0x10000`.
The recap shows RPM, the existing turn path and two circle/dot indicators:
**Start on the left, End on the right**. The dots use recorded tilt at optical
burst onset and end, and stay fixed as the device moves after the pull.
Numeric angles, path scale and end roll/pitch/yaw text are removed.

Start/end tilt is estimated from a pre-launch acceleration baseline and full-rate
gyro integration before chart reduction. It is a rough pose estimate; travel
height and distance are not estimated. No hold-still requirement is added.
After five seconds, the screen returns to live; A recalls the latest pull or
returns to live immediately. The live main-page level stays available.

The reference format advances to schema 3 in the same 1124-byte slots, preserving
both snapshots. Existing schemas 1 and 2 remain readable, reconstructing tilt
from their stored trace. The latest trace remains in RAM unless saved as the
Recreate reference. History, Recreate, battery, 10-minute inactivity shutdown,
portrait orientation, and the 80-count / 0.70 optical profile are retained.

The application hash was verified during flashing. All 42 prior launches and
8 session summaries matched exactly after installation. Subsequent handling
recorded new launches; a real accepted moving-start trace and its framebuffer
were checked. The user confirmed the recap dots stay fixed. This does not
establish absolute tilt/RPM calibration or an annotated misses/duplicates rate.
Four sanitizer suites passed; 16 device scratch reference saves/reopens passed.
The labeled `q` preview is RAM-only and cannot change real history/reference.

`manifest.json` records exact bytes and validation scope. `source/` contains
matching source and tests; `evidence/` contains build, flash, retention, UI and
runtime checks. Flash/NVS backup bytes stay private locally. Previous QRE and
old TCRT5000 releases are preserved separately.
