"""Exercise original audio-only wrapper with balanced synthetic interrupt frame."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from audio_irq_wrapper_refresh import audio_irq_wrapper_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=list(itertools.product(range(256),[0,1,127,128,255],[0,1],[0,5,255]))
 rom,folder=generate('wrapper',records,[0x20,0xa,3,4],0x3040,'audio-irq-refresh-unit')
 image=bytearray(rom.read_bytes());image[0x3430:0x3430+400]=bytes(400);image[0x3430+5]=128
 #PUSH AF models the vector save;JP0137 leaves caller's return beneath it.
 stub=bytes.fromhex('3a20de3230c0f5c33701');image[0x3040:0x3040+len(stub)]=stub;rom.write_bytes(image)
 assert image[0x137:0x227]==SOURCE[0x137:0x227] and image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_prefix_samples','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
 dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_m1_fetches.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];branches=[0,0]
  def observe(f,r):
   if r[4]:done.append(f)
   n=dll.gaw_prefix_samples()
   if n==previous[0]:return
   assert n==previous[0]+1
   before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little');timer=before[0x20]
   reader=reader_refresh(image,before);wrapper=audio_irq_wrapper_refresh(timer!=0)
   cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after()
   expected_cost=47+wrapper['to_return_excluding_reader']+reader['tstates']+wrapper['return_instruction']
   expected_M1=4+wrapper['to_return_excluding_reader_M1']+reader['m1_fetches']+wrapper['return_instruction_M1']
   assert (cost,fetches,after)==(expected_cost,expected_M1,reader['state']),(region,case,records[case],cost,fetches,expected_cost,expected_M1)
   assert exitR==advance_refresh(entryR,fetches+1) and r[0x30]==max(timer-1,0) and r[0x2e]==r[0x2f]==0 and r[0x1fff]==6
   checked[case]=struct.pack('<5I',cost,fetches,entryR,exitR,r[0x30])+hashlib.sha256(after).digest();branches[timer!=0]+=1;previous[0]=n
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records);data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(records),zero_timer_cases=branches[0],nonzero_timer_cases=branches[1],raw_sha256=hashlib.sha256(data).hexdigest()));print(region,len(records),'original0137..0226 M1/R/cost/audio/timer exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Original0137..0226/bank6 intact. Synthetic balancedPUSHAF/JP caller underVINT-disabled video;not actual interrupt acceptance. All256 C030 counters,five pause values/two compensation flags/three phases. Stub47T/4M1 explicitly excluded from wrapper accounting.','Read-only M1/R/cost/all400 audio/timer andclock/gate/bank restoration compare;inactive channels when reader proceeds. Vector38..42 andhardware acknowledge require separate live checks.','No fullIRQ handler/foreground M1 composition,load-entry R/native RNG replacement,waveform/hardware/full progression proof.'])
 (ROOT/'analysis/audio_irq_refresh_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
