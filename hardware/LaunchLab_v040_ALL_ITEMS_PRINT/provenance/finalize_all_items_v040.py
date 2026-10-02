"""Freeze and verify the complete v0.40 local print package."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[1]
O = R / 'releases/LaunchLab_v040_ALL_ITEMS_PRINT'
QRE = R / 'releases/LaunchLab_v033_flush_QRE'
M5 = R / 'releases/LaunchLab_v040_right_block_print'
assert not (O / 'SHA256SUMS.txt').exists(), 'Frozen package'
for filename in ['project_readback.json', 'actual_paths.json']:
    assert json.loads((O / 'reports' / filename).read_text())['status'] == 'PASS'
metrics = json.loads((O / 'reports/slicing_metrics.json').read_text())
assert metrics['plate_count'] == 1 and len(metrics['parts']) == 6
inventory = json.loads((O / 'print_inventory.json').read_text())
for name, item in inventory['parts'].items():
    source = R / 'releases' / item['source_release'] / item['source_file']
    data = (O / item['source_file']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    assert data == source.read_bytes()

(O / 'references').mkdir(exist_ok=True)
shutil.copy2(QRE / 'LICENSE.txt', O / 'LICENSE.txt')
shutil.copy2(QRE / 'references/QRE_BP_port_LICENSE.txt',
             O / 'references/QRE_BP_port_LICENSE.txt')
for filename in ['prepare_all_items_v040.py', 'check_all_items_paths_v040.py',
                 'finalize_all_items_v040.py', 'slice_comparison_v05.py',
                 'finalize_low_stack_v018.py']:
    shutil.copy2(R / 'scripts' / filename, O / 'provenance' / filename)
for filename in ['cad_validation.json', 'release_review.json']:
    shutil.copy2(M5 / 'reports' / filename, O / 'provenance' / ('M5_' + filename))
shutil.copy2(M5 / 'renders/01_topdown_before_after.png', O / 'reports/M5_before_after.png')
project = O / metrics['release_project']
with ZipFile(project) as z:
    assert z.testzip() is None
    (O / 'reports/plate_preview.png').write_bytes(z.read('Metadata/plate_1.png'))

(O / 'README.md').write_text(f'''# LaunchLab v0.40 complete print package

Open `bambu/LaunchLab_v040_P1S_PLA_ALL_ITEMS_ONE_PLATE.3mf` in Bambu Studio. It contains one plate with one of each of the six required printed parts:

- v0.33 QRE base, with the center step trimmed 0.5 mm per side and the center platform/sensor seat lowered 1 mm.
- v0.32 thicker latch crossbar.
- v0.32 centered sensor pressure plate, upright on its continuous flat edge.
- Left launcher latch.
- Right launcher latch.
- v0.40 separate M5 platform with the circled right block trimmed 3 mm left and its factory edge finish restored.

Only the M5 platform changes; reuse the five sensor parts if you already have them. The circled raised right block is shortened 3 mm toward the left in the top view with USB-C on the right. Its end changes from Y-18.5 to Y-15.5. The opposite edge's native 0.5 mm bevel, including its corner, is copied onto the new top edge. The lower launcher foot, curved receivers, M5 position, 2 mm deck, M2 mounting posts and other raised block are preserved. See `reports/M5_before_after.png` for a rendering of the actual meshes.

Settings: Bambu P1S, 0.4 mm nozzle, PLA, 0.2 mm layers, Arachne walls and 5 mm outer brims. Tree Slim supports are enabled globally, with supports explicitly disabled on the upright pressure plate. All six parts retain their manufacturing geometry and print orientations; auto-arrangement changes only their positions and rotation within the plate.

The slice estimates {metrics['estimated_time']} and {metrics['total_header_g']:.2f} g of PLA. Assign the project's single PLA filament to AMS filament 3 in the print dialog. This package has not been dispatched to the printer.

Nominal assembly hardware:

- 2 x M2x6 screws for the M5 platform, installed from underneath.
- 2 x M2x5 countersunk screws for the latch crossbar.
- 2 x M2x4 pan-head screws for the sensor pressure plate.

Individual STLs are included in `stl/`. Each matches its frozen source release byte-for-byte. The five QRE STEP files are included in `step/`; the M5 platform is supplied as a mesh. The saved 3MF is checked against all six source STLs, its G-code checksum and per-object settings are verified, and all models fit within one P1S plate. Actual model deposition is checked for every part, with no support deposition through the pressure plate's bounding box. Digital clearance checks pass; physical thumb reach, button operation and the trimmed mount's strength need checking after printing.

Source BP Gear Port and native grip: Migbello, Thingiverse 6856080, CC BY-SA (version unspecified). See `LICENSE.txt` and `references/QRE_BP_port_LICENSE.txt`.
''')

for source in [QRE, M5]:
    for line in (source / 'SHA256SUMS.txt').read_text().splitlines():
        digest, relative = line.split('  ', 1)
        assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == digest
files = sorted(p for p in O.rglob('*') if p.is_file())
hashes = {p.relative_to(O).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in files}
(O / 'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n'
                                         for name, digest in hashes.items()))
archive = R / 'releases/LaunchLab_v040_ALL_ITEMS_PRINT_package.zip'
with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
    for p in sorted(O.rglob('*')):
        if p.is_file():
            z.write(p, O.name + '/' + p.relative_to(O).as_posix())
with ZipFile(archive) as z:
    assert z.testzip() is None
    for name, digest in hashes.items():
        assert hashlib.sha256(z.read(O.name + '/' + name)).hexdigest() == digest
    assert z.read(O.name + '/SHA256SUMS.txt') == (O / 'SHA256SUMS.txt').read_bytes()
print('ALL_ITEMS_PACKAGE_VERIFIED', archive, archive.stat().st_size)
