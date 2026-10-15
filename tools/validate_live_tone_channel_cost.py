"""Validate implemented84C7 paths;retain unsupported live command cases explicitly."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from audio_tone_channel_cost import tone_channel_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-tone-channel-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer changed original trace'
  path=folder/f'{region}-live-envelope-records.bin';raw=path.read_bytes();assert len(raw)%824==0
  checked=0;unsupported=[];channels=collections.Counter();pitch=collections.Counter();envelopes=collections.Counter();categories=collections.Counter()
  for n in range(0,len(raw),824):
   ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,n);offset=ix-0xde00
   assert offset in [0x40,0x70,0xa0,0x100,0x130,0x160]
   before=raw[n+24:n+424];after=raw[n+424:n+824]
   channels[f"{ix:04X}"]+=1;pitch[str(before[offset+6])]+=1;envelopes[str(before[offset+7])]+=1
   categories["new_note" if before[offset+10]==1 else "held_note"]+=1
   try:predicted=tone_channel_cost(source,before,offset,de_before)
   except NotImplementedError as error:
    reason=str(error);assert reason.startswith('Command '),('unmodeled memory access',reason)
    unsupported.append(dict(record=n//824,reason=reason,ix=ix,sequence_pointer=int.from_bytes(before[offset+3:offset+5],'little'),observed_tstates=cost,caller_unwind=bool(unwind)));continue
   assert bool(unwind)==predicted.get('unwind',False),(region,n//824,'caller unwind')
   assert de_after==predicted['de'],(region,n//824,'DE',de_after,predicted['de'])
   assert cost==predicted['tstates'],(region,n//824,cost,predicted['tstates'])
   assert after==predicted['state'],(region,n//824,'RAM')
   checked+=1
  assert checked>0 and checked+len(unsupported)==len(raw)//824
  rows.append(dict(region=region,captured_cases=len(raw)//824,validated_cases=checked,unsupported_command_cases=unsupported,channel_calls=dict(channels),pitch_modes=dict(pitch),envelope_modes=dict(envelopes),categories=dict(categories),raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,checked,'tone channel state/cost matches;',len(unsupported),'unsupported command paths retained',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['validated_cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled6D->96/full-mask paid route PAL/NTSC;read-only84C7 entry and six reader continuations plus0205.400-byte state/complete instruction costs asserted with explicit actualDE. All calls counted,unsupported controls retained explicitly.','Complete source cycle arrays identical to archivedv0179. This route does not exercise all pitch/envelope/command combinations.','R-dependent sequencer commands,restoration8211,whole reader/futureIRQ/load timing and natural progression remain open.'])
 (ROOT/'analysis/live_tone_channel_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
