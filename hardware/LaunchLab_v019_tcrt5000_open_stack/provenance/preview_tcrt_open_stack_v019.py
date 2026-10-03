"""CAD-derived open-stack assembly, underside, exploded and print previews."""
from pathlib import Path
import sys,json
import bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,write_3mf
O=R/'releases/LaunchLab_v019_tcrt5000_open_stack';M=json.loads((O/'assembly_manifest.json').read_text());E={e['name']:e for e in M['parts']}
bpy.ops.wm.read_factory_settings(use_empty=True);base=bpy.context.scene;base.name='01 OPEN STACK';col=collection(base,'Actual assembly meshes');objects={}
for e in M['parts']:
 ob=import_mesh(O/e['filename'],base,e['name'],col,e);objects[e['name']]=ob
 if e['group'] in ['clearance','fit_envelope']:ob.hide_render=True;ob.hide_set(True)
def view(scene,direction,scale,target):
 configure(scene,target,Vector(target)+Vector(direction).normalized()*.35,scale);scene.render.resolution_x=1500;scene.render.resolution_y=1050;scene.cycles.samples=32
 scene['architecture']='Original-scale launcher interface, original posts, old TCRT5000 cradle and removable M5 top dock with integrated corner keeper, exposed M5StickS3. No walls/frame.'
 scene['electronics']='Intact M5StickS3 K150 + OLD blue TCRT5000/LM393';scene['battery_allowance']='Integrated M5 battery, no separate battery bay';scene['attachment']='Two M2x6 screws into existing brass inserts; Grove unused.';scene['status']='Digital fit prototype. Physical fit, insertion depth and retention untested.'
 scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.07,.09,.12,1)
def duplicate(name,predicate,shift=lambda n:(0,0,0)):
 scene=bpy.data.scenes.new(name);col=collection(scene,'Actual CAD copies');copies={}
 for n,ob in objects.items():
  if not predicate(n) or E[n]['group'] in ['clearance','fit_envelope']:continue
  c=ob.copy();c.name=name[:2]+' / '+n;col.objects.link(c);c.hide_set(False);c.location+=Vector(shift(n));copies[n]=c
 return scene,copies
view(base,(1,-1.3,1.1),.125,(0,0,.019))
under,_=duplicate('02 UNDERSIDE AND SENSOR',lambda n:E[n]['printable'] or n.startswith('REF_TCRT') or n.startswith('REF_M2') or n.startswith('REF_M3') or n=='REF_M5_OFFICIAL_GEOMETRY')
view(under,(.9,-1.1,-1.1),.125,(0,0,.017))
ex,_=duplicate('03 ASSEMBLY ORDER',lambda n:E[n]['printable'] or E[n]['group'] in ['electronics','liner','visual','fasteners'],lambda n:(0,0,.040 if n=='REF_M5_OFFICIAL_GEOMETRY' or E[n]['group']=='visual' else .033 if E[n]['group']=='liner' else .028 if n.startswith('REF_M3') else .043 if n.startswith('REF_M2x6') else .028 if n.startswith('REF_M2x4') else .026 if n=='04_TCRT_M5_top_dock' else .020 if n=='03_TCRT_sensor_cradle' or n.startswith('REF_TCRT') else 0))
view(ex,(1,-1.3,.7),.20,(0,0,.032))
layout=bpy.data.scenes.new('04 COMPLETE FIVE PIECES');lc=collection(layout,'Complete first-build prints');pr=[];positions=[(65,128),(115,128),(170,135),(208,100),(208,165)]
required=['01_TCRT_attachment_port','03_TCRT_sensor_cradle','04_TCRT_M5_top_dock','02_latch_LEFT','02_latch_RIGHT']
for n,(x,y) in zip(required,positions):
 ob=import_mesh(O/'stl'/f'{n}.stl',layout,n,lc,E[n]);ob.location=(x/1000,y/1000,0);pr.append(ob)
