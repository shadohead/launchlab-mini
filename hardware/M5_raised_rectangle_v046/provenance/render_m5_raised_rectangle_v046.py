"""Show the real printable carrier and the 1 mm extension of its center tab."""
from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'inspection/M5_raised_rectangle_v046'
sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,material,write_3mf
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='label':exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert not (O/'SHA256SUMS.txt').exists()
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text())
NAME=M['parts'][0]['name']
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='01 REVISED CENTER RECTANGLE'
ob=import_mesh(O/'stl'/(NAME+'.stl'),s,NAME,collection(s,'One printable carrier'),M['parts'][0])
ob['geometry_revision']='v046 tiny rectangle projects 1 mm farther from plate'
ob.data.materials.append(material('#D7AB61'))
face=-P['center_rectangle']['plate_face_x_mm']+P['print_translation_mm'][2]
for f in ob.data.polygons:
    p=f.center*1000
    if p.z>face-.001 and abs(p.y)<1.876 and -.401<p.x<1.351:f.material_index=1
def setup(sc,d,target,scale):
    configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
    sc.render.resolution_x=1300;sc.render.resolution_y=1100;sc.cycles.samples=20
    sc['electronics']='Factory M5StickS3 on separate launcher carrier'
    sc['battery_allowance']='Factory integrated battery'
    sc['mount']='Existing native U-shaped launcher attachment'
    sc['architecture']='v045 carrier with center rectangle extended outward 1 mm'
    sc['status']='CAD geometry verified; revised launcher fit untested'
setup(s,(1,1,1.5),(0,0,.0175),.084)
label(s,'Center rectangle / 1 mm farther out from plate',-.037,.028,.002)
label(s,'Projection: 0.25 mm -> 1.25 mm',-.037,-.029,.002)
close=bpy.data.scenes.new('02 REVISED CLOSEUP');c=collection(close,'Actual copied print mesh')
copy=ob.copy();c.objects.link(copy)
setup(close,(1,1,1.5),(.000475,0,face/1000),.020)
label(close,'Same position / original rounded cap retained',-.009,.006,.0005)
label(close,'1.25 mm projection from the plate',-.009,-.006,.0006)
original=bpy.data.scenes.new('03 ORIGINAL CLOSEUP');c=collection(original,'Original v045 print mesh')
old=import_mesh(R/'inspection/M5_recessed_screws_v045/stl/01_M5_recessed_screw_platform.stl',original,'ORIGINAL_v045',c,dict(color='#357B73',reference=True,source='Frozen v045',description='Previous 0.25 mm projection',group='Inspection'))
old.data.materials.append(material('#D7AB61'))
for f in old.data.polygons:
    p=f.center*1000
    if p.z>face-.001 and abs(p.y)<1.876 and -.401<p.x<1.351:f.material_index=1
setup(original,(1,1,1.5),(.000475,0,face/1000),.020)
label(original,'Previous center rectangle / reference only',-.009,.006,.00055)
label(original,'0.25 mm projection from the plate',-.009,-.006,.0006)
section=bpy.data.scenes.new('04 CENTER SECTION');c=collection(section,'True center section through the rectangle')
q=import_mesh(O/'references/SECTION_revised_rectangle.stl',section,'SECTION_revised',c,dict(color='#357B73',reference=True,source='True v046 CAD section',description='Center cross-section, not printable',group='Inspection'))
q.data.materials.append(material('#D7AB61'))
for f in q.data.polygons:
    if f.center.x*1000<-11.5:f.material_index=1
setup(section,(0,-1,0),(-.01165,0,.000375),.006)
label(section,'Center section / gold shows the raised rectangle',-.0027,.0018,.00016)
label(section,'Total projection from plate: 1.25 mm',-.0027,-.0018,.00019)
a=audit(ob)
assert a['components']==1 and a['nonmanifold_edges']==a['inconsistent_winding_edges']==0
(O/'reports/blender_audit.json').write_text(json.dumps(a,indent=2))
write_3mf(O/'M5_raised_rectangle_v046_UNSLICED.3mf',[ob],description='One M5 carrier: tiny center rectangle projects an additional 1 mm, total 1.25 mm. Previous underside screw-head recesses preserved. Unsliced, existing side print orientation. Revised physical launcher fit untested. Migbello / Thingiverse 6856080 / CC BY-SA (version unspecified).')
bpy.data.texts.new('README - center rectangle').write((O/'README.md').read_text())
bpy.context.window.scene=s;bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL'
            sp.region_3d.view_location=(0,0,.0175);sp.region_3d.view_distance=.10;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
p=O/'M5_raised_rectangle_v046.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p));bpy.ops.wm.open_mainfile(filepath=str(p))
b=audit(bpy.data.scenes['01 REVISED CENTER RECTANGLE'].objects[NAME]);assert b['vertices']==a['vertices'] and b['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',mesh=b),indent=2))
for name,stem in [('01 REVISED CENTER RECTANGLE','01_revised_carrier'),('02 REVISED CLOSEUP','02_revised_closeup'),('03 ORIGINAL CLOSEUP','03_original_closeup'),('04 CENTER SECTION','04_center_section')]:
    if '--only-full' in sys.argv and stem!='01_revised_carrier':continue
    sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',p,flush=True)
