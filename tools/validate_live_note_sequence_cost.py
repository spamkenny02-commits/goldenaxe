"""Validate implemented8357 paths;retain unsupported live command cases explicitly."""
import hashlib,json,struct
from actor_reference import ROOT
from audio_note_sequence_cost import note_sequence_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-note-sequence-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer changed original trace'
  path=folder/f'{region}-live-envelope-records.bin';raw=path.read_bytes();assert len(raw)%824==0
  checked=0;unsupported=[]
  for n in range(0,len(raw),824):
   ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,n);offset=ix-0xde00
   assert offset in [0x40,0x70,0xa0,0x100,0x130,0x160]
   before=raw[n+24:n+424];after=raw[n+424:n+824]
   try:predicted=note_sequence_cost(source,before,offset)
   except NotImplementedError as error:
    reason=str(error);assert reason.startswith('Command '),('unmodeled memory access',reason)
    unsupported.append(dict(record=n//824,reason=reason,ix=ix,sequence_pointer=int.from_bytes(before[offset+3:offset+5],'little'),observed_tstates=cost,caller_unwind=bool(unwind)));continue
   assert bool(unwind)==predicted.get('unwind',False),(region,n//824,'caller unwind')
   assert cost==predicted['tstates'],(region,n//824,cost,predicted['tstates'])
   assert after==predicted['state'],(region,n//824,'RAM')
   checked+=1
  assert checked>0 and checked+len(unsupported)==len(raw)//824
  rows.append(dict(region=region,captured_cases=len(raw)//824,validated_cases=checked,unsupported_command_cases=unsupported,raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,checked,'note/control state/cost matches;',len(unsupported),'unsupported command paths retained',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['validated_cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Actual controlled6D->96/full-mask paid route,PAL/NTSC. Original8357 calls observed read-only. Implemented notes/rest/raw/E7/F7/F8/F9 and F1/F2 termination with DE0E=0 paths are asserted against400-byte state/cost predictions;unsupported commands retained with record number,stream pointer and observed cost.','Every captured call remains in raw824-byte records;complete source cycle arrays equal archivedv0179. Passing supported cases is not complete sequencer coverage. Noise864F,F1/F2 restoration8211 (DE0E!=0),remaining commands,whole channel/reader region gating and futureIRQ/load prediction remain open.'])
 (ROOT/'analysis/live_note_sequence_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
