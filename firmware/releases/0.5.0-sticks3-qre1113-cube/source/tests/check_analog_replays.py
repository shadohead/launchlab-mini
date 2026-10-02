"""Regression checks against saved physical captures; not absolute RPM proof."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
evidence = root / 'firmware/evidence'
exe = Path(sys.argv[1]).resolve()
# expected launch counts apply only to captures with known activity context.
cases = {
    'mounted-fast-rip-20260922-010625/samples.u16le': 1,
    'mounted-fast-repeat-20260922-011034/samples.u16le': 1,
    # Handling, then a slow hand rotation. Since 0.5.2 a chaotic handling burst
    # at 3.5 s can pass as three matching periods and its hold covers the
    # rotation; the old envelope threshold hid it. No pull labels exist here.
    'mounted-sensor-20260922-010221/samples.u16le': None,
    'missed-pull-20260922-153759/samples.u16le': None,
    'rpm-firmware-0.2.3/idle-60s.u16le': 0,
    'sensor-reseated-20260923/idle-no-ui/samples.u16le': 0,
    'rpm-firmware-0.3.5/physical-calibration/samples.u16le': 3,
    'rpm-firmware-0.3.5/settled-physical-calibration/samples.u16le': 3,
    'rpm-firmware-0.5.2/recorder-selftest/export-01/samples.u16le': 0,
    # Idle with display-transfer markers: one dip per transfer, all blanked.
    'rpm-firmware-0.5.3/flush-markers/export-01/samples.u16le': 0,
    'rpm-firmware-0.5.2/repro-session/export-01/samples.u16le': None,
    'rpm-firmware-0.5.2/controlled-session/export-01/samples.u16le': 6,
    # Idle, untouched and stationary (0.5.4 flight recorder). Slow AO wander
    # formed 138 and 91 RPM phantoms before the 1,000 RPM launch floor.
    'idle-phantom-0.5.4-20260923/export-01/samples.u16le': 0,
    # In the enclosure (0.6.0 flight recorder, 2026-09-26). Idle, then the
    # device picked up / handled: 1,940, 1,567 and 2,542 RPM phantoms from
    # 14-21 count edges. The 300-count mark floor removes all of them.
    'idle-phantom-0.5.5-20260926/export-01/samples.u16le': 0,
    'idle-phantom-0.5.5-20260926/export-02/samples.u16le': 0,
    'idle-phantom-0.5.5-20260926/export-03/samples.u16le': 0,
    'idle-phantom-0.5.5-20260926/export-04/samples.u16le': 0,
    # 45 s untouched, then pulls at 45.5 s and 56.0 s (third pull cut off by
    # the export). A 10-count 2,736 RPM phantom at 54.4 s between them.
    'idle-phantom-0.5.5-20260926/export-05/samples.u16le': 2,
    # 0.6.0 verification: ~20 s of handling (no pull), then three pulls. The
    # shaft rested at the 4095 rail for 8 s after pull 2; the old rail fault
    # cleared that result and swallowed pull 3, which began as it left the rail.
    'rpm-firmware-0.6.0/verification/export-01/samples.u16le': 3,
}
# Recordings from the earlier printed case, whose revolution marks were only
# 10-40 counts. No mark floor can separate those from phantoms, so they are
# replayed with the floor disabled to keep exercising the rest of the detector.
weak_optics = {
    'mounted-sensor-20260922-010221/samples.u16le',
    'missed-pull-20260922-153759/samples.u16le',
    'rpm-firmware-0.3.5/physical-calibration/samples.u16le',
    'rpm-firmware-0.3.5/settled-physical-calibration/samples.u16le',
    'rpm-firmware-0.5.2/repro-session/export-01/samples.u16le',
    'rpm-firmware-0.5.2/controlled-session/export-01/samples.u16le',
}
report = {}
for name, expected in cases.items():
    args = [str(exe), str(evidence/name)] + (['0'] if name in weak_optics else [])
    output = subprocess.check_output(args, text=True)
    rows = [json.loads(line) for line in output.splitlines()]
    report[name] = rows
    if expected is not None:
        assert rows[-1]['launches'] == expected, (name, rows)
    valid = [row for row in rows if row.get('valid')]
    times = [row['time_s'] for row in valid]
    if 'mounted-fast' in name:
        assert len(valid) == 1 and 7300 < valid[0]['rpm'] < 7650, (name, rows)
    if 'missed-pull' in name:
        assert any(3700 < row['rpm'] < 4300 for row in valid), (name, rows)
    if 'physical-calibration' in name:
        assert all(sum(a <= t < b for t in times) == 1
                   for a, b in [(4, 9), (9, 14), (14, 19)]), (name, rows)
    if 'export-05' in name and 'idle-phantom-0.5.5' in name:
        assert [round(row['rpm']) for row in valid] == [3830, 5607], (name, rows)
        assert all(row['amplitude'] > 900 for row in valid), (name, rows)
    if 'rpm-firmware-0.6.0/verification' in name:
        assert [round(row['rpm']) for row in valid] == [5941, 6040, 7500], (name, rows)
        assert not any(row.get('reason') == 'signal_fault' for row in rows), (name, rows)
    if 'repro-session' in name:
        # The user's "misses after two pulls": baseline jumps inflated the old
        # hysteresis. This clean ~3.4k RPM train at 52.5 s was one of them.
        assert any(52.5 < row['time_s'] < 53.0 and 3000 < row['rpm'] < 3900
                   for row in valid), (name, rows)
        assert len(valid) >= 8, (name, rows)
    if 'controlled-session' in name:
        # Labeled by the user: (1) pull, held 3 s, (2) slow pull, held 3 s,
        # (3)-(5) normal pulls. Rewind after a >1 s hold is a separate burst
        # that one optical channel cannot tell apart from a pull (23.9 s after
        # pull 1, 34.2 s after pull 2). The slow pull itself stays below the
        # 1,000 RPM launch floor. Before 0.5.5 a ~640 RPM phantom near 33.5 s
        # (display interference; this recording predates transfer markers)
        # took pull 2's slot and its hold swallowed the rewind.
        windows = [(19.5, 21), (23.5, 24.5), (33.7, 34.5), (37.5, 38.5),
                   (42, 43), (45.5, 47)]
        assert all(sum(a <= t < b for t in times) == 1 for a, b in windows), (name, rows)
print(json.dumps(report, indent=2))
