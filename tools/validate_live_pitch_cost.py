"""Predict original82C5 pitch calls during actual controlled paid exit."""
import hashlib,json,struct
from actor_reference import ROOT
from audio_pitch_cost import pitch_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-pitch-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer altered original trace'
  path=folder/f'{region}-live-envelope-records.bin';raw=path.read_bytes();assert len(raw)%824==0
  counts={};unwinds=0
  for n in range(0,len(raw),824):
   ix,de_before,de_after,hl,cost,unwind=struct.unpack_from('<6I',raw,n);offset=ix-0xde00
   assert offset in [0x40,0x70,0xa0,0xd0,0x100,0x130,0x160]
   before=raw[n+24:n+424];after=raw[n+424:n+824];predicted=pitch_cost(source,before,offset,0x8507)
   assert (cost,hl,bool(unwind))==(predicted['tstates'],predicted['hl'],predicted['unwind']),(region,n//824,hex(ix),before[offset+6],cost,hl,predicted)
   assert after==predicted['state'],(region,n//824,'RAM')
   mode=str(before[offset+6]);counts[mode]=counts.get(mode,0)+1;unwinds+=unwind
  assert len(raw)//824>0,'No original pitch calls captured'
  rows.append(dict(region=region,cases=len(raw)//824,pitch_modes=counts,caller_unwind_cases=unwinds,raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,len(raw)//824,'live pitch cost/state/HL exact;',counts,flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled actual6D->96/full-mask route,PAL/NTSC,original82C5/read-only observations. Independent cost,400-byte state and returnedHL comparisons. Complete original cycle arrays identical to archivedv0179.','Only recorded modes/phase states are covered live;isolated suite supplies signed vibrato/wrap and additional table cases. Caller unwind81/82 is modeled but not encountered in original pitch streams in these suites.','Sequencer/full channel/reader region gating and futureIRQ/load prediction,native audio waveforms and full natural progression remain open.'])
 (ROOT/'analysis/live_pitch_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