write_3mf(O/'LaunchLab_v019_ALL_PARTS_UNSLICED.3mf',pr,positions=[(x,y,0) for x,y in positions],description='LaunchLab v0.19 OLD TCRT5000 + top-mounted intact M5StickS3. Complete first build: port, sensor cradle, M5 top dock, left and right mounting clips. Unit scale. Physical fit unverified. See README/LICENSE.')
write_3mf(O/'LaunchLab_v019_REPLACEMENTS_UNSLICED.3mf',pr[:3],positions=[(x,y,0) for x,y in positions[:3]],description='LaunchLab v0.19 OLD sensor three replacement pieces. Reuse both original launcher clips. Not a complete first-build plate. See README.')
write_3mf(O/'LaunchLab_v019_CLIPS_UNSLICED.3mf',pr[3:],positions=[(x,y,0) for x,y in positions[3:]],description='Two original-scale launcher mounting clips, one left and one right. No other pieces.')
fit_scene=bpy.data.scenes.new('05 SENSOR FIT SAMPLES');fc=collection(fit_scene,'Two sensor fit pieces');fit=[]
for n,xy,rotation in [('11_TCRT_SEAT_FIT',(108,128),[0,0,0]),('12_TCRT_KEEPER_FIT',(155,128),[180,0,0])]:
 meta={'color':'#417767','group':'Fit samples','source':'LaunchLab v0.19 OLD TCRT5000','reference':False,'description':'Exact PCB seat and keeper geometry, without M5 upper supports.'}
 ob=import_mesh(O/'extras'/f'{n}.stl',fit_scene,n,fc,meta);ob.location=(xy[0]/1000,xy[1]/1000,0);fit.append(ob)
write_3mf(O/'LaunchLab_v019_SENSOR_FIT_UNSLICED.3mf',fit,positions=[(108,128,0),(155,128,0)],description='OLD TCRT5000 sensor fit samples: exact cradle seat and lower keeper, no M5 upper beams. Not additional installed assembly pieces. Physical fit untested.')
view(layout,(.4,-1,1.4),.20,(.137,.132,.018))
checks={}
for n,ob in objects.items():
 if E[n]['printable']:
  a=audit(ob);assert a['nonmanifold_edges']==0 and a['inconsistent_winding_edges']==0 and a['components']==1,(n,a);checks[n]=a
(O/'reports/blender_mesh_audit.json').write_text(json.dumps(checks,indent=2))
bpy.data.texts.new('START HERE - OLD TCRT5000').write((O/'README.md').read_text());bpy.context.window.scene=base
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   s=area.spaces.active;s.clip_start=.0001;s.overlay.show_floor=False;s.overlay.show_extras=False;s.shading.color_type='MATERIAL';s.region_3d.view_location=(0,0,.019);s.region_3d.view_distance=.16;s.region_3d.view_rotation=base.camera.rotation_euler.to_quaternion();s.region_3d.view_perspective='ORTHO'
scenes=[(base,'01_assembled'),(under,'02_underside_sensor'),(ex,'03_exploded'),(layout,'04_complete_five_pieces')]
for s,n in scenes:s.render.filepath=str(O/'renders'/f'{n}.png')
bpy.context.preferences.filepaths.save_version=0;names=[(s.name,n) for s,n in scenes];bn=base.name;file=O/'LaunchLab_v019_tcrt5000_open_stack.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file));bpy.ops.wm.open_mainfile(filepath=str(file));back={}
for n,a in checks.items():
 b=audit(bpy.data.scenes[bn].objects[n]);assert b['vertices']==a['vertices'] and b['triangles']==a['triangles'] and b['components']==1;back[n]=b
(O/'reports/blender_saved_readback.json').write_text(json.dumps({'status':'PASS','parts':back},indent=2))
for n,stem in names:bpy.ops.render.render(write_still=True,scene=n)
print('SAVED_REOPENED_RENDERED',file,flush=True)
