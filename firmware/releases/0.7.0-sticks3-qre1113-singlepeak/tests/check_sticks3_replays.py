"""M5 profile regressions; waveform estimates are not absolute shaft RPM proof."""
import json
from pathlib import Path
import subprocess
import sys

evidence = Path(__file__).resolve().parents[1] / 'evidence'
exe = Path(sys.argv[1]).resolve()
cases = {
    'sticks3-old-sensor-20260930/confirmed-string-pull/samples.u16le': 1,
    # User confirmed three working pulls on installed M5 0.2.0; its counter
    # advanced from zero to three. Retained AO contains all three bursts.
    'sticks3-0.2.0/confirmed-three-pulls/export-01/samples.u16le': 3,
    'sticks3-old-sensor-20260930/reported-pull/samples.u16le': 0,
    # Startup captures contain persistent 60-Hz pickup. No new launch is valid.
    'sticks3-0.1.1/short-capture/export-01/samples.u16le': 0,
    # Cross-board negatives broaden the noise/handling check; they do not prove
    # the M5's mounted hardware is interchangeable with the older enclosure.
    'idle-phantom-0.5.5-20260926/export-01/samples.u16le': 0,
    'idle-phantom-0.5.5-20260926/export-02/samples.u16le': 0,
    'idle-phantom-0.5.5-20260926/export-03/samples.u16le': 0,
    'idle-phantom-0.5.5-20260926/export-04/samples.u16le': 0,
    'idle-phantom-0.5.4-20260923/export-01/samples.u16le': 0,
    'sensor-reseated-20260923/idle-no-ui/samples.u16le': 0,
    'rpm-firmware-0.2.3/idle-60s.u16le': 0,
    'idle-phantom-0.5.5-20260926/export-05/samples.u16le': 2,
    'rpm-firmware-0.6.0/verification/export-01/samples.u16le': 3,
}
report = {}
for name, count in cases.items():
    rows = [json.loads(line) for line in subprocess.check_output([str(exe), str(evidence/name)], text=True).splitlines()]
    assert rows[-1]['launches'] == count, (name, rows)
    if 'confirmed-string-pull' in name:
        valid = [row for row in rows if row.get('valid')]
        assert len(valid) == 1 and 4900 < valid[0]['three_turn_rpm'] < 5000
        assert valid[0]['rpm'] >= valid[0]['three_turn_rpm'] and valid[0]['rpm'] <= 30000
        assert 40.5 < valid[0]['time_s'] < 41.0 and valid[0]['amplitude'] >= 80
    report[name] = rows
print(json.dumps(report, indent=2))
