"""Actual Blender geometry: 0.5 mm side trims and 1 mm lower central assembly."""
from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v033_flush_QRE';S=R/'releases/LaunchLab_v032_balanced_QRE';sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,material
for n in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name=='label':exec(compile(ast.Module(body=[n],type_ignores=[]),'label','exec'))
assert json.loads((O/'reports/fit_and_motion.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='01 LOWER SENSOR ASSEMBLY';c=collection(s,'Delivered meshes');obs={}
for e in M['parts']:obs[e['name']]=import_mesh(O/e['filename'],s,e['name'],c,e)
def setup(sc,d,scale,target):
 configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
 sc.render.resolution_x=1400;sc.render.resolution_y=1050;sc.cycles.samples=16
 sc['status']='Digital prototype; installed fit and optical response need physical check'
 sc['electronics']='SparkFun analog QRE1113; board, sensor, plugs and clamp translated exactly minus 1 mm'
 sc['mount']='Launcher-facing center step narrower; side clips and hinges at unchanged poses'
 sc['architecture']='Print one new base, reuse centered pressure plate and crossbar'
 sc['battery_allowance']='Factory battery; separate unchanged v024 M5 platform'
 sc['registration']='No invented full launcher collision geometry or installed M5 pose'
 sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.073,.095,1)
 if d[2]<0:
  for a in sc.objects:
   if a.type=='LIGHT':a.location.z=-abs(a.location.z);a.rotation_euler=(Vector(target)-a.location).to_track_quat('-Z','Y').to_euler()
def clone(name,omit=()):
 sc=bpy.data.scenes.new(name);co=collection(sc,'Exact delivered mesh copies')
 for n,a in obs.items():
  if n in omit:continue
  b=a.copy();co.objects.link(b)
 return sc
setup(s,(-1,1,1.6),.081,(0,-.003,.011))
label(s,'v0.33  |  Lower sensor platform',-.037,.025,.0027)
label(s,'One new base  /  existing clamp and side clips reused',-.037,-.027,.0018)
u=clone('02 NARROWED UNDERSIDE',omit=tuple(n for n in obs if n!='01_QRE_minimal_port'))
setup(u,(.5,-1,-1.5),.059,(0,0,.004))
label(u,'Center step: 0.5 mm trimmed off each side',-.027,.019,.00165)
label(u,'Center platform and sensor 1 mm lower',-.027,-.020,.00165)
comp=bpy.data.scenes.new('03 SAME SCALE BEFORE AFTER');co=collection(comp,'Actual v032 and v033 assembly meshes')
for prefix,source,dx in [('BEFORE',S,-.027),('AFTER',O,.027)]:
 for e in M['parts']:
  if e['name'].startswith('REF_M2'):continue
  a=import_mesh(source/e['filename'],comp,prefix+' '+e['name'],co,e);a.location.x=dx
setup(comp,(0,-1,.28),.104,(0,-.003,.012))
label(comp,'v0.32',-.047,.031,.003)
label(comp,'v0.33',.009,.031,.003)
label(comp,'Fixed side clips  /  center and sensor down 1 mm',-.047,-.034,.00215)
base=clone('04 NEW BASE ONLY',omit=tuple(n for n in obs if n!='01_QRE_minimal_port'))
setup(base,(-1,-1,1.5),.064,(0,-.002,.006))
label(base,'Print only this new base',-.029,.021,.0021)
label(base,'PCB pocket keeps its 9.24 mm opening',-.029,-.022,.0016)
section=bpy.data.scenes.new('05 CENTER AND SHOULDER SECTION');co=collection(section,'Actual STEP intersections')
for n,color in [('REF_section_base','#48545D'),('REF_section_bar','#E5AB62'),('REF_section_PCB','#BF3845')]:
 import_mesh(O/'references'/(n+'.stl'),section,n,co,dict(color=color,reference=True,source='Actual CAD intersection'))
setup(section,(0,-1,.04),.031,(0,P['sensor_screw_axes_xy_mm'][0][1]/1000,.006))
label(section,'Center lowered 1 mm; side heights retained',-.014,.010,.00102)
label(section,'Board lands and pressure plate move together',-.014,-.0105,.001)
checks={n:audit(a) for n,a in obs.items() if not a['reference_only']}
for n,a in checks.items():assert a['components']==1 and a['nonmanifold_edges']==a['inconsistent_winding_edges']==0,(n,a)
(O/'reports/blender_mesh_audit.json').write_text(json.dumps(checks,indent=2))
bpy.data.texts.new('START HERE - flush QRE').write((O/'README.md').read_text());bpy.context.window.scene=s
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='VIEW_3D':
   sp=ar.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL';sp.region_3d.view_location=(0,-.003,.011);sp.region_3d.view_distance=.12;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
views=[(s.name,'01_lowered_assembly'),(u.name,'02_narrowed_underside'),(comp.name,'03_before_after'),(base.name,'04_new_base'),(section.name,'05_center_section')]
assembly_scene_name=s.name
path=O/'LaunchLab_v033_flush_QRE.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
back={n:audit(bpy.data.scenes[assembly_scene_name].objects[n]) for n in checks}
for n,a in back.items():assert a['vertices']==checks[n]['vertices'] and a['triangles']==checks[n]['triangles'] and a['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',parts=back),indent=2))
for name,stem in views:
 sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
bpy.context.window.scene=bpy.data.scenes['01 LOWER SENSOR ASSEMBLY'];bpy.ops.object.select_all(action='DESELECT')
for e in M['parts']:bpy.context.scene.objects[e['name']].select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'LaunchLab_v033_flush_QRE.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False)
print('V033_REAL_RENDER_SAVED_REOPENED',flush=True)
