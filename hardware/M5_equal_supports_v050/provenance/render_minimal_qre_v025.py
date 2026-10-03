"""Real Blender render and editable scenes; no generated images or launcher proxy."""
from pathlib import Path
import json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v025_minimal_QRE'
sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,material
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text())
assert json.loads((O/'reports/fit_and_motion.json').read_text())['status']=='PASS'
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='01 MINIMAL QRE SENSOR';co=collection(s,'Actual QRE pod - M5 on separate v024 platform');obs={}
for e in M['parts']:
    a=import_mesh(O/e['filename'],s,e['name'],co,e);a['geometry_revision']='v0.25 minimal QRE';obs[e['name']]=a
def setup(sc,d,scale,target):
    cam=configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
    sc.render.resolution_x=1400;sc.render.resolution_y=1050;sc.cycles.samples=16
    sc['status']='DIGITAL FIT PROTOTYPE - physical fit and retention unverified'
    sc['electronics']='SparkFun QRE1113 analog, current board/sensor reference; separate M5StickS3'
    sc['battery_allowance']='Factory M5 battery on separate unchanged mount'
    sc['mount']='Exact source launcher underside, hinge beds and existing two latch meshes'
    sc['architecture']='Low QRE pocket, dual-edge screw keeper, narrow U clip keeper; M5 carries no sensor load'
    sc['registration']='Sensor and M5 shown independently; no measured relative launcher pose'
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.073,.095,1)
    return cam
def label(sc,text,x,y,size=.003):
    data=bpy.data.curves.new(text,'FONT');data.body=text;data.size=size
    ob=bpy.data.objects.new(text,data);sc.collection.objects.link(ob)
    ob.parent=sc.camera;ob.location=(x,y,-.10)
    mat=bpy.data.materials.get('Label white')
    if mat is None:
        mat=bpy.data.materials.new('Label white');mat.use_nodes=True
        nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.75,.84,.94,1);em.inputs[1].default_value=.8;mat.node_tree.links.new(em.outputs[0],out.inputs[0])
    data.materials.append(mat)
    bg=bpy.data.materials.get('Label backing')
    if bg is None:
        bg=bpy.data.materials.new('Label backing');bg.use_nodes=True
        nodes=bg.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.018,.025,.033,1);em.inputs[1].default_value=1;bg.node_tree.links.new(em.outputs[0],out.inputs[0])
    w=len(text)*size*.62;pad=size*.25
    me=bpy.data.meshes.new(text+' backing')
    me.from_pydata([(-pad,-size*.35,0),(w+pad,-size*.35,0),(w+pad,size*1.1,0),(-pad,size*1.1,0)],[],[(0,1,2,3)])
    panel=bpy.data.objects.new(text+' backing',me);sc.collection.objects.link(panel)
    panel.parent=sc.camera;panel.location=(x,y,-.1002);me.materials.append(bg)
def clone(name,shift=lambda n:(0,0,0),omit=()):
    sc=bpy.data.scenes.new(name);c=collection(sc,'Production mesh copies')
    for n,a in obs.items():
        if n in omit:continue
        b=a.copy();c.objects.link(b);b.location+=Vector(shift(n))
    return sc
setup(s,(-1,1,1.65),.085,(0,-.003,.012))
label(s,'v0.25  |  Separate QRE sensor mount',-.039,.027,.0028)
label(s,'Low pocket + dual-edge keeper  /  M5 remains separate',-.039,-.029,.0018)
u=clone('02 OPTICAL UNDERSIDE');setup(u,(-.6,-1,-1.5),.080,(0,-.004,.004))
for a in u.objects:
    if a.type=='LIGHT':a.location.z=-abs(a.location.z);a.rotation_euler=(Vector((0,-.004,.004))-a.location).to_track_quat('-Z','Y').to_euler()
label(u,'Original launcher contacts and optical datum',-.036,.026,.0025)
def explode(n):
    if n=='02_QRE_clip_keeper' or 'CLIP' in n:return (0,0,.02)
    if n=='03_QRE_fork_keeper' or 'SENSOR_' in n:return (0,0,.011)
    return (0,0,0)
