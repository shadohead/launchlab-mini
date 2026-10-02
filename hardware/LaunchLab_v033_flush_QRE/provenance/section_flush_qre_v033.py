"""Actual clamp and base solid sections with the unchanged PCB envelope."""
from pathlib import Path
import json
import cadquery as cq
import trimesh
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v033_flush_QRE'
P=json.loads((O/'parameters.json').read_text());x0,x1,y0,y1,z0,z1=P['PCB_box_mm'];x=(x0+x1)/2;y=P['sensor_screw_axes_xy_mm'][0][1]
def box(a):
    x0,x1,y0,y1,z0,z1=a
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
slab=box([x-15,x+15,y-.2,y+.2,2,11])
shapes={'REF_section_base':cq.importers.importStep(str(O/'step/01_QRE_minimal_port.step')).val(),
        'REF_section_bar':cq.Shape.importBrep(str(O/'step/03_QRE_pressure_bar.brep')),
        'REF_section_PCB':box(P['PCB_box_mm'])}
checks={}
for name,s in shapes.items():
    s=s.intersect(slab);vs,fs=s.tessellate(.02,.07)
    m=trimesh.Trimesh([v.toTuple() for v in vs],fs,process=True)
    assert m.is_watertight and m.is_winding_consistent
    m.export(O/'references'/(name+'.stl'));checks[name]=dict(closed=True,components=len(m.split()),source='Actual delivered CAD' if name!='REF_section_PCB' else 'Unchanged nominal PCB envelope')
(O/'reports/section_readback.json').write_text(json.dumps(dict(status='PASS',references=checks),indent=2))
print('V033_REAL_SECTIONS_SAVED',flush=True)
