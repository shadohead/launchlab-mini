"""Two local P1S plates: base/crossbar with slim trees; upright clamp without supports."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import ast,hashlib,json,shutil,xml.etree.ElementTree as ET
import numpy as np,trimesh
from scipy.spatial import cKDTree
import slice_comparison_v05 as slicer
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v033_flush_QRE'
assert not (O/'SHA256SUMS.txt').exists()
assert json.loads((O/'reports/fit_and_motion.json').read_text())['status']=='PASS'
N='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',N);q=lambda s:'{'+N+'}'+s
slicer.P=R/'inspection/print_v033_flush_QRE';(slicer.P/'profiles').mkdir(parents=True,exist_ok=True)
for filename in ['machine.json','PLA.json']:
    shutil.copy2(R/'inspection/print_v031_vertical_QRE/profiles'/filename,slicer.P/'profiles'/filename)
for key,supports in [('base',True)]:
    d=json.loads((R/'inspection/print_v031_vertical_QRE/profiles/process.json').read_text())
    d.update(name='LaunchLab v033 '+key,print_settings_id='LaunchLab v033 '+key,enable_support=str(int(supports)),support_type='tree(auto)',support_style='tree_slim',layer_height='0.2',initial_layer_print_height='0.2',wall_generator='arachne')
    (slicer.P/'profiles'/('process_'+key+'.json')).write_text(json.dumps(d,indent=2))
shutil.copytree(slicer.P/'profiles',O/'print_profiles',dirs_exist_ok=True)
ns={'m':N}
for node in ast.parse((R/'scripts/finalize_low_stack_v018.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in ['project_meshes','compare']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'readback','exec'))
cases=[('new_base',['01_QRE_minimal_port'],'base','BASE_TREE_SLIM')]
metrics={};checks=[]
for key,names,profile,suffix in cases:
    ms=[trimesh.load(O/'stl'/(n+'.stl'),force='mesh') for n in names]
    root=ET.Element(q('model'),unit='millimeter')
    ET.SubElement(root,q('metadata'),name='Title').text='LaunchLab v033 '+suffix
    ET.SubElement(root,q('metadata'),name='Description').text='Narrower lower QRE platform: print only the base, reuse v032 centered pressure plate and crossbar, original latches and separate M5 platform.'
    resources=ET.SubElement(root,q('resources'));build=ET.SubElement(root,q('build'))
    for i,(n,m) in enumerate(zip(names,ms),1):
        ob=ET.SubElement(resources,q('object'),id=str(i),name=n,type='model')
        mesh=ET.SubElement(ob,q('mesh'));vs=ET.SubElement(mesh,q('vertices'));fs=ET.SubElement(mesh,q('triangles'))
        for v in m.vertices:ET.SubElement(vs,q('vertex'),{k:format(float(a),'.12g') for k,a in zip('xyz',v)})
        for f in m.faces:ET.SubElement(fs,q('triangle'),{k:str(int(a)) for k,a in zip(['v1','v2','v3'],f)})
        ET.SubElement(build,q('item'),objectid=str(i),transform=f'1 0 0 0 1 0 0 0 1 {60+i*40} 128 0')
    path=O/('LaunchLab_v033_'+suffix+'_UNSLICED.3mf')
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
    report=slicer.run('v033_'+suffix,'PLA',path,'process_'+profile+'.json')
    report['support_transition_g']=report['extrusion_by_feature_g'].get('Support transition',0.)
    report['support_g']=sum(v for k,v in report['extrusion_by_feature_g'].items() if k.startswith('Support'))
    dest=O/'bambu'/('LaunchLab_v033_P1S_PLA_'+suffix+'.3mf');shutil.copy2(report['project'],dest)
    report['release_project']=str(dest.relative_to(O));report['parts']=names
    log=Path(report['project']).parent/'slice.log';report['log_warnings']=[l.strip() for l in log.read_text().splitlines() if 'warning' in l.lower() or 'error' in l.lower()]
    assert not report['log_warnings'],report['log_warnings']
    if profile=='plate':assert report['support_g']==0
    for file in [path,dest]:
        with ZipFile(file) as z:
            assert z.testzip() is None
            actual=project_meshes(z);assert len(actual)==len(ms)
            unused=list(ms)
            for a in actual:
                found=next((i for i,b in enumerate(unused) if compare(a,b)),None)
                assert found is not None,(file,a.extents)
                unused.pop(found)
            result={'file':str(file.relative_to(O)),'mesh_count':len(actual),'geometry_readback':'PASS'}
            if 'Metadata/plate_1.gcode' in z.namelist():
                assert hashlib.md5(z.read('Metadata/plate_1.gcode')).hexdigest()==z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
                settings=json.loads(z.read('Metadata/project_settings.config'))
                assert settings['enable_support']==('1' if profile=='base' else '0') and settings['layer_height']=='0.2'
                if profile=='base':assert settings['support_type']=='tree(auto)' and settings['support_style']=='tree_slim'
                meta=json.loads(z.read('Metadata/plate_1.json'));assert len(meta['bbox_objects'])==len(names) and min(meta['bbox_all'])>=0 and max(meta['bbox_all'])<=256
                result.update(gcode_integrity='PASS',supports_enabled=profile=='base',actual_support_g=report['support_g'])
            checks.append(result)
    metrics[key]=report
(O/'reports/slicing_metrics.json').write_text(json.dumps(metrics,indent=2))
(O/'reports/project_readback.json').write_text(json.dumps({'status':'PASS','checks':checks},indent=2))
(O/'print_inventory.json').write_text(json.dumps(dict(replacement_printed_parts=1,plates={k:r['parts'] for k,r in metrics.items()},reuse=['v032 centered pressure plate','v032 crossbar','existing QRE latches','separate v024 M5 platform','two M2x4 sensor screws','two M2x5 clip screws'],requested_filament='AMS A3 / filament 3; assignment occurs at dispatch',dispatch='None'),indent=2))
print('V033_NEW_BASE_SLICE_READBACK_PASS',flush=True)
