"""Real Blender preview of opposite-end integral M5 support pads."""
from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'inspection/M5_level_support_v044';sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,material
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='label':exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='01 M5 LEVEL SUPPORT';c=collection(s,'Actual carrier and M5 meshes');obs={}
for e in M['parts']:
 ob=import_mesh(O/e['filename'],s,e['name'],c,e);obs[e['name']]=ob;ob['geometry_revision']='v044: opposite-end integral back-panel support pads'
 if e['name']=='01_M5_level_platform':
  ob.data.materials.append(material('#D7AB61'))
  for f in ob.data.polygons:
   p=f.center*1000
   if 11.19<p.y<13.81 and p.z>-5.801 and (1.29<p.x<7.31 or 13.29<p.x<19.31):f.material_index=1

def setup(sc,d,target,scale):
 configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
 sc.render.resolution_x=1500;sc.render.resolution_y=1100;sc.cycles.samples=20;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.073,.095,1)
 sc['electronics']='Factory M5StickS3 on separate launcher carrier; sensor mount excluded'
 sc['battery_allowance']='Factory integrated battery'
 sc['architecture']='Accepted v040 trimmed mount with integral pads against the opposite back panel'
 sc['status']='CAD contact verified; physical leveling and fit untested'
setup(s,(1,-1,1.2),(.006,0,0),.074)
label(s,'M5 mount / opposite-end leveling supports',-.032,.023,.0021)
label(s,'Same screws and device pose / printed support pads',-.032,-.024,.0018)

def clone(name,explode=False,bare=False):
 sc=bpy.data.scenes.new(name);co=collection(sc,'Actual CAD copies')
 for n,a in obs.items():
  if bare and n!='01_M5_level_platform':continue
  b=a.copy();co.objects.link(b)
  if explode and n!='01_M5_level_platform':b.location.z+=.017 if n.startswith('REF_M2') else .023
 return sc
bare=clone('02 SUPPORT PADS',bare=True);setup(bare,(1,1,1.5),(.007,0,-.003),.090)
label(bare,'Gold: two integral pads beneath the Hat-side back panel',-.032,.023,.0018)
label(bare,'0.5 mm lift above the deck / no extra fasteners',-.032,-.024,.002)
ex=clone('03 EXPLODED SUPPORT');
for ob in ex.objects:
 if ob.type=='MESH' and ob.get('reference_only'):ob.location.z+=.017 if ob.name.startswith('REF_M2') else .023
setup(ex,(1,1,1.2),(.007,0,.011),.097)
label(ex,'Pads meet the flat back panel at the opposite end',-.042,.029,.0022)
label(ex,'Original two M2x6 mounting screws retained',-.042,-.030,.0022)
side=clone('04 LONG EDGE LEVEL');setup(side,(1,0,0),(.0103,0,-.001),.065)
label(side,'LEVEL CONTACT / factory back panel and screw faces',-.028,.020,.0017)
label(side,'Support pads: 0.5 mm / screw posts: 2.3 mm',-.028,-.021,.0017)
a=audit(obs['01_M5_level_platform']);assert a['components']==1 and a['nonmanifold_edges']==a['inconsistent_winding_edges']==0
(O/'reports/blender_audit.json').write_text(json.dumps(a,indent=2));bpy.data.texts.new('README - leveling supports').write((O/'README.md').read_text());bpy.context.window.scene=s;bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL';sp.region_3d.view_location=(.006,0,0);sp.region_3d.view_distance=.105;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
p=O/'M5_level_support_v044.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p));bpy.ops.wm.open_mainfile(filepath=str(p));b=audit(bpy.data.scenes['01 M5 LEVEL SUPPORT'].objects['01_M5_level_platform']);assert b['vertices']==a['vertices'] and b['nonmanifold_edges']==0;(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',mesh=b),indent=2))
for name,stem in [('01 M5 LEVEL SUPPORT','01_assembled'),('02 SUPPORT PADS','02_bare_supports'),('03 EXPLODED SUPPORT','03_exploded'),('04 LONG EDGE LEVEL','04_side_contact')]:
 sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',p,flush=True)
