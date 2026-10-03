"""Render the tapered center tab with a rounded blend to its plate."""
from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'inspection/M5_smooth_rectangle_v048'
sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,material,write_3mf
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='label':exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert not (O/'SHA256SUMS.txt').exists()
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text());NAME=M['parts'][0]['name']
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='01 SMOOTH CENTER TAB'
ob=import_mesh(O/'stl'/(NAME+'.stl'),s,NAME,collection(s,'One printable carrier'),M['parts'][0])
ob['geometry_revision']='v048 tapered tab with 0.3 mm base and corner blends'
face=-P['center_rectangle']['plate_face_x_mm']+P['print_translation_mm'][2]
def highlight(a,new=True):
    a.data.materials.append(material('#D7AB61'))
    for f in a.data.polygons:
        p=f.center*1000
        if p.z>face+.00005 and ((abs(p.y)<1.8 and -2.5<p.x<3.5) if new else (abs(p.y)<.876 and -1.401<p.x<2.351)):f.material_index=1
highlight(ob)
def setup(sc,d,target,scale):
    configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
    sc.render.resolution_x=1300;sc.render.resolution_y=1100;sc.cycles.samples=20
    sc['electronics']='Factory M5StickS3 on separate launcher carrier';sc['battery_allowance']='Factory integrated battery'
    sc['mount']='Existing native U-shaped launcher attachment';sc['architecture']='v047 carrier with a tapered tab and rounded base blend'
    sc['status']='CAD geometry verified; revised launcher fit untested'
setup(s,(1,1,1.5),(0,0,.0175),.084)
label(s,'Center tab / sloped sides and smooth base transition',-.037,.028,.0019)
label(s,'0.3 mm edge and base blends / 1.25 mm projection',-.037,-.029,.0019)
close=bpy.data.scenes.new('02 REVISED CLOSEUP');c=collection(close,'Actual print mesh')
a=ob.copy();c.objects.link(a)
setup(close,(1,1,1.5),(.000475,0,face/1000),.020)
label(close,'Rounded trapezoid / blended into the plate',-.009,.006,.00055)
label(close,'Sloped sides / softer corners / 1.25 mm projection',-.009,-.006,.0005)
before=bpy.data.scenes.new('03 PREVIOUS CLOSEUP');c=collection(before,'Original v047 print mesh')
old=import_mesh(R/'inspection/M5_rotated_rectangle_v047/stl/01_M5_rotated_rectangle_platform.stl',before,'ORIGINAL_v047',c,dict(color='#357B73',reference=True,source='Frozen v047',description='Previous rectangle footprint',group='Inspection'))
highlight(old,False);setup(before,(1,1,1.5),(.000475,0,face/1000),.020)
label(before,'Previous straight-sided tab / comparison only',-.009,.006,.00055)
label(before,'Previous footprint: 1.75 x 3.75 mm / projection: 1.25 mm',-.009,-.006,.0005)
top=bpy.data.scenes.new('04 FOOTPRINT TOP');c=collection(top,'Actual print mesh from directly above')
a=ob.copy();c.objects.link(a);setup(top,(0,0,1),(.000475,0,face/1000),.012)
label(top,'Tapered tab / wider base and rounded corners',-.0054,.0036,.00032)
label(top,'Same center, direction and 1.25 mm projection',-.0054,-.0036,.00036)
check=audit(ob);assert check['components']==1 and check['nonmanifold_edges']==check['inconsistent_winding_edges']==0
(O/'reports/blender_audit.json').write_text(json.dumps(check,indent=2))
write_3mf(O/'M5_smooth_rectangle_v048_UNSLICED.3mf',[ob],description='One M5 carrier with trapezoidal center tab, 0.3 mm rounded edges and concave blend at the plate. Projection 1.25 mm. Previous screw-head recesses preserved. Unsliced, existing side print orientation. Revised physical launcher fit untested. Migbello / Thingiverse 6856080 / CC BY-SA (version unspecified).')
bpy.data.texts.new('README - smooth tapered center tab').write((O/'README.md').read_text())
bpy.context.window.scene=s;bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL'
            sp.region_3d.view_location=(0,0,.0175);sp.region_3d.view_distance=.10;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
p=O/'M5_smooth_rectangle_v048.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p));bpy.ops.wm.open_mainfile(filepath=str(p))
b=audit(bpy.data.scenes['01 SMOOTH CENTER TAB'].objects[NAME]);assert b['vertices']==check['vertices'] and b['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',mesh=b),indent=2))
for name,stem in [('01 SMOOTH CENTER TAB','01_revised_carrier'),('02 REVISED CLOSEUP','02_revised_closeup'),('03 PREVIOUS CLOSEUP','03_previous_closeup'),('04 FOOTPRINT TOP','04_footprint_top')]:
    sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',p,flush=True)