x=clone('03 EXPLODED KEEPERS',explode);setup(x,(-1,1,1.6),.100,(0,-.003,.019))
label(x,'Two small keepers; four M2 screws',-.045,.032,.003)
detail=clone('04 QRE BOARD SEAT',omit=('03_QRE_fork_keeper','02_QRE_clip_keeper','REF_M2x5_CLIP_1','REF_M2x5_CLIP_2','REF_M2x4_SENSOR_1','REF_M2x4_SENSOR_2','08_QRE_latch_LEFT','09_QRE_latch_RIGHT'))
setup(detail,(-.4,1,2),.037,(.0002,-.0065,.007))
label(detail,'14 x 9 mm PCB: edge lands + end stops',-.017,.011,.0011)
label(detail,'Keeper removed to show the close-fitting seat',-.017,-.012,.0009)
comparison=bpy.data.scenes.new('05 BEFORE AND AFTER');c=collection(comparison,'Same-scale comparison')
old=R/'releases/LaunchLab_v021_native_grip_M5';oldM=json.loads((old/'assembly_manifest.json').read_text())
for e in oldM['parts']:
    if e['group']!='QRE':continue
    a=import_mesh(old/e['filename'],comparison,'BEFORE / '+e['name'],c,e);a.location.x=-.041
    a['geometry_revision']='v0.21 sensor assembly, unchanged reference'
for n,a in obs.items():b=a.copy();b.name='AFTER / '+n;c.objects.link(b);b.location.x=.041
setup(comparison,(0,-1,1.9),.159,(0,-.003,.012))
label(comparison,'BEFORE',-.066,.045,.0038)
label(comparison,'v0.25  MINIMAL',.022,.045,.0038)
label(comparison,f'{P["comparison"]["material_reduction_percent"]:.0f}% less plastic in the three replacement parts',-.069,-.049,.003)
label(comparison,'Same launcher footprint. Tall frame/posts removed.',-.069,-.055,.0025)
# Independent M5 view uses its delivered meshes at unchanged native coordinates.
m5=bpy.data.scenes.new('06 M5 SEPARATE UNCHANGED');c=collection(m5,'Unmodified v024 carrier and factory M5')
m5src=R/'releases/LaunchLab_v024_stepped_platform'
for e in json.loads((m5src/'assembly_manifest.json').read_text())['parts']:
    ob=import_mesh(m5src/e['filename'],m5,'v024 / '+e['name'],c,e);ob['geometry_revision']='v0.24 unchanged reference'
setup(m5,(-1,-1,1.9),.080,(.006,0,0))
label(m5,'M5 keeps its separate v0.24 stepped platform',-.036,.026,.0024)
checks={n:audit(a) for n,a in obs.items() if not a['reference_only']}
for n,a in checks.items():assert a['components']==1 and a['nonmanifold_edges']==a['inconsistent_winding_edges']==0,(n,a)
(O/'reports/blender_mesh_audit.json').write_text(json.dumps(checks,indent=2))
bpy.data.texts.new('START HERE - minimal separate QRE').write((O/'README.md').read_text())
bpy.context.window.scene=s
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            sp=ar.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL';sp.region_3d.view_location=(0,-.003,.012);sp.region_3d.view_distance=.12;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
views=[(s.name,'01_minimal_sensor'),(u.name,'02_underside'),(x.name,'03_exploded'),(detail.name,'04_PCB_seat'),(comparison.name,'05_before_after'),(m5.name,'06_M5_separate')]
path=O/'LaunchLab_v025_minimal_QRE.blend';bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
back={n:audit(bpy.data.scenes['01 MINIMAL QRE SENSOR'].objects[n]) for n in checks}
for n,a in back.items():assert a['vertices']==checks[n]['vertices'] and a['triangles']==checks[n]['triangles'] and a['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps({'status':'PASS','parts':back},indent=2))
for name,stem in ([] if '--export-only' in sys.argv else views):
    sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
bpy.context.window.scene=bpy.data.scenes['01 MINIMAL QRE SENSOR'];bpy.ops.object.select_all(action='DESELECT')
export_names={e['name'] for e in M['parts']}
for a in bpy.context.scene.objects:
    if a.name in export_names:a.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'LaunchLab_v025_minimal_QRE.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False)
print('V025_REAL_RENDER_SAVED_REOPENED',flush=True)
