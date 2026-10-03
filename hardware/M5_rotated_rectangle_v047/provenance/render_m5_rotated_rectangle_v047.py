"""Render the center rectangle with its long axis in the other plate direction."""
from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'inspection/M5_rotated_rectangle_v047'
sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,material,write_3mf
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='label':exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert not (O/'SHA256SUMS.txt').exists()
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text());NAME=M['parts'][0]['name']
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='01 TALLER CENTER RECTANGLE'
ob=import_mesh(O/'stl'/(NAME+'.stl'),s,NAME,collection(s,'One printable carrier'),M['parts'][0])
ob['geometry_revision']='v047 center rectangle footprint turned 90 degrees'
face=-P['center_rectangle']['plate_face_x_mm']+P['print_translation_mm'][2]
def highlight(a,new=True):
    a.data.materials.append(material('#D7AB61'))
    for f in a.data.polygons:
        p=f.center*1000
        if p.z>face-.001 and ((abs(p.y)<.876 and -1.401<p.x<2.351) if new else (abs(p.y)<1.876 and -.401<p.x<1.351)):f.material_index=1
highlight(ob)
def setup(sc,d,target,scale):
    configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
    sc.render.resolution_x=1300;sc.render.resolution_y=1100;sc.cycles.samples=20
    sc['electronics']='Factory M5StickS3 on separate launcher carrier';sc['battery_allowance']='Factory integrated battery'
    sc['mount']='Existing native U-shaped launcher attachment';sc['architecture']='v046 carrier with rectangle footprint turned 90 degrees'
    sc['status']='CAD geometry verified; revised launcher fit untested'
setup(s,(1,1,1.5),(0,0,.0175),.084)
label(s,'Center rectangle / long direction turned 90 degrees',-.037,.028,.0019)
label(s,'Root: 1.75 x 3.75 mm / projection: 1.25 mm',-.037,-.029,.0019)
close=bpy.data.scenes.new('02 REVISED CLOSEUP');c=collection(close,'Actual print mesh')
a=ob.copy();c.objects.link(a)
setup(close,(1,1,1.5),(.000475,0,face/1000),.020)
label(close,'Long axis now runs bottom-left to top-right',-.009,.006,.00055)
label(close,'1 mm growth at each end of the former short side',-.009,-.006,.0005)
before=bpy.data.scenes.new('03 PREVIOUS CLOSEUP');c=collection(before,'Original v046 print mesh')
old=import_mesh(R/'inspection/M5_raised_rectangle_v046/stl/01_M5_raised_rectangle_platform.stl',before,'ORIGINAL_v046',c,dict(color='#357B73',reference=True,source='Frozen v046',description='Previous rectangle footprint',group='Inspection'))
highlight(old,False);setup(before,(1,1,1.5),(.000475,0,face/1000),.020)
label(before,'Previous rectangle / comparison only',-.009,.006,.00055)
label(before,'Root: 3.75 x 1.75 mm / projection: 1.25 mm',-.009,-.006,.0005)
top=bpy.data.scenes.new('04 FOOTPRINT TOP');c=collection(top,'Actual print mesh from directly above')
a=ob.copy();c.objects.link(a);setup(top,(0,0,1),(.000475,0,face/1000),.012)
label(top,'New footprint / 1.75 x 3.75 mm at the root',-.0054,.0036,.00032)
label(top,'Same center and outward projection',-.0054,-.0036,.00036)
check=audit(ob);assert check['components']==1 and check['nonmanifold_edges']==check['inconsistent_winding_edges']==0
(O/'reports/blender_audit.json').write_text(json.dumps(check,indent=2))
write_3mf(O/'M5_rotated_rectangle_v047_UNSLICED.3mf',[ob],description='One M5 carrier with center rectangle footprint turned 90 degrees, root 1.75 x 3.75 mm, projection 1.25 mm. Previous screw-head recesses preserved. Unsliced, existing side print orientation. Revised physical launcher fit untested. Migbello / Thingiverse 6856080 / CC BY-SA (version unspecified).')
bpy.data.texts.new('README - taller center rectangle').write((O/'README.md').read_text())
bpy.context.window.scene=s;bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL'
            sp.region_3d.view_location=(0,0,.0175);sp.region_3d.view_distance=.10;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
p=O/'M5_rotated_rectangle_v047.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p));bpy.ops.wm.open_mainfile(filepath=str(p))
b=audit(bpy.data.scenes['01 TALLER CENTER RECTANGLE'].objects[NAME]);assert b['vertices']==check['vertices'] and b['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',mesh=b),indent=2))
for name,stem in [('01 TALLER CENTER RECTANGLE','01_revised_carrier'),('02 REVISED CLOSEUP','02_revised_closeup'),('03 PREVIOUS CLOSEUP','03_previous_closeup'),('04 FOOTPRINT TOP','04_footprint_top')]:
    sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',p,flush=True)
