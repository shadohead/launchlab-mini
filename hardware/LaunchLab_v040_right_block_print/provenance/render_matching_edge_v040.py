"""Real Blender review of the user's circled right-block 3 mm trim."""
from pathlib import Path
import ast
import json
import math
import sys
import bpy
from mathutils import Vector

R = Path(__file__).resolve().parents[1]
O = R/'releases/LaunchLab_v040_right_block_print'
OLD = R/'releases/LaunchLab_v024_stepped_platform'
sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh, collection, configure, material, audit
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='label':
        exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M = json.loads((O/'assembly_manifest.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = '01 CIRCLED RIGHT BLOCK TRIM'
group = collection(scene,'Actual revised carrier and factory M5')
objects = {}

def button_color(ob):
    ob.data.materials.append(material('#47AA69'))
    index=len(ob.data.materials)-1
    for p in ob.data.polygons:
        point=p.center*1000
        if abs(point.x+1.7)<.02 and -17.073<point.y<-13.927 and -.301<point.z<4.773:
            p.material_index=index

for item in M['parts']:
    ob=import_mesh(O/item['filename'],scene,item['name'],group,item)
    ob['geometry_revision']='v0.40: circled raised right block trimmed left 3mm'
    objects[item['name']]=ob
    if item['name']=='REF_M5Stick_factory_geometry':button_color(ob)

def setup(sc,direction,scale,target,top=False):
    camera=configure(sc,target,Vector(target)+Vector(direction).normalized()*.35,scale)
    if top:camera.rotation_euler=(0,0,-math.pi/2)
    sc.render.resolution_x=1600
    sc.render.resolution_y=1100
    sc.cycles.samples=20
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.073,.095,1)
    sc['status']='MODEL PREVIEW ONLY - physical thumb fit and strength unverified'
    sc['electronics']='Factory M5StickS3; separate existing QRE mount unchanged'
    sc['mount']='User-circled raised right block shortened 3mm along Y; lower foot unchanged'
    sc['architecture']='Original X/Z profile, M5 pose, deck, posts and receivers preserved'
    sc['battery_allowance']='Factory M5 battery'
    return camera

setup(scene,(-1,-1,1.1),.077,(.005,0,0))
label(scene,'3 mm trim / matching factory edge',-.034,.022,.0024)
label(scene,'Original M5 position and lower foot retained',-.034,-.024,.0018)
bare=bpy.data.scenes.new('03 BARE MOUNT')
group=collection(bare,'Actual revised carrier')
group.objects.link(objects['01_M5_stepped_platform'].copy())
setup(bare,(1,-1,1.05),.073,(.005,0,-.001))
label(bare,'Trimmed right block with matching 0.5 mm bevel',-.032,.021,.0021)

top=bpy.data.scenes.new('02 TOP DOWN BEFORE AFTER')
actual=collection(top,'Actual original and revised models')
annotations=collection(top,'Review annotations - not print geometry')
for title,source,dy in [('Original',OLD,.034),('Revised',O,-.034)]:
    for item in M['parts']:
        if item['name'].startswith('REF_M2') or item['name'].startswith('REF_soft'):continue
        ob=import_mesh(source/item['filename'],top,title+' '+item['name'],actual,item)
        ob.location.y=dy
        if item['name']=='REF_M5Stick_factory_geometry':button_color(ob)
    # The arrow spans the actual old and new raised-block end faces.
    curve=bpy.data.curves.new(title+' leftward 3mm arrow','CURVE')
    curve.dimensions='3D';curve.bevel_depth=.00009
    spline=curve.splines.new('POLY');spline.points.add(1)
    spline.points[0].co=(-.0065,dy-.0185,.0107,1)
    spline.points[1].co=(-.0065,dy-.0155,.0107,1)
    arrow=bpy.data.objects.new(curve.name,curve);annotations.objects.link(arrow)
    curve.materials.append(material('#F8DF9C'))
    mesh=bpy.data.meshes.new(title+' arrowhead')
    mesh.from_pydata([(-.0065,dy-.0155,.0107),(-.007,dy-.0163,.0107),
                     (-.006,dy-.0163,.0107)],[],[(0,1,2)])
    head=bpy.data.objects.new(mesh.name,mesh);annotations.objects.link(head)
    mesh.materials.append(material('#F8DF9C'))
overlay=import_mesh(O/'references/REMOVED_circled_right_3mm_visual.stl',top,
    'Orange actual removed portion',annotations,
    dict(color='#EFAB3D',reference=True,source='Actual original minus revised mesh',
         description='Only the circled raised right block is cut 3mm left',group='ANNOTATION'))
overlay.location.y=.034;overlay.location.z=.000035
setup(top,(0,0,1),.132,(.005,0,0),True)
top.render.resolution_x=1800;top.render.resolution_y=1125
label(top,'TOP VIEW  /  Circled right block: 3 mm LEFT',-.060,.033,.003)
label(top,'Original: orange portion to remove',-.060,.025,.0025)
label(top,'Revised right block',.012,.025,.0025)
label(top,'3 mm',-.025,-.0175,.0018)
label(top,'3 mm',.043,-.0175,.0018)
label(top,'Side button',-.020,-.0038,.00165)
label(top,'Side button',.045,-.0038,.00165)
label(top,'M5, left block and lower foot unchanged',-.060,-.026,.0024)
label(top,'Factory edge matched / no print dispatched',-.060,-.035,.0022)

check=audit(objects['01_M5_stepped_platform'])
assert check['components']==1 and check['nonmanifold_edges']==check['inconsistent_winding_edges']==0
(O/'reports/blender_mesh_audit.json').write_text(json.dumps(check,indent=2))
bpy.data.texts.new('README: circled block preview').write((O/'README.md').read_text())
bpy.context.window.scene=scene
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_start=.0001
            sp.overlay.show_floor=False;sp.overlay.show_extras=False
            sp.shading.color_type='MATERIAL';sp.region_3d.view_location=(.005,0,0)
            sp.region_3d.view_distance=.1
            sp.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
            sp.region_3d.view_perspective='ORTHO'
bpy.context.preferences.filepaths.save_version=0
path=O/'LaunchLab_v040_right_block_print.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
readback=audit(bpy.data.scenes['01 CIRCLED RIGHT BLOCK TRIM'].objects['01_M5_stepped_platform'])
assert readback['vertices']==check['vertices'] and readback['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',mesh=readback),indent=2))
for name,stem in [('02 TOP DOWN BEFORE AFTER','01_topdown_before_after'),
                  ('01 CIRCLED RIGHT BLOCK TRIM','02_assembled'),('03 BARE MOUNT','03_bare_mount')]:
    sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'))
    bpy.ops.render.render(write_still=True,scene=name)
bpy.context.window.scene=bpy.data.scenes['01 CIRCLED RIGHT BLOCK TRIM']
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    if ob.type=='MESH' and ob.name in objects:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'LaunchLab_v040_right_block_print.glb'),
    export_format='GLB',use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False)
print('V040_CIRCLED_BLOCK_RENDERED_AND_REOPENED',flush=True)
