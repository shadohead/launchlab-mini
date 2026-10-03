"""Real Blender views of underside counterbores and a true axial CAD section."""
from pathlib import Path
import ast, json, sys, bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
O=R/'inspection/M5_recessed_screws_v045'
sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh, collection, configure, audit, material, write_3mf
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='label':
        exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert not (O/'SHA256SUMS.txt').exists()
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
P=json.loads((O/'parameters.json').read_text())
M=json.loads((O/'assembly_manifest.json').read_text())
NAME='01_M5_recessed_screw_platform'
bpy.ops.wm.read_factory_settings(use_empty=True)
bare=bpy.context.scene;bare.name='01 UNDERSIDE RECESSES'
co=collection(bare,'Actual printable carrier')
e=M['parts'][0]
carrier=import_mesh(O/e['filename'],bare,NAME,co,e)
carrier['geometry_revision']='v045 underside screw-head recesses'
carrier.data.materials.append(material('#D7AB61'))
for f in carrier.data.polygons:
    p=f.center*1000
    if -7.801<p.z<-6.399 and any((p.x-x)**2+(p.y-y)**2<2.11**2 for x,y in P['M5_axes_xy_mm']):
        f.material_index=1

def setup(sc,d,target,scale,under=False):
    configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
    sc.render.resolution_x=1500;sc.render.resolution_y=1100;sc.cycles.samples=20
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.073,.095,1)
    sc['electronics']='Factory M5StickS3 on separate launcher carrier'
    sc['battery_allowance']='Factory integrated battery'
    sc['mount']='Existing native U-shaped launcher attachment'
    sc['architecture']='v044 carrier with two underside flat-bottom head recesses'
    sc['status']='CAD head flushness verified; actual fastener fit unverified'
    if under:
        ld=bpy.data.lights.new(sc.name+' underside light','AREA')
        ld.energy=1.2;ld.shape='DISK';ld.size=.12
        ob=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(ob)
        ob.location=(.04,-.05,-.15)
        ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

setup(bare,(1,-1,-1.5),(.006,0,-.003),.088,True)
label(bare,'UNDERSIDE / two recessed M5 screw seats',-.039,.028,.0021)
label(bare,'4.2 mm diameter x 1.4 mm deep / existing mounts retained',-.039,-.029,.00165)

heads=bpy.data.scenes.new('02 FLUSH HEADS');c=collection(heads,'Actual carrier and nominal hardware')
a=carrier.copy();c.objects.link(a)
for e in M['parts']:
    if e['name'].startswith('REF_M2x6'):
        import_mesh(O/e['filename'],heads,e['name'],c,e)
setup(heads,(1,-1,-1.5),(.006,0,-.003),.088,True)
label(heads,'SCREW HEADS / seated flush with the deck underside',-.039,.028,.0019)
label(heads,'Nominal head: 3.8 mm diameter x 1.4 mm thick',-.039,-.029,.0018)

section=bpy.data.scenes.new('03 AXIAL SECTION');c=collection(section,'True mesh section through both screw axes')
for stem,color in [('SECTION_carrier','#357B73'),('SECTION_screw_1','#C3C9D1'),('SECTION_screw_2','#C3C9D1')]:
    ob=import_mesh(O/'references'/(stem+'.stl'),section,stem,c,dict(color=color,reference=True,description='Actual mesh clipped through screw axes',source='v045 CAD section',group='Inspection'))
    if stem=='SECTION_carrier':
        ob.data.materials.append(material('#D7AB61'))
        for f in ob.data.polygons:
            p=f.center*1000
            if -6.401<p.z<-6.399:f.material_index=1
setup(section,(0,1,0),(.0103,-.021,-.0056),.032,True)
label(section,'SECTION / circular head pockets beneath both standoffs',-.0147,.010,.00085)
label(section,'Flat seats move screws 1.4 mm closer to the M5',-.0147,-.010,.00095)

top=bpy.data.scenes.new('04 TOP UNCHANGED');c=collection(top,'Actual upper carrier geometry')
a=carrier.copy();c.objects.link(a)
setup(top,(1,1,1.5),(.007,0,-.003),.090)
label(top,'TOP / existing standoffs and opposite-end supports retained',-.040,.029,.00165)
label(top,'Device pose and launcher attachment unchanged',-.040,-.030,.002)

check=audit(carrier)
assert check['components']==1 and check['nonmanifold_edges']==check['inconsistent_winding_edges']==0
(O/'reports/blender_audit.json').write_text(json.dumps(check,indent=2))
print_scene=bpy.data.scenes.new('05 PRINTABLE PART ONLY');c=collection(print_scene,'One replacement carrier, existing print orientation')
ob=import_mesh(O/'stl'/(NAME+'.stl'),print_scene,NAME+'_PRINT',c,M['parts'][0])
write_3mf(O/'M5_recessed_screws_v045_UNSLICED.3mf',[ob],description='One v045 M5 carrier: 4.2 mm diameter x 1.4 mm deep underside head recesses. Existing side print orientation. Unsliced, no hardware/reference meshes. Actual screw fit unverified. Migbello / Thingiverse 6856080 / CC BY-SA (version unspecified).')
bpy.data.texts.new('README - recessed M5 screw heads').write((O/'README.md').read_text())
bpy.context.window.scene=bare;bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False
            sp.shading.color_type='MATERIAL';sp.region_3d.view_location=(.006,0,-.003);sp.region_3d.view_distance=.105
            sp.region_3d.view_rotation=bare.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
p=O/'M5_recessed_screws_v045.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(p));bpy.ops.wm.open_mainfile(filepath=str(p))
b=audit(bpy.data.scenes['01 UNDERSIDE RECESSES'].objects[NAME])
assert b['vertices']==check['vertices'] and b['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',mesh=b),indent=2))
for name,stem in [('01 UNDERSIDE RECESSES','01_underside_recesses'),('02 FLUSH HEADS','02_flush_heads'),('03 AXIAL SECTION','03_axial_section'),('04 TOP UNCHANGED','04_top_unchanged')]:
    sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'))
    bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',p,flush=True)
