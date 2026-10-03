"""Actual sensor-only CAD in Blender; separate M5 carrier is intentionally excluded."""
from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'inspection/minimal_TCRT_split_keepers_v043';sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='label':exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());E={e['name']:e for e in M['parts']};assert not any('M5' in n for n in E)
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='01 TCRT SENSOR ONLY';co=collection(s,'Actual sensor mount');obs={}
for e in M['parts']:
 ob=import_mesh(O/e['filename'],s,e['name'],co,e);obs[e['name']]=ob;ob['geometry_revision']='v043 sensor-only launcher mount'
 if e['group']=='clearance':ob.hide_render=True

def setup(sc,d,target,scale):
 cam=configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
 sc.render.resolution_x=1500;sc.render.resolution_y=1100;sc.cycles.samples=20
 sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.073,.095,1)
 sc['electronics']='OLD TCRT5000 31x13x1 PCB; M5 remains on its separate existing carrier'
 sc['battery_allowance']='No battery or M5 electronics within this sensor mount'
 sc['architecture']='Two independent screw-on clip caps; original latches, cleaned QRE narrow lower plate and unchanged TCRT PCB keeper'
 sc['status']='CAD prototype: physical fit, contact lands and optics unverified'
 return cam
setup(s,(1,-1.4,1.3), (0,0,.010),.073)
label(s,'TCRT5000 / your marked changes applied',-.032,.023,.0022)
label(s,'Separate screw-on clip caps / clean lower plate',-.032,-.024,.00195)

def clone(name,shift,omit):
 sc=bpy.data.scenes.new(name);c=collection(sc,'Actual CAD copies')
 for n,ob in obs.items():
  if n in omit or E[n]['group']=='clearance':continue
  a=ob.copy();c.objects.link(a);a.location+=Vector(shift(n))
 return sc
bare=clone('02 CRADLE AND SENSOR',lambda n:(0,0,0),['03_TCRT_sensor_pressure_keeper','REF_M2x4_SENSOR_1','REF_M2x4_SENSOR_2'])
setup(bare,(1,-1.3,1.8),(0,0,.010),.073)
label(bare,'Same TCRT seat / flat gray plate / round cap holes',-.032,.023,.0019)
label(bare,'M5 stays on its existing separate attachment',-.032,-.024,.0019)
ex=clone('03 SENSOR EXPLODED',lambda n:(0,0,.024 if n.startswith('REF_M2x4_SENSOR') else .011 if n.startswith('REF_M2x5_CLIP') else .019 if n=='03_TCRT_sensor_pressure_keeper' else .005 if n.startswith('02_TCRT_clip_cap') else .009 if n.startswith('REF_TCRT') else 0),[])
setup(ex,(1,-1.4,.9),(0,0,.019),.095)
label(ex,'U crossbar removed / two independent screw-on caps',-.041,.029,.0021)
label(ex,'QRE narrow lower plate / gray recesses smoothed',-.041,-.030,.0022)
under=clone('04 OPTICS UNDERSIDE',lambda n:(0,0,0),[])
setup(under,(1,-1,-1.2),(0,0,.009),.073)
label(under,'Downward optical head / original clip interface',-.032,.023,.0019)
checks={n:audit(ob) for n,ob in obs.items() if E[n]['printable']}
for n,a in checks.items():assert a['components']==1 and a['nonmanifold_edges']==a['inconsistent_winding_edges']==0,(n,a)
(O/'reports/blender_audit.json').write_text(json.dumps(checks,indent=2))
bpy.context.window.scene=s;bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL';sp.region_3d.view_location=(0,0,.010);sp.region_3d.view_distance=.105;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
bpy.data.texts.new('README - sensor-only corrected scope').write((O/'README.md').read_text())
path=O/'TCRT_split_keepers_v043.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
back={}
for n,a in checks.items():
 b=audit(bpy.data.scenes['01 TCRT SENSOR ONLY'].objects[n]);assert a['vertices']==b['vertices'] and b['nonmanifold_edges']==0;back[n]=b
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',parts=back),indent=2))
for name,stem in [('01 TCRT SENSOR ONLY','01_assembled'),('02 CRADLE AND SENSOR','02_sensor_cradle'),('03 SENSOR EXPLODED','03_exploded'),('04 OPTICS UNDERSIDE','04_underside')]:
 sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',path,flush=True)
