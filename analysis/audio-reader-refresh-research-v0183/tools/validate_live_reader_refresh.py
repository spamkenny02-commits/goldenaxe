"""Check complete8000 M1/R/cost/state/DE against unchanged paid-exit captures."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from source_rng_refresh import advance_refresh

def main():
 source=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/reader-refresh-live/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
    raw=(folder/f'{region}-live-envelope-records.bin').read_bytes();assert len(raw)%824==0
    baseline=ROOT/f'validation/wait-raster/{town:02x}-{mask:02x}/{region}-live-envelope-records.bin';assert raw==baseline.read_bytes(),'Prior reader state/cost capture changed'
    m1=(folder/f'{region}-live-envelope-m1-records.bin').read_bytes();assert len(m1)==len(raw)//824*12
    events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());pairs=[];pending=None;returns=collections.Counter()
    for event in events:
     if event[1] in [0x1a2,0x202]:assert pending is None;pending=event
     elif event[1] in [0x1a5,0x205]:
      assert pending is not None and event[1]==pending[1]+3;pairs.append((event[2]-pending[2])//15-17);returns[f'{event[1]:04X}']+=1;pending=None
    assert pending is None and len(pairs)==len(raw)//824
    histogram=collections.Counter();channels=collections.Counter();gates=collections.Counter()
    for n in range(0,len(raw),824):
     ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,n);before=raw[n+24:n+424];after=raw[n+424:n+824];fetches,entryR,exitR=struct.unpack_from('<3I',m1,n//824*12)
     prediction=reader_refresh(source,before,de_before)
     assert not unwind and (fetches,cost,de_after,after)==(prediction['m1_fetches'],prediction['tstates'],prediction['de'],prediction['state']),(town,mask,region,n//824,'M1/state/cost',fetches,prediction['m1_fetches'])
     assert cost==pairs[n//824] and exitR==advance_refresh(entryR,fetches),(town,mask,region,n//824,'IRQ cost/live R')
     histogram[fetches]+=1;channels[sum(bool(before[o]&128) for o in [0x40,0x70,0xa0,0xd0,0x100,0x130,0x160])]+=1;gates[before[0xa]]+=1
    rows.append(dict(town=town,target=target,mask=mask,region=region,cases=len(raw)//824,M1_histogram=dict(histogram),entry_active_channels=dict(channels),entry_gate=dict(gates),return_sites=dict(returns),state_cost_sha256=hashlib.sha256(raw).hexdigest(),M1_R_sha256=hashlib.sha256(m1).hexdigest()));print(f'{town:02X}/{mask:02X}',region,len(raw)//824,'full reader M1/R/cost/state/DE exact;prior captures/sourcecycles unchanged',flush=True)
 assert rows
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=len(rows),reader_calls=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled paid exits,six routes/two masks/PAL/NTSC. Read-only8000 M1/R observer;old824-byte state/cost records byte-identical andcomplete sourcecycles identical to v0179. All captured reader calls predicted without unsupported skips;both IRQ return sites asserted.','Complete supported8000 composition includes priorities,tempo,fade,dispatch,priority effect,gate/compensation andallactive channels. Entry R remains observed;future helper R delta is independently composed,not full16D0 refresh propagation.','Other contexts,unsupported R-based/restoration/noise commands,IRQ wrapper/foreground fetch composition,load-entry R/native RNG replacement,waveform/hardware/full progression remain open.'])
 (ROOT/'analysis/live_audio_reader_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
