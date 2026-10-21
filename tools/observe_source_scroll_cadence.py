"""Read-only source vertical scroll completion cadence, restored after build."""
import contextlib,ctypes as c,io,json,subprocess,sys
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_sprite_scene_timed import sha
OBSERVER=r'''
static unsigned gaw_scroll_events[4096][4],gaw_scroll_count_value,gaw_scroll_enabled,gaw_scroll_errors;
__declspec(dllexport) void gaw_scroll_reset(unsigned enabled) {gaw_scroll_count_value=gaw_scroll_errors=0;gaw_scroll_enabled=enabled;}
__declspec(dllexport) unsigned gaw_scroll_count(void) {return gaw_scroll_count_value;}
__declspec(dllexport) unsigned gaw_scroll_error(void) {return gaw_scroll_errors;}
__declspec(dllexport) const unsigned *gaw_scroll_data(void) {return &gaw_scroll_events[0][0];}
static void gaw_scroll_observe(unsigned pc) {
 unsigned *p;if(!gaw_scroll_enabled || (pc!=0x20ca && pc!=0x20d0 && pc!=0x208a && pc!=0x2090)) return;
 if(gaw_scroll_count_value==4096) {gaw_scroll_errors++;return;}
 p=gaw_scroll_events[gaw_scroll_count_value++];p[0]=pc;p[1]=Z80.cycles;p[2]=Z80.bc.w.l>>8;p[3]=v_counter;
}
'''
def main():
 folder=ROOT/'validation/sms-scroll-cadence';folder.mkdir(exist_ok=True);engine=ROOT.parents[1]/'work/genesis-plus-gx';path=engine/'core/z80/z80.c';original=path.read_bytes();s=original.decode().replace('\r\n','\n');anchor='void z80_run(unsigned int cycles)';assert s.count(anchor)==1;s=s.replace(anchor,OBSERVER+'\n'+anchor,1);anchor='gaw_timing_observe(pc);EXEC_INLINE(op,ROP());';assert s.count(anchor)==1;s=s.replace(anchor,'gaw_scroll_observe(pc);'+anchor,1);modified=s.encode()
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_scroll_cadence_libretro.dll'],capture_output=True,text=True,cwd=ROOT);(folder/'build.log').write_text(result.stdout+result.stderr);assert not result.returncode,result.stdout+result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original;(folder/'original.snapshot').write_bytes(original);(folder/'modified.snapshot').write_bytes(modified);core=engine/'genesis_plus_gx_scroll_cadence_libretro.dll';(folder/'observer.dll').write_bytes(core.read_bytes());dll=c.CDLL(str(core));dll.gaw_scroll_reset.argtypes=[c.c_uint];dll.gaw_scroll_count.restype=dll.gaw_scroll_error.restype=c.c_uint;dll.gaw_scroll_data.restype=c.POINTER(c.c_uint);results=[]
 for region in ['auto','pal']:
  dll.gaw_scroll_reset(0);events=[]
  def ram(f,r):
   assert not dll.gaw_scroll_error();p=dll.gaw_scroll_data();events.extend([[f,*[int(p[n*4+k]) for k in range(4)]] for n in range(dll.gaw_scroll_count())]);dll.gaw_scroll_reset(int(f>=2700))
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3450,folder/region,set(),[(200,220,0)]+PRESSES[:11]+[(3000,3060,5),(3220,3360,4)],core=core,ram_observer=ram,core_options={'genesis_plus_gx_region_detect':region})
  (folder/(region+'-events.json')).write_text(json.dumps(events)+'\n');groups=[]
  for f,pc,cycles,b,line in events:
   if pc in [0x20ca,0x208a] and b==20:groups.append(dict(direction=1 if pc==0x20ca else 0,steps=[]))
   if pc in [0x20d0,0x2090]:groups[-1]['steps'].append(dict(step=21-b,frame=f,cycles=cycles,line=line))
  assert len(groups)==2 and all([r['step'] for r in g['steps']]==list(range(1,21)) for g in groups),groups
  for g in groups:g['frame_intervals']=[b['frame']-a['frame'] for a,b in zip(g['steps'],g['steps'][1:])]
  results.append(dict(region=region,scrolls=groups));print(region,[(g['direction'],g['steps'][0]['frame'],g['frame_intervals']) for g in groups],flush=True)
 (ROOT/'analysis/source_scroll_cadence_report.json').write_text(json.dumps(dict(original_source_sha256=sha(original),observer_source_sha256=sha(modified),observer_core_sha256=sha(core.read_bytes()),restored=True,results=results,limits=['Unchanged original ROM on natural controller route. Read-only20D0/2090 completion boundaries identify B20..1 vertical20step loop. Cadence of map-copy completion, not full pixel or absolute boot fidelity.']),indent=2)+'\n')
if __name__=='__main__':main()
