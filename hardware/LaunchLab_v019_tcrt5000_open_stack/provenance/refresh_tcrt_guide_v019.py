"""Update the embedded guide without changing or rerendering geometry."""
from pathlib import Path
import sys,json,bpy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'));from blender_helpers_v09 import audit
O=R/'releases/LaunchLab_v019_tcrt5000_open_stack';f=O/'LaunchLab_v019_tcrt5000_open_stack.blend';bpy.ops.wm.open_mainfile(filepath=str(f));t=bpy.data.texts['START HERE - OLD TCRT5000'];t.clear();t.write((O/'README.md').read_text());bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(f));bpy.ops.wm.open_mainfile(filepath=str(f));assert bpy.data.texts['START HERE - OLD TCRT5000'].as_string()==(O/'README.md').read_text()
a=json.loads((O/'reports/blender_mesh_audit.json').read_text());parts={}
for n,v in a.items():
 b=audit(bpy.data.scenes['01 OPEN STACK'].objects[n]);assert b['vertices']==v['vertices'] and b['triangles']==v['triangles'] and b['components']==1;parts[n]=b
(O/'reports/blender_saved_readback.json').write_text(json.dumps({'status':'PASS','parts':parts,'embedded_guide_matches_release_README':True},indent=2));print('GUIDE_UPDATED_GEOMETRY_READBACK_PASS',flush=True)
