from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'inspection/minimal_TCRT_stack_v041';sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='label':exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());E={e['name']:e for e in M['parts']}
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='01 TCRT STACK';co=collection(s,'Actual CAD');obs={}
for e in M['parts']:
 ob=import_mesh(O/e['filename'],s,e['name'],co,e);obs[e['name']]=ob
 if e['group']=='clearance':ob.hide_render=True

def setup(sc,d,target,scale):
 configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
 sc.render.resolution_x=1500;sc.render.resolution_y=1100;sc.cycles.samples=20
 sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.073,.095,1)
 sc['electronics']='OLD TCRT5000 measured 31x13x1 board + factory M5StickS3'
 sc['battery_allowance']='Integrated factory battery'
 sc['architecture']='Open cradle and two-screw keeper with integrated M5 support'
 sc['status']='CAD prototype: physical fit, contact lands and optics unverified'
setup(s,(1,-1.4,1), (0,0,.019),.092)
label(s,'TCRT5000 / compact stacked alternate',-.040,.029,.0025)
label(s,'Open cradle + removable M5 support',-.040,-.030,.0021)

def clone(name,shift,omit):
 sc=bpy.data.scenes.new(name);c=collection(sc,'Actual CAD copies')
 for n,ob in obs.items():
  if n in omit or E[n]['group']=='clearance':continue
  a=ob.copy();c.objects.link(a);a.location+=Vector(shift(n))
 return sc
bare=clone('02 SENSOR CAPTURE',lambda n:(0,0,0),['REF_M5_OFFICIAL_GEOMETRY','REF_M5_SOFT_LINER','REF_M5_SCREEN_VISUAL_ONLY','03_TCRT_M5_clamp_dock'])
setup(bare,(1,-1.3,1.5),(0,0,.011),.085)
label(bare,'31 x 13 mm PCB / four edge seats',-.037,.026,.0025)
label(bare,'Header end open / original launcher clips',-.037,-.027,.0019)
ex=clone('03 EXPLODED',lambda n:(0,0,.029 if n.startswith('REF_M5') else .017 if n=='03_TCRT_M5_clamp_dock' else .008 if n.startswith('REF_TCRT') else 0),[])
setup(ex,(1,-1.4,.8),(0,0,.034),.135)
label(ex,'M5 screws underneath / keeper screws from above',-.059,.041,.0027)
label(ex,'Two screws clamp the board at its bare edge lands',-.059,-.041,.0024)
checks={n:audit(ob) for n,ob in obs.items() if E[n]['printable']}
for n,a in checks.items():assert a['components']==1 and a['nonmanifold_edges']==a['inconsistent_winding_edges']==0,(n,a)
(O/'reports/blender_audit.json').write_text(json.dumps(checks,indent=2))
bpy.context.window.scene=s;bpy.context.preferences.filepaths.save_version=0
path=O/'TCRT_minimal_stack_v041.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
for n,a in checks.items():
 b=audit(bpy.data.scenes['01 TCRT STACK'].objects[n]);assert a['vertices']==b['vertices'] and b['nonmanifold_edges']==0
for name,stem in [('01 TCRT STACK','01_assembled'),('02 SENSOR CAPTURE','02_sensor_cradle'),('03 EXPLODED','03_exploded')]:
 sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',path,flush=True)
