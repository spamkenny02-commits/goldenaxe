"""Read-only 68000 entry/return timing on natural vertical screen transitions."""
import contextlib,ctypes as c,hashlib,io,json,re,subprocess
from pathlib import Path
from run_core import run
from validate_actor_tick import PRESSES
ROOT=Path(__file__).resolve().parents[1]

def main():
 symbols={m[2]:int(m[1],16) for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 watched={};functions={}
 for prefix in ['sound_tick.','step_room_transition.','flushQueue','VDP_setTileMapDataRect.constprop.']:
  for name,address in symbols.items():
   if not name.startswith(prefix):continue
   dump=subprocess.check_output([str(ROOT.parents[1]/'work/sgdk/bin/objdump.exe'),'-d','--disassemble='+name,str(ROOT/'megadrive/out/release/rom.out')],text=True)
   returns=[int(m[1],16) for l in dump.splitlines() if(m:=re.match(r'\s*([0-9a-fA-F]+):.*\trts\s*$',l))]
   if not returns:continue
   functions[name]=dict(entry=address,returns=returns);watched[address]=name+':entry'
   for p in returns:watched[p]=name+':return'
 assert 0<len(watched)<=32,len(watched)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll';dll=c.CDLL(str(core));dll.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)];dll.gaw_md_event_count.restype=c.c_uint;dll.gaw_md_event_data.restype=c.POINTER(c.c_uint)
 outcomes=[]
 for region,lines in [('auto',262),('pal',313)]:
  pcs=(c.c_uint*len(watched))(*watched);dll.gaw_md_config(len(watched),pcs);previous=[0];events=[];states=[]
  def observe(f,r):
   if f<3000:
    dll.gaw_md_config(len(watched),pcs);previous[0]=0;return
   count=dll.gaw_md_event_count();p=dll.gaw_md_event_data()
   assert count<8192,'Observer buffer full'
   for n in range(previous[0],count):
    pc,cycles,sp=[int(p[n*3+k]) for k in range(3)];events.append(dict(frame=f,pc=pc,event=watched[pc],master_in_frame=cycles,absolute_master=(f-1)*lines*3420+cycles,sp=sp))
   previous[0]=count
   def word(name):
    key=next(k for k in symbols if k.split('.lto_priv.')[0]==name);a=symbols[key]&65535;return int.from_bytes(bytes(r[(a+i)^1] for i in range(2)),'big')
   states.append(dict(frame=f,stage=word('transition_stage'),step=word('transition_step'),direction=word('transition_direction'),state=word('game_state')))
  folder=ROOT/f'validation/vertical-publication-profile-{region}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',3280,folder,set(),PRESSES[:11]+[(3000,3060,5),(3220,3360,4)],core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  pending={};spans=[]
  for e in events:
   name,phase=e['event'].rsplit(':',1);key=(name,e['sp'])
   # At RTS the saved register/stack frame has already been unwound.
   # Function entry and its RTS therefore have the same SP.
   if phase=='entry':pending[key]=e
   elif key in pending:
    a=pending.pop(key);elapsed=e['absolute_master']-a['absolute_master'];assert elapsed>=0,(a,e)
    spans.append(dict(function=name,entry_frame=a['frame'],exit_frame=e['frame'],start_master=a['master_in_frame'],end_master=e['master_in_frame'],elapsed_master=elapsed,elapsed_lines=round(elapsed/3420,3)))
  result=dict(region=region,functions=functions,events=events,spans=spans,states=states)
  outcomes.append(result)
  print(region,'max sound lines',max(s['elapsed_lines'] for s in spans if s['function'].startswith('sound_tick.')),flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),production_rom_unmodified=True,ram_injections=False,regions=outcomes,limits=['Read-only function entry/RTS observations; RTS instruction cost itself excluded. DMA and interrupt stalls inside a span are included, not attributed to individual instructions. Natural initial south/north routes only.'])
 (ROOT/'validation/vertical_publication_profile.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
