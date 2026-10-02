"""One local P1S plate containing all six current printable parts."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import ast,hashlib,json,shutil,xml.etree.ElementTree as ET
import numpy as np,trimesh
from scipy.spatial import cKDTree
import slice_comparison_v05 as slicer
R=Path(__file__).resolve().parents[1];S=R/'releases/LaunchLab_v033_flush_QRE';M5=R/'releases/LaunchLab_v040_right_block_print';O=R/'releases/LaunchLab_v040_ALL_ITEMS_PRINT'
assert not (O/'SHA256SUMS.txt').exists(),'Frozen package'
for d in ['stl','step','reports','profiles','provenance','bambu']:(O/d).mkdir(parents=True,exist_ok=True)
parts=[(e['name'],S) for e in json.loads((S/'assembly_manifest.json').read_text())['parts'] if e['printable']]+[('01_M5_stepped_platform',M5)]
inputs={}
for n,src in parts:
 p=src/'stl'/(n+'.stl');h=hashlib.sha256(p.read_bytes()).hexdigest()
 frozen={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (src/'SHA256SUMS.txt').read_text().splitlines()};assert h==frozen['stl/'+n+'.stl']
 inputs[n]=dict(source_release=src.name,source_file='stl/'+n+'.stl',sha256=h,quantity=1,supports=False if n=='03_QRE_pressure_bar' else True)
 shutil.copy2(p,O/'stl'/p.name)
 if (src/'step'/(n+'.step')).exists():shutil.copy2(src/'step'/(n+'.step'),O/'step'/(n+'.step'))
ms=[trimesh.load(O/'stl'/(n+'.stl'),force='mesh') for n,_ in parts]
for m in ms:assert m.is_watertight and m.is_winding_consistent and len(m.split())==1 and abs(m.bounds[0,2])<.001
slicer.P=R/'inspection/print_v040_all_items';(slicer.P/'profiles').mkdir(parents=True,exist_ok=True)
for n in ['machine.json','PLA.json']:shutil.copy2(S/'print_profiles'/n,slicer.P/'profiles'/n)
d=json.loads((S/'print_profiles/process_base.json').read_text());d.update(name='LaunchLab v040 all six parts',print_settings_id='LaunchLab v040 all six parts',brim_type='outer_only',brim_width='5',enable_support='1',support_type='tree(auto)',support_style='tree_slim',wall_generator='arachne',layer_height='0.2',initial_layer_print_height='0.2')
(slicer.P/'profiles/process.json').write_text(json.dumps(d,indent=2));shutil.copytree(slicer.P/'profiles',O/'profiles',dirs_exist_ok=True)
N='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',N);q=lambda s:'{'+N+'}'+s
root=ET.Element(q('model'),unit='millimeter');ET.SubElement(root,q('metadata'),name='Title').text='LaunchLab v040 complete six-part print'
resources=ET.SubElement(root,q('resources'));build=ET.SubElement(root,q('build'))
for i,((n,_),m) in enumerate(zip(parts,ms),1):
 ob=ET.SubElement(resources,q('object'),id=str(i),name=n,type='model');mesh=ET.SubElement(ob,q('mesh'));vs=ET.SubElement(mesh,q('vertices'));fs=ET.SubElement(mesh,q('triangles'))
 for v in m.vertices:ET.SubElement(vs,q('vertex'),{k:format(float(a),'.12g') for k,a in zip('xyz',v)})
 for f in m.faces:ET.SubElement(fs,q('triangle'),{k:str(int(a)) for k,a in zip(['v1','v2','v3'],f)})
 ET.SubElement(build,q('item'),objectid=str(i),transform=f'1 0 0 0 1 0 0 0 1 {80+30*((i-1)%3)} {90+60*((i-1)//3)} 0')
raw=slicer.P/'ALL_ITEMS_UNSLICED.3mf'
with ZipFile(raw,'w',ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
 z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
 z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
# Canonicalize the six independent objects before adding the clamp's object
# override. Re-slice the saved project so its G-code reflects that override.
first=slicer.run('ALL_ITEMS_CANONICAL','PLA',raw)
patched=slicer.P/'ALL_ITEMS_OBJECT_SETTINGS.3mf'
with ZipFile(first['project']) as src,ZipFile(patched,'w',ZIP_DEFLATED) as out:
 cfg=ET.fromstring(src.read('Metadata/model_settings.config'));found=0
 for ob in cfg.findall('object'):
  name=ob.find("metadata[@key='name']").attrib['value']
  if name=='03_QRE_pressure_bar':
   ET.SubElement(ob,'metadata',key='enable_support',value='0');found+=1
 assert found==1
 for info in src.infolist():
  out.writestr(info,ET.tostring(cfg,encoding='utf-8',xml_declaration=True) if info.filename=='Metadata/model_settings.config' else src.read(info.filename))
report=slicer.run('ALL_ITEMS_FINAL','PLA',patched)
report['support_g']=sum(v for k,v in report['extrusion_by_feature_g'].items() if k.startswith('Support'))
dest=O/'bambu/LaunchLab_v040_P1S_PLA_ALL_ITEMS_ONE_PLATE.3mf';shutil.copy2(report['project'],dest)
log=Path(report['project']).parent/'slice.log';warnings=[l.strip() for l in log.read_text().splitlines() if 'warning' in l.lower() or 'error' in l.lower()];assert not warnings,warnings
ns={'m':N}
for node in ast.parse((R/'scripts/finalize_low_stack_v018.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['project_meshes','compare']:exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
with ZipFile(dest) as z:
 assert z.testzip() is None
 actual=project_meshes(z);assert len(actual)==6
 unused=list(ms)
 for a in actual:
  i=next((i for i,b in enumerate(unused) if compare(a,b)),None);assert i is not None
  unused.pop(i)
 assert not unused
 assert hashlib.md5(z.read('Metadata/plate_1.gcode')).hexdigest()==z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
 settings=json.loads(z.read('Metadata/project_settings.config'));meta=json.loads(z.read('Metadata/plate_1.json'));cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
 assert len(meta['bbox_objects'])==6 and min(meta['bbox_all'])>=0 and max(meta['bbox_all'])<=256
 assert len(cfg.findall('plate'))==1 and len(cfg.findall('plate/model_instance'))==6
 assert settings['enable_support']=='1' and settings['support_style']=='tree_slim' and settings['layer_height']=='0.2'
 overrides={ob.find("metadata[@key='name']").attrib['value']:{e.attrib['key']:e.attrib['value'] for e in ob.findall('metadata') if 'key' in e.attrib} for ob in cfg.findall('object')}
 assert overrides['03_QRE_pressure_bar']['enable_support']=='0',overrides
report.update(release_project=str(dest.relative_to(O)),parts=[n for n,_ in parts],plate_count=1,log_warnings=warnings)
(O/'reports/slicing_metrics.json').write_text(json.dumps(report,indent=2));(O/'reports/project_readback.json').write_text(json.dumps(dict(status='PASS',plate_count=1,model_count=6,all_meshes_match_frozen_STLs=True,gcode_md5='PASS',pressure_plate_support_override=False,bed_bounds_mm=meta['bbox_all']),indent=2))
(O/'print_inventory.json').write_text(json.dumps(dict(parts=inputs,plates=1,requested_filament='AMS A3 / filament 3 at dispatch',dispatch='None',hardware=['2 x M2x6 for M5','2 x M2x5 countersunk for clip crossbar','2 x M2x4 pan head for sensor pressure plate']),indent=2))
for src in [S,M5]:
 for line in (src/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,(src.name,n)
print('ALL_SIX_ITEMS_ONE_PLATE_READBACK_PASS',report['estimated_time'],report['total_header_g'],flush=True)
