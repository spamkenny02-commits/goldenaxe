"""Compare semantic prefix M1 counts with original opcode-fetch events and R."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct,collections
from actor_reference import ROOT
from audio_prefix_refresh import tempo_refresh,fade_refresh,stop_refresh,arbitration_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,rows as prefix_rows,SOURCE
from run_core import run

def main():
 requests=[]
 for slot,value,priority in itertools.product(range(3),range(256),[0,1,15,127,128,255]):
  r=[0,0,0,priority,128];r[slot]=value;requests.append(tuple(r))
 for music,effect1,effect2,priority in itertools.product(list(range(0x81,0x8e))+[0xb0],range(0x90,0xad),range(0x90,0xad),[0,1]):requests.append((music,effect1,effect2,priority,128))
 requests=list(dict.fromkeys(requests))
 specs=[('tempo',prefix_rows('tempo'),None,0x807e,tempo_refresh),('fade',prefix_rows('fade'),None,0x80c8,fade_refresh),('stop',[()],[],0x83ef,stop_refresh),('arbitration',requests,[6,7,8,0x11,5],0x8097,lambda r:arbitration_refresh(SOURCE,r))]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefixrefresh_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_m1_fetches.restype=c.c_uint64;dll.gaw_prefix_refresh_before.restype=c.c_uint;dll.gaw_prefix_refresh_after.restype=c.c_uint;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 results=[]
 for kind,records,offsets,address,model in specs:
  rom,folder=generate(kind,records,offsets,address,'audio-prefix-refresh')
  for region in ['auto','pal']:
   dll.gaw_timing_reset();previous=[0];checked={};done=[];histogram=collections.Counter()
   def observe(f,r):
    if r[4]:done.append(f)
    n=dll.gaw_prefix_samples()
    if n==previous[0]:return
    assert n==previous[0]+1
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little');prediction=model(before);cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after()
    assert (cost,fetches,after)==(prediction['tstates'],prediction['m1_fetches'],prediction['state']),(kind,region,case,cost,fetches,prediction['m1_fetches'])
    assert exitR==advance_refresh(entryR,fetches+1),(kind,region,case,'R',entryR,exitR,fetches)
    checked[case]=struct.pack('<4I',cost,fetches,entryR,exitR)+hashlib.sha256(after).digest();histogram[fetches]+=1;previous[0]=n
   with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   assert done and len(checked)==len(records),(kind,region,len(checked),len(records));data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
   results.append(dict(kind=kind,region=region,cases=len(records),M1_histogram=dict(histogram),raw_sha256=hashlib.sha256(data).hexdigest(),fixture_sha256=hashlib.sha256(rom.read_bytes()).hexdigest()))
   print(kind,region,len(records),'original M1/R/cost/400byte state exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in results),rows=results,production_ROM_changed=False,full_game_ported=False,limits=['Unmodified original bank6 tempo/fade/stop/arbitration andpriority table. Read-only counter follows each existing R++ and optimized-loop R increment; CPU state/cycles unchanged. Raw M1 counts,logical R delta,cost andall400 sound bytes verified under DI.','Tempo counters/reloads,fade counters/four volumes,stop LDIR/OTIR,request/priority orders/boundaries covered. Some request/volume/priority values are synthetic. Not full reader refresh coverage:dispatch,channels andIRQ wrapper remain open.','Counter does not add hardware interrupt acknowledge increment missing from local core; isolated fixtures have no IRQ. Full load R prediction,native RNG replacement,PSG waveform andfull game not proved.'])
 (ROOT/'analysis/audio_prefix_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
