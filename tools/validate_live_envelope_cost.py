"""Predict original envelope work during actual paid-exit gameplay."""
import hashlib,json,struct
from actor_reference import ROOT
from audio_adsr_cost import adsr_cost
from audio_table_envelope_cost import table_envelope_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-envelope-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  path=folder/f'{region}-live-envelope-records.bin';raw=path.read_bytes();assert len(raw)%824==0
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer changed original trace'
  counts={};unwinds=0;adsr=0
  for n in range(0,len(raw),824):
   ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,n)
   offset=ix-0xde00;assert offset in [0x40,0x70,0xa0,0xd0,0x100,0x130,0x160]
   before=raw[n+24:n+424];after=raw[n+424:n+824];mode=before[offset+7]
   if mode&128:predicted=adsr_cost(before,offset);assert not unwind;adsr+=1
   else:
    predicted=table_envelope_cost(source,before,offset,de_before)
    assert (de_after,bool(unwind))==(predicted['de'],predicted['unwind']),(region,n//824,'DE/unwind')
   assert cost==predicted['tstates'],(region,n//824,hex(ix),mode,cost,predicted['tstates'])
   assert after==predicted['state'] and a==predicted['accumulator'],(region,n//824,hex(ix),mode,'RAM/A',a,predicted['accumulator'])
   counts[str(mode)]=counts.get(str(mode),0)+1;unwinds+=unwind
  assert len(raw)//824>1000 and unwinds>0,(region,len(raw)//824,unwinds)
  rows.append(dict(region=region,cases=len(raw)//824,envelope_modes=counts,ADSR_cases=adsr,caller_unwind_cases=unwinds,raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,len(raw)//824,'live envelope cost/state/A exact;',unwinds,'caller unwinds;',adsr,'ADSR calls',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled actual6D->96/full-mask paid route,original854B/return paths observed read-only. Cost,all400 audio RAM bytes,returnedA and table DE/caller unwinding predicted independently per call. Complete original cycle arrays identical to archivedv0179.','Only modes actually encountered are covered live;ADSR and all16 table streams covered separately by explicit fixtures. Mode9 control83 depends on DE;arbitrary RAM reads and full progression are not validated.','Pitch,sequence/channel processing and reader entry/region gating still need cost prediction. PSG waveforms,full future IRQ/load scheduling and whole faithful port remain unproved.'])
 (ROOT/'analysis/live_envelope_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
