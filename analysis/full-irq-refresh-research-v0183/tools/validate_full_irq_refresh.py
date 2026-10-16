"""Controlled original gated IRQ: independent nine-stage M1/R/state/cost checks."""
import contextlib,ctypes as c,hashlib,io,json,struct
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from full_irq_refresh import full_irq_refresh
from source_rng_refresh import advance_refresh
from irq_raster_phase import predict_palette_wait
from run_core import run

def check(source,raw,metadata,reader,context):
 points=struct.unpack_from('<12Q',raw);values=struct.unpack_from('<8I',raw,96)
 counts=struct.unpack_from('<10Q',metadata);refresh=struct.unpack_from('<10I',metadata,80);phase=struct.unpack_from('<8I',metadata,120)
 ix,de,finalde,a,cost,unwind=struct.unpack_from('<6I',reader)
 audio=reader_refresh(source,reader[24:424],de)
 assert not unwind and (cost,finalde,reader[424:824])==(audio['tstates'],audio['de'],audio['state']),(context,'reader')
 state=raw[128:464]
 prefix=full_irq_refresh(source,state,0,0 if state[0x33] else 1,*values[2:5],audio['tstates'],audio['m1_fetches'])
 polling=predict_palette_wait(phase,sum(list(prefix['stages'].values())[:4]),state[0x33],values[4])
 assert (polling['taken'],polling['exits'])==values[:2],(context,'palette')
 prediction=full_irq_refresh(source,state,polling['taken'],polling['exits'],*values[2:5],audio['tstates'],audio['m1_fetches'])
 times=[points[0]]+list(points[2:11]);expected=list(prediction['M1_stages'].values())
 assert [(b-a)//15 for a,b in zip(times,times[1:])]==list(prediction['stages'].values()),(context,'T')
 actual=[b-a for a,b in zip(counts,counts[1:])]
 assert actual==expected,(context,'M1',dict(zip(prediction['M1_stages'],zip(actual,expected))))
 assert list(refresh[1:])==[advance_refresh(r,n) for r,n in zip(refresh,expected)],(context,'R')
 assert raw[464:800]==prediction['state'],(context,'RAM')
 return prediction

def main():
 source=(ROOT/'input/original.sms').read_bytes();prior=json.loads((ROOT/'analysis/full_irq_unit_report.json').read_text())
 fixture=ROOT/'validation/full-irq-unit/full-irq/source.sms';assert hashlib.sha256(fixture.read_bytes()).hexdigest()==prior['fixture_sha256']
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_fullirqrefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_full_irq_records','gaw_full_irq_m1_events','gaw_live_envelope_events']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
 dll.gaw_full_irq_samples.restype=c.c_uint;dll.gaw_live_envelope_samples.restype=c.c_uint
 folder=ROOT/'validation/full-irq-refresh-unit';folder.mkdir(exist_ok=True);rows=[]
 for old in prior['rows']:
  region=old['region'];dll.gaw_timing_reset();previous=[0];retained=bytearray();m1=bytearray();done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   count=dll.gaw_full_irq_samples()
   if count!=previous[0]:
    assert count==previous[0]+1 and dll.gaw_live_envelope_samples()==count
    raw=c.string_at(dll.gaw_full_irq_records(),count*800)[-800:];metadata=c.string_at(dll.gaw_full_irq_m1_events(),count*152)[-152:];reader=c.string_at(dll.gaw_live_envelope_events(),count*824)[-824:]
    check(source,raw,metadata,reader,(region,count));retained.extend(raw);m1.extend(metadata);previous[0]=count
  with contextlib.redirect_stdout(io.StringIO()):run(fixture,old['cases']*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and previous[0]==old['cases'];assert hashlib.sha256(retained).hexdigest()==old['raw_sha256'],'Original state/cost trace changed'
  (folder/f'{region}-records.bin').write_bytes(retained);(folder/f'{region}-m1.bin').write_bytes(m1)
  rows.append(dict(region=region,cases=previous[0],M1_sha256=hashlib.sha256(m1).hexdigest()));print(region,previous[0],'full IRQ M1/R/states/cost exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),fixture_sha256=prior['fixture_sha256'],cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled empty queue/tile workload; original fixture unchanged. Nine stages to RET entry, not physical interrupt acknowledgement. Palette decisions independently predicted from entry raster. Final RET and vector outside this sidecar.'])
 (ROOT/'analysis/full_irq_refresh_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
