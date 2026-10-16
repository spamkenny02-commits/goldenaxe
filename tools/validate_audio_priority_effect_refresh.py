"""Compare original priority queue/restoration M1/R/cost/state across ownership flags."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct,collections
from actor_reference import ROOT
from audio_priority_effect_refresh import priority_effect_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=list(itertools.product([0,128]+list(range(0x90,0xad)),[0,1,127,255],[0x90,0x94,0xac],[0,1,127,128,255],[0,128,192],[0,128,192]))
 rom,folder=generate('priority',records,[9,0x10,0xe,0xf,0x130,0x160],0x81f8,'audio-priority-effect-refresh')
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefixrefresh_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_m1_fetches.restype=c.c_uint64;dll.gaw_prefix_refresh_before.restype=c.c_uint;dll.gaw_prefix_refresh_after.restype=c.c_uint;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];histogram=collections.Counter()
  def observe(f,r):
   if r[4]:done.append(f)
   n=dll.gaw_prefix_samples()
   if n==previous[0]:return
   assert n==previous[0]+1
   before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little');prediction=priority_effect_refresh(SOURCE,before);cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after()
   assert (cost,fetches,after)==(prediction['tstates'],prediction['m1_fetches'],prediction['state']),(region,case,records[case],cost,fetches,prediction['m1_fetches'])
   assert exitR==advance_refresh(entryR,fetches+1),(region,case,'R',entryR,exitR,fetches)
   checked[case]=struct.pack('<4I',cost,fetches,entryR,exitR)+hashlib.sha256(after).digest();histogram[fetches]+=1;previous[0]=n
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records));data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(records),M1_histogram=dict(histogram),raw_sha256=hashlib.sha256(data).hexdigest(),fixture_sha256=hashlib.sha256(rom.read_bytes()).hexdigest()));print(region,len(records),'original81F8 M1/R/cost/400byte state exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Unmodified original81F8/bank6 helpers/priority tables. Custom DI caller;read-only existing M1 counter andR observations. Requests0/80/all29 valid effects;priority0/1/127/255 andborrowed channel ownership/active flag boundaries compare raw M1,R,cost/all400 state bytes.','Ownership0/1/127/128/255 andDF30/DF60 inactive/active/bit6 contexts. Synthetic combinations;invalid request indices andstandalone8211 outside scope. Full channel/envelope/command/IRQ fetch composition remains open.','No full-load R prediction,native RNG replacement,actual PSG waveform orhardware/full progression proof.'])
 (ROOT/'analysis/audio_priority_effect_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
