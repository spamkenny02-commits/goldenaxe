"""Execute original82C5 andcheck M1/R/state/HL/cost including positive unwinds."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct,collections
from actor_reference import ROOT
from audio_pitch_refresh import pitch_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def fixtures():
 records=[]
 def row(mode,base,delta,delay,rate,step,phase,flags=0):return (mode,base&255,base>>8,delta&255,delta>>8,delay,rate,step,phase,0xc0,0x8a,flags)
 for mode,base,delta,delay,rate,step,phase in itertools.product([128,255],[0,1,255,256,1023,32767,32768,65535],[0,1,255,256,32767,32768,65535],[0,1,2,255],[0,1,2,255],[128,129,255,0,1,127],[0,1,2,255]):records.append(row(mode,base,delta,delay,rate,step,phase))
 for mode,index,base,flags in itertools.product(range(1,9),range(256),[0x8ab8,0x8a61],[0,4,32,255]):records.append(row(mode,base,0,1,index,0,1,flags))
 for base in [0,1,255,256,1023,32767,32768,65535]:records.append(row(0,base,65535,0,0,128,0))
 for table,delay,rate,phase,step in itertools.product([0xde40,0xfe40,0xdf70,0xff70],[0,1,2],[0,1,2],[0,1,2],[128,255,0,127]):
  record=list(row(128,0x8ab8,0xff80,delay,rate,step,phase));record[9:11]=[table&255,table>>8];records.append(tuple(record))
 records=list(dict.fromkeys(records));ordinary=len(records)
 #Additional synthetic modes point through unchanged ROM words to81/82.
 #They exercise original unwind instructions; not claimed to be valid game modes.
 read=lambda a:SOURCE[a] if a<0x8000 else SOURCE[0x18000+(a&0x3fff)]
 stops={}
 for mode in range(9,128):
  p=0x8a52+(mode-1)*2;table=read(p)|(read(p+1)<<8)
  if table>=0xc000:continue
  for index in range(256):
   address=(table+index)&65535
   if address>=0xc000:continue
   value=read(address)
   if value in [0x81,0x82] and value not in stops:stops[value]=dict(mode=mode,index=index,table=table)
  if len(stops)==2:break
 assert set(stops)=={0x81,0x82}
 for stop in stops.values():
  for base,flags in itertools.product([0x8ab8,0x8a61],[0,4,32,255]):records.append(row(stop['mode'],base,0,1,stop['index'],0,1,flags))
 return records,ordinary,stops

def main():
 records,ordinary,stops=fixtures()
 rom,folder=generate('pitch',records,[0x46,0x4b,0x4c,0x52,0x53,0x54,0x55,0x56,0x57,0x50,0x51,0x40],0x82c5,'audio-pitch-refresh',0xde40,True)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_pitchrefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_prefix_samples','gaw_pitch_return_hl','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
 dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_m1_fetches.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];histogram=collections.Counter();unwinds=[0]
  def observe(f,r):
   if r[4]:done.append(f)
   n=dll.gaw_prefix_samples()
   if n==previous[0]:return
   assert n==previous[0]+1
   before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little');prediction=pitch_refresh(SOURCE,before,return_address=0x3003,de=0xdf90)
   cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after();hl=dll.gaw_pitch_return_hl();unwind=bool(dll.gaw_envelope_did_unwind())
   assert (cost,fetches,hl,unwind,after)==(prediction['tstates'],prediction['m1_fetches'],prediction['hl'],prediction['unwind'],prediction['state']),(region,case,records[case],cost,fetches,prediction['m1_fetches'],hl,unwind)
   if 'de' in prediction:assert dll.gaw_envelope_return_de()==prediction['de'],(region,case,'DE')
   assert exitR==advance_refresh(entryR,fetches+1),(region,case,'R',entryR,exitR,fetches)
   checked[case]=struct.pack('<7I',cost,fetches,entryR,exitR,hl,dll.gaw_envelope_return_de(),unwind)+hashlib.sha256(after).digest();histogram[fetches]+=1;unwinds[0]+=unwind;previous[0]=n
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records) and unwinds[0]==len(records)-ordinary,(region,len(checked),len(records),unwinds[0])
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(records),caller_unwind_cases=unwinds[0],M1_histogram=dict(histogram),raw_sha256=hashlib.sha256(data).hexdigest(),fixture_sha256=hashlib.sha256(rom.read_bytes()).hexdigest()));print(region,len(records),'original82C5 M1/R/cost/state/HL/unwind exact;',unwinds[0],'unwinds',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,synthetic_unwind_modes=stops,production_ROM_changed=False,full_game_ported=False,limits=['Unmodified original82C5/allbank6 andtables. Custom two-level DI caller,IXDE40,entryDE=DF90. Absolute M1,R,cost/all400 state bytes,HL/DE/unwind compared for every case.','Two high-bit vibrato modes/base/signed delta/delay/rate/phase/step boundaries;all8 pitch tables/all256 indices/two ROM bases/four flags;zero mode and432 mirrored modulation-table cases. Dimensions sampled,not full Cartesian;some indices/base/counter inputs synthetic.','Positive81/82 unwind probes use synthetic modes beyond valid1..8 pointing through existing ROM words to fixed-ROM bytes. They verify source unwind code,not occurrence in natural music. No complete channel/sequence/IRQ fetch composition,full-load R/native RNG replacement,waveform/hardware/full progression proof.'])
 (ROOT/'analysis/audio_pitch_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
