"""Local print projects for a complete old-TCRT first build; no dispatch or printer connection."""
from pathlib import Path
import json,shutil
import slice_comparison_v05 as slicer
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v019_tcrt5000_open_stack';slicer.P=R/'inspection/print_v019_tcrt5000_open_stack';(slicer.P/'profiles').mkdir(parents=True,exist_ok=True)
for p in (R/'releases/LaunchLab_v017_open_stack/print_profiles').glob('*.json'):
 d=json.loads(p.read_text())
 if p.name.startswith('process'):d['name']=d['name'].replace('v017','v019_OLD_TCRT');d['print_settings_id']=d['name']
 (slicer.P/'profiles'/p.name).write_text(json.dumps(d,indent=2))
reports=[]
projects=[('ALL_PARTS',O/'LaunchLab_v019_ALL_PARTS_UNSLICED.3mf','process.json'),('REPLACEMENTS',O/'LaunchLab_v019_REPLACEMENTS_UNSLICED.3mf','process.json'),('CLIPS',O/'LaunchLab_v019_CLIPS_UNSLICED.3mf','process.json'),('PORT',O/'stl/01_TCRT_attachment_port.stl','process.json'),('SENSOR_CRADLE',O/'stl/03_TCRT_sensor_cradle.stl','process.json'),('M5_TOP_DOCK',O/'stl/04_TCRT_M5_top_dock.stl','process.json'),('SENSOR_FIT',O/'LaunchLab_v019_SENSOR_FIT_UNSLICED.3mf','process.json'),('M5_MOUNT_FIT',O/'extras/13_M5_MOUNT_FIT.stl','process_no_support.json')]
for name,source,profile in projects:
 rep=slicer.run('v019_OLD_TCRT_'+name,'PLA',source,profile);dest=O/'bambu'/f'LaunchLab_v019_P1S_PLA_{name}.3mf';shutil.copy2(rep['project'],dest);rep['release_project']=str(dest)
 log=Path(rep['project']).parent/'slice.log';rep['log_warnings']=[l.strip() for l in log.read_text().splitlines() if 'warning' in l.lower() or 'error' in l.lower()];reports.append(rep)
(O/'reports/slicing_metrics.json').write_text(json.dumps(reports,indent=2));shutil.copytree(slicer.P/'profiles',O/'print_profiles',dirs_exist_ok=True);shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
assert all(not r['log_warnings'] for r in reports),[(r['name'],r['log_warnings']) for r in reports]
print('ALL_OLD_TCRT_SLICES_PASS',flush=True)
