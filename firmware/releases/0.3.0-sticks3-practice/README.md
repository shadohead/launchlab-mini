# M5StickS3 0.3.0 — launch practice history

Adds persistent launch records, session averages and charts to the portrait UI.
The practice metric is accepted peak RPM. Records start with new launches after
this update; older readings are not reconstructed.

- **Tap B:** live ↔ history.
- **Tap A in history:** recent launches → pull trend → session trend.
- **Hold B for 1 second in history:** browse older windows.
- **Hold A for 1 second:** start a new session on the next accepted pull.
- **Tap A on live:** pause/resume. **Hold B on live:** signal diagnostics.

Sessions also separate after 10 minutes without an accepted launch and after a
power cycle. Retains the latest 128 launches and 24 session summaries. A
session's average and best cover all its accepted launches, including records
that have left the individual-launch ring.

Pull trend shows 30 readings per window and a trailing five-pull average.
Session trend shows 12 session means per window. Change compares the first/last
five pulls or first/last two session means, with nonoverlapping groups. Axes
represent practice order, not calendar dates or equal elapsed intervals.

Two versioned, checksummed snapshots are saved in a separate NVS namespace and
read back before being marked saved. Storage errors appear on history and USB.
Flash writes briefly pause sampling only after a completed pull during rearm
or while measurement is paused. The finished RPM is retained; fresh quiet is
required before rearming. Active measured bursts cannot be checkpointed.
After that acquisition gap, the raw recorder exports its newest contiguous
segment. A power cut during saving may lose the newest unsaved result.

The 80-count / 0.70 optical profile, 50 kS/s active acquisition, GPIO1, launch
floor and level calculations are unchanged. All earlier sensor/UI releases
remain preserved. See `manifest.json` for exact hashes and validation scope.
The previous application and settings were backed up locally before updating.

Validation includes native tests with address/undefined-behavior sanitizers,
the M5 optical tests and 13 saved capture regressions, actual framebuffer review
of all pages, 36 isolated flash save/reopen cycles, and a 30-second chart-load
test with twelve 200 ms UI stalls. A stack overflow found in the early storage
stress check was fixed by moving large validation temporaries to heap storage;
the corrected on-device check passed with over 3 KiB UI stack headroom.
Demo records stayed separate from real practice data and were turned off.
Fresh annotated pulls and a battery power-cycle retention check remain distinct
from build, flash, storage-reopen and sampled-runtime evidence.

To restore on an existing LaunchLab M5, write `LaunchLabMini.ino.bin` only at
`0x10000`. Self-contained Arduino source is in `source/LaunchLabMini/`; native
tests are in `source/tests/`. USB `u` exports retained launches and sessions.
