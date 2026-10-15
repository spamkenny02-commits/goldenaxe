"""Validate implemented864F noise paths; retain unsupported commands explicitly."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from audio_noise_channel_cost import noise_channel_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-noise-channel-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer changed original trace'
  path=folder/f'{region}-live-envelope-records.bin';raw=path.read_bytes();assert len(raw)%824==0
  checked=0;unsupported=[];categories=collections.Counter();modes=collections.Counter();controls=collections.Counter()
  for n in range(0,len(raw),824):
   ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,n);offset=ix-0xde00
   assert offset==0xd0
   before=raw[n+24:n+424];after=raw[n+424:n+824]
   categories['new_note' if before[offset+10]==1 else 'held_note']+=1
   modes[str(before[offset+7])]+=1
   if before[offset+10]==1:
    pointer=int.from_bytes(before[offset+3:offset+5],'little');first=source[pointer] if pointer<0x8000 else source[0x18000+(pointer&0x3fff)]
    if first>=0xe0:controls[f'{first:02X}']+=1
   try:predicted=noise_channel_cost(source,before,offset,de_before)
   except NotImplementedError as error:
    reason=str(error);assert reason.startswith('Noise command '),('unmodeled memory access',reason)
    unsupported.append(dict(record=n//824,reason=reason,ix=ix,sequence_pointer=int.from_bytes(before[offset+3:offset+5],'little'),observed_tstates=cost,caller_unwind=bool(unwind)));continue
   assert bool(unwind)==predicted.get('unwind',False),(region,n//824,'caller unwind')
   assert de_after==predicted['de'],(region,n//824,'DE',de_after,predicted['de'])
   assert cost==predicted['tstates'],(region,n//824,cost,predicted['tstates'])
   assert after==predicted['state'],(region,n//824,'RAM')
   checked+=1
  assert checked>0 and checked+len(unsupported)==len(raw)//824
  rows.append(dict(region=region,captured_cases=len(raw)//824,validated_cases=checked,unsupported_command_cases=unsupported,categories=dict(categories),entry_envelope_modes=dict(modes),initial_control_commands=dict(controls),raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,checked,'noise channel state/cost matches;',len(unsupported),'unsupported command paths retained',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['validated_cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Actual controlled6D->96/full-mask paid route PAL/NTSC. Read-only original864F entry/reader continuation805C or full reader exit0205 observations;400 bytes and complete instruction cost predicted. All calls counted;unsupported noise commands retained with record,stream pointer and observed cost.','Complete source cycle arrays equal archivedv0179. Held-envelope modes/dependencies come from actual entry state includingDE. Passing supported calls is not complete noise sequencer coverage.','Noise commands other than F6/F7,whole reader/R-dependent controls/restoration8211,futureIRQ/loading prediction and full game progression remain open.'])
 (ROOT/'analysis/live_noise_channel_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
