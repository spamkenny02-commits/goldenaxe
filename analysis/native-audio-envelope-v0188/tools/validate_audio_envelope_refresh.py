"""Execute original envelope helpers and compare M1/R/cost/state/A/DE/unwind."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct,collections,sys
from actor_reference import ROOT
from audio_envelope_refresh import adsr_refresh,table_envelope_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def fixtures(table):
 if table:
  read=lambda a:SOURCE[0x18000+a-0x8000];pointers=[read(0x897f+i*2)|(read(0x8980+i*2)<<8) for i in range(16)]+[0x8a52];records=[]
  for mode in range(1,17):
   for index,flags,tone,de in itertools.product(range(pointers[mode]-pointers[mode-1]),[0,4,16,20,128,255],[128,160,192,224],[0x8a0b,0x899e,0x89a1]):records.append((mode,index,flags,tone,de&255,de>>8))
  for index,flags in itertools.product(range(256),[0,4]):records.append((0,index,flags,128,11,138))
  return records,[0x47,0x5f,0x40,0x41,0x3e,0x3f]
 records=[];steps=[0,1,15,16,127,128,254,255];bounds=steps
 for value,step,phase,flags in itertools.product(range(256),steps,[0,8,16,24,32,40,64,72],[0,4]):records.append((128,flags,128,phase,value,step,step,127,step,step))
 for value,step,phase,limit,flags in itertools.product(bounds,steps,[32,40],bounds,[0,4]):records.append((128,flags,128,phase,value,step,step,limit,step,step))
 for phase,value,step,flags,tone in itertools.product([0,8,16,32,64,112,255],bounds,steps,[0,4],[128,160,192,224]):records.append((255,flags,tone,phase,value,step,step,255,step,step))
 for phase,value in itertools.product(range(256),bounds):records.append((0,4,128,phase,value,0,0,0,0,0))
 return list(dict.fromkeys(records)),[0x47,0x40,0x41,0x5d,0x5f,0x60,0x61,0x62,0x63,0x64]

def main():
 table='--table' in sys.argv;kind='table' if table else 'adsr';records,offsets=fixtures(table)
 rom,folder=generate(kind,records,offsets,0x854b,'audio-envelope-refresh',0xde40,table,0xde3e)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_prefix_samples','gaw_envelope_return_a','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
 dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_m1_fetches.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];histogram=collections.Counter();unwinds=[0]
  def observe(f,r):
   if r[4]:done.append(f)
   n=dll.gaw_prefix_samples()
   if n==previous[0]:return
   assert n==previous[0]+1
   before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little');de=int.from_bytes(before[0x3e:0x40],'little')
   prediction=table_envelope_refresh(SOURCE,before,de=de) if table else adsr_refresh(before,de=de)
   cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after();a=dll.gaw_envelope_return_a();returned_de=dll.gaw_envelope_return_de();unwind=bool(dll.gaw_envelope_did_unwind())
   assert (cost,fetches,a,returned_de,unwind,after)==(prediction['tstates'],prediction['m1_fetches'],prediction['accumulator'],prediction['de'],prediction.get('unwind',False),prediction['state']),(kind,region,case,records[case],cost,fetches,prediction['m1_fetches'],a,returned_de,unwind)
   assert exitR==advance_refresh(entryR,fetches+1),(kind,region,case,'R',entryR,exitR,fetches)
   checked[case]=struct.pack('<7I',cost,fetches,entryR,exitR,a,returned_de,unwind)+hashlib.sha256(after).digest();histogram[fetches]+=1;unwinds[0]+=unwind;previous[0]=n
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(kind,region,len(checked),len(records));data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(records),caller_unwind_cases=unwinds[0],M1_histogram=dict(histogram),raw_sha256=hashlib.sha256(data).hexdigest(),fixture_sha256=hashlib.sha256(rom.read_bytes()).hexdigest()));print(kind,region,len(records),'original854B M1/R/cost/state/A/DE/unwind exact;',unwinds[0],'unwinds',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),kind=kind,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Unmodified original854B/8602/863E/bank6 tables. Custom DI caller andIXDE40;explicit DE input. Read-only absolute M1 counter,R,cost/all400 sound bytes,A/DE/unwind compare.','ADSR:all256 values,step/limit boundaries,phase/bounce/high-bit flags,termination ownership/four PSG types;dimensions not full Cartesian. Table:all16 tables/everyoffset,six channel flags,four PSG types/three DE inputs;zero mode separately.','Invalid table indices/arbitrary uncaptured RAM DE excluded. No complete channel/sequence/IRQ fetch composition orfull-load R prediction/native RNG replacement/waveform/hardware/full progression proof.'])
 (ROOT/'analysis'/('audio_table_envelope_refresh_report.json' if table else 'audio_adsr_refresh_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
