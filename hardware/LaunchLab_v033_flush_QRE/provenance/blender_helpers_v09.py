"""Shared Blender import, scene, audit and 3MF helpers; extracted from our v0.2.1 builder."""
import bpy,bmesh
from mathutils import Vector,Matrix
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
q=lambda s:'{'+NS+'}'+s
def bounds(ob):
    vs=[ob.matrix_world@v.co for v in ob.data.vertices]
    lo=[min(v[j] for v in vs)*1000 for j in range(3)]
    hi=[max(v[j] for v in vs)*1000 for j in range(3)]
    return {'min':lo,'max':hi,'size':[hi[j]-lo[j] for j in range(3)]}

def audit(ob):
    bm=bmesh.new();bm.from_mesh(ob.data)
    unseen=set(bm.verts); components=0
    while unseen:
        components+=1; todo=[unseen.pop()]
        while todo:
            v=todo.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in unseen:unseen.remove(other);todo.append(other)
    result={'vertices':len(bm.verts),'triangles':len(bm.faces),
        'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'inconsistent_winding_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
        'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),
        'components':components,'volume_mm3':bm.calc_volume(signed=True)*1e9,
        'bounds_mm':bounds(ob)}
    bm.free();return result

def material(hexcolor):
    if hexcolor in bpy.data.materials:return bpy.data.materials[hexcolor]
    mat=bpy.data.materials.new(hexcolor)
    rgb=[int(hexcolor[j:j+2],16)/255 for j in (1,3,5)]
    linear=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    mat.diffuse_color=(*linear,1);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*linear,1)
    bsdf.inputs['Roughness'].default_value=.42
    return mat

def collection(scene,name):
    col=bpy.data.collections.new(name);scene.collection.children.link(col);return col

def import_mesh(path,scene,name,col,meta=None):
    bpy.context.window.scene=scene
    bpy.ops.wm.stl_import(filepath=str(path),global_scale=.001,use_scene_unit=False)
    ob=bpy.context.object;ob.name=name
    # STL importer stores the mm-to-m conversion on object scale. Bake the unit
    # conversion into vertices so linked inspection copies/export data stay SI.
    ob.data.transform(ob.matrix_basis);ob.matrix_basis=Matrix.Identity(4)
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob)
    if meta:
        ob.data.materials.append(material(meta['color']))
        for key in ['source','description','group']:ob[key]=meta.get(key,'')
        ob['reference_only']=meta['reference'];ob['physical_fit']='UNVERIFIED'
        ob['geometry_revision']='v0.9 longitudinal candidate'
    bpy.context.view_layer.update();return ob

def configure(scene, target, camera_pos, ortho):
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene.unit_settings.length_unit='MILLIMETERS'
    scene['status']='FIT PROTOTYPE - battery, optical alignment, retention UNVERIFIED'
    scene['electronics']='Waveshare ESP32-S3-Touch-AMOLED-1.64; HiLetgo TCRT5000; MakerFocus 3.7 V 1100 mAh'
    scene['battery_allowance']='30 x 50 x 7 mm USER-MEASURED body; connector/lead exit unmeasured'
    scene['mount']='Original-scale two-clip TOP port; no side-grip interface'
    scene.world=bpy.data.worlds.new(scene.name+' world');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.2,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
    rig=collection(scene,'VIEW / cameras and lights')
    cd=bpy.data.cameras.new(scene.name+' camera');cam=bpy.data.objects.new(cd.name,cd);rig.objects.link(cam)
    cam.location=camera_pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cd.type='ORTHO';cd.ortho_scale=ortho;cd.clip_start=.0001;cd.clip_end=10;scene.camera=cam
    for name,pos,power,size in [('Key',(.08,-.11,.24),.8,.15),('Fill',(-.12,-.03,.13),.5,.15),('Rim',(.05,.13,.2),1,.1)]:
        ld=bpy.data.lights.new(scene.name+name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
        light=bpy.data.objects.new(ld.name,ld);rig.objects.link(light);light.location=pos
        light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1440;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    return cam

def write_3mf(filename,objects,positions=None,description=None):
    root=ET.Element(q('model'),{'unit':'millimeter'})
    ET.SubElement(root,q('metadata'),{'name':'Title'}).text=filename.stem
    ET.SubElement(root,q('metadata'),{'name':'Description'}).text=description or 'LaunchLab v0.9 longitudinal; BP port upper optical recess revised; two latches and mating interface at scale 1; UNTESTED fit prototype, unsliced. Migbello / Thingiverse 6856080 / CC BY-SA (version unspecified).'
    resources=ET.SubElement(root,q('resources'));build=ET.SubElement(root,q('build'))
    for ix,ob in enumerate(objects,1):
        obj=ET.SubElement(resources,q('object'),{'id':str(ix),'type':'model','name':ob.name})
        mesh=ET.SubElement(obj,q('mesh'));verts=ET.SubElement(mesh,q('vertices'));tri=ET.SubElement(mesh,q('triangles'))
        for v in ob.data.vertices:ET.SubElement(verts,q('vertex'),{a:format(float(c)*1000,'.9g') for a,c in zip('xyz',v.co)})
        for face in ob.data.polygons:
            assert len(face.vertices)==3
            ET.SubElement(tri,q('triangle'),{a:str(c) for a,c in zip(['v1','v2','v3'],face.vertices)})
        loc=positions[ix-1] if positions else tuple(v*1000 for v in ob.location)
        ET.SubElement(build,q('item'),{'objectid':str(ix),'transform':'1 0 0 0 1 0 0 0 1 '+' '.join(format(v,'.9g') for v in loc)})
    ct='<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rel='<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with ZipFile(filename,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',ct);z.writestr('_rels/.rels',rel)
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
    with ZipFile(filename) as z:
        parsed=ET.fromstring(z.read('3D/3dmodel.model'))
        assert parsed.attrib['unit']=='millimeter'
        assert len(parsed.find(q('build')))==len(objects)
        for item,ob in zip(parsed.find(q('resources')),objects):
            mesh=item.find(q('mesh'))
            assert len(mesh.find(q('vertices')))==len(ob.data.vertices)
            assert len(mesh.find(q('triangles')))==len(ob.data.polygons)
            for el,v in zip(mesh.find(q('vertices')),ob.data.vertices):
                delta=max(abs(float(el.attrib[a])-v.co[j]*1000) for j,a in enumerate('xyz'))
                assert delta<1e-5,(ob.name,el.attrib,tuple(v.co),delta)
