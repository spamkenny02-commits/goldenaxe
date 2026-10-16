"""Compare live84C7 semantic M1 with opcode counts/R andunchanged source traces."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from audio_tone_channel_refresh import tone_channel_refresh
from source_rng_refresh import advance_refresh

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/tone-refresh-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json').read_text())
  raw=(folder/f'{region}-live-envelope-records.bin').read_bytes();assert len(raw)%824==0
  assert raw==(ROOT/f'validation/audio-tone-channel-live/6d-ff/{region}-live-envelope-records.bin').read_bytes(),'Prior state/cost capture changed'
  m1=(folder/f'{region}-live-envelope-m1-records.bin').read_bytes();assert len(m1)==len(raw)//824*12
  histogram=collections.Counter();channels=collections.Counter();pitch=collections.Counter();envelope=collections.Counter()
  for n in range(0,len(raw),824):
   ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,n);offset=ix-0xde00;assert offset in [0x40,0x70,0xa0,0x100,0x130,0x160]
   before=raw[n+24:n+424];after=raw[n+424:n+824];fetches,entryR,exitR=struct.unpack_from('<3I',m1,n//824*12)
   prediction=tone_channel_refresh(source,before,offset,de_before)
   assert (fetches,cost,de_after,bool(unwind),after)==(prediction['m1_fetches'],prediction['tstates'],prediction['de'],prediction['unwind'],prediction['state']),(region,n//824,'M1/state/cost',fetches,prediction['m1_fetches'])
   assert exitR==advance_refresh(entryR,fetches),(region,n//824,'live R')
   histogram[fetches]+=1;channels[f'{ix:04X}']+=1;pitch[str(before[offset+6])]+=1;envelope[str(before[offset+7])]+=1
  rows.append(dict(region=region,cases=len(raw)//824,M1_histogram=dict(histogram),channels=dict(channels),pitch_modes=dict(pitch),envelope_modes=dict(envelope),state_cost_sha256=hashlib.sha256(raw).hexdigest(),M1_R_sha256=hashlib.sha256(m1).hexdigest()));print(region,len(raw)//824,'live tone M1/R/cost/state/DE exact;prior state records andsource cycle traces unchanged',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled6D->96/full-mask paid exit PAL/NTSC. Read-only live84C7 opcode/R observer;old824-byte state/cost records byte-identical andsource cycles identical to v0179. All captured tone calls predicted without unsupported skips.','Observed channel/pitch/envelope modes reported;live route only pitch0. R at helper entry is still observed,not predicted from16D0;helper R delta follows independently composed M1 count.','Other routes/contexts,noise/whole reader/IRQ fetch composition,unsupported commands/restoration,load-entry R/native RNG replacement,waveform/hardware/full progression remain open.'])
 (ROOT/'analysis/live_tone_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
