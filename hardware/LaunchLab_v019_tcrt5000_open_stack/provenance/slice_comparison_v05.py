"""Local-only Bambu CLI comparisons. Does not connect to a printer."""
from pathlib import Path
import subprocess,concurrent.futures,sys,json,math,re
R=Path(__file__).resolve().parents[1];P=R/'inspection/print_v05';B='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
def analyze(p,density):
 roles={};feature='';relative=True;e0=0.
 lines=p.read_text().splitlines()
 for line in lines:
  if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
  line=line.split(';')[0].strip()
  if line=='M82':relative=False
  if line=='M83':relative=True
  if line.startswith('G92 '):
   v=re.search(r'\bE([-+\d.]+)',line)
   if v:e0=float(v[1])
  if re.match(r'^G[0123] ',line):
   v=re.search(r'\bE([-+\d.]+)',line)
   if v:
    e=float(v[1]);delta=e if relative else e-e0;e0=e
    if delta>0 and re.search(r'\b[XY][-+\d.]',line):roles[feature]=roles.get(feature,0)+delta
 area=math.pi*(1.75/2)**2
 mass={k:v*area/1000*density for k,v in roles.items()}
 header='\n'.join(lines[:15]);weight=re.search(r'total filament weight \[g\] : ([\d.]+)',header)
 time=re.search(r'total estimated time: (.*)',header)
 return {'support_g':sum(v for k,v in mass.items() if k in ['Support','Support interface']),'support_base_g':mass.get('Support',0),'support_interface_g':mass.get('Support interface',0),'extrusion_by_feature_g':mass,'total_header_g':float(weight[1]) if weight else None,'estimated_time':time[1] if time else None}
def run(name,material='PLA',source=None,profile='process.json'):
 out=P/'slices'/f'{name}_{material}';out.mkdir(parents=True,exist_ok=True)
 source=source or P/'orientations'/f'{name}.stl'
 cmd=[B,'--datadir',str(P/'slicer_data'),'--load-settings',str(P/'profiles/machine.json')+';'+str(P/'profiles'/profile),'--load-filaments',str(P/'profiles'/f'{material}.json'),'--orient','0','--arrange','1','--slice','0','--export-3mf',f'{name}_{material}.3mf','--outputdir',str(out),str(source)]
 with (out/'slice.log').open('w') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=240)
 assert result.returncode==0,(name,result.returncode)
 gcode=out/'plate_1.gcode';report=analyze(gcode,1.24 if material=='PLA' else 1.27);report.update(name=name,material=material,source=str(source),project=str(out/f'{name}_{material}.3mf'),cli_exit=0)
 (out/'metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['name','material','support_g','total_header_g','estimated_time']}),flush=True);return report
if __name__=='__main__':
 names=sys.argv[1:] or ['upright','upside_down','front_on_bed','rear_on_bed','left_on_bed','right_on_bed']
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,names))
 (P/'orientation_slices.json').write_text(json.dumps(results,indent=2))
