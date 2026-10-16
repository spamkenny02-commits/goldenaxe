"""Replay retained864F matrix andcompare composed M1/R/cost/state/DE/unwind."""
import contextlib,ctypes as c,hashlib,io,json,struct,collections
from actor_reference import ROOT
from audio_noise_channel_refresh import noise_channel_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import SOURCE
from run_core import run

def main():
 reference=json.loads((ROOT/'analysis/audio_noise_channel_cost_report.json').read_text());expected=reference['cases']//2
 image=(ROOT/'validation/audio-noise-channel/noise-channel/source.sms').read_bytes();assert hashlib.sha256(image).hexdigest()==reference['fixture_sha256'];assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 folder=ROOT/'validation/audio-noise-channel-refresh/noise';folder.mkdir(parents=True,exist_ok=True);rom=folder/'source.sms'
 if rom.exists():assert rom.read_bytes()==image
 else:rom.write_bytes(image)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_prefix_samples','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
 dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_m1_fetches.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];histogram=collections.Counter()
  def observe(f,r):
   if r[4]:done.append(f)
   n=dll.gaw_prefix_samples()
   if n==previous[0]:return
   assert n==previous[0]+1
   before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little');prediction=noise_channel_refresh(image,before,offset=0xd0,de=0x8a0b)
   cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after();de=dll.gaw_envelope_return_de();unwind=bool(dll.gaw_envelope_did_unwind())
   assert (cost,fetches,de,unwind,after)==(prediction['tstates'],prediction['m1_fetches'],prediction['de'],prediction['unwind'],prediction['state']),(region,case,cost,fetches,prediction['m1_fetches'],de,unwind)
   assert exitR==advance_refresh(entryR,fetches+1)
   checked[case]=struct.pack('<6I',cost,fetches,entryR,exitR,de,unwind)+hashlib.sha256(after).digest();histogram[fetches]+=1;previous[0]=n
  with contextlib.redirect_stdout(io.StringIO()):run(rom,expected*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==expected,(region,len(checked),expected);data=b''.join(checked[n] for n in range(expected));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=expected,M1_histogram=dict(histogram),raw_sha256=hashlib.sha256(data).hexdigest()));print(region,expected,'original864F composed M1/R/cost/state/DE/unwind exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Exact previous noise fixture hash replayed;original864F/bank6 intact. Custom DI caller/fixed-ROM streams,IXDED0,DE8A0B. Noise-note/envelope M1 models composed with audited wrapper instructions. Raw M1,R,cost/all400 bytes,DE/unwind compare.','Notes/durations,flags,scale,counter,envelope0/1/128 plusF6/F7 control paths;synthetic boundary combinations,not natural reachability.','Other noise commands/contexts,whole reader/IRQ fetch composition,load-entry R/native RNG replacement/waveform/hardware/full progression remain open.'])
 (ROOT/'analysis/audio_noise_channel_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
