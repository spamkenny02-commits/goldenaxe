"""Validate composed8000 paths;retain unsupported live command cases explicitly."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from audio_reader_cost import reader_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-reader-complete-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer changed original trace'
  path=folder/f'{region}-live-envelope-records.bin';raw=path.read_bytes();assert len(raw)%824==0
  irq_events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());pairs=[];pending=None;returns=collections.Counter()
  for event in irq_events:
   if event[1] in [0x1a2,0x202]:assert pending is None;pending=event
   elif event[1] in [0x1a5,0x205]:
    assert pending is not None and event[1]==pending[1]+3
    pairs.append((event[2]-pending[2])//15-17);returns[f'{event[1]:04X}']+=1;pending=None
  assert pending is None and len(pairs)==len(raw)//824
  checked=0;unsupported=[]
  for n in range(0,len(raw),824):
   ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,n);offset=ix-0xde00
   assert cost==pairs[n//824],(region,n//824,'IRQ-call span differs')
   before=raw[n+24:n+424];after=raw[n+424:n+824]
   try:predicted=reader_cost(source,before,de_before)
   except NotImplementedError as error:
    reason=str(error);assert reason.startswith(('Command ','Noise command ','Priority ')),('unmodeled memory access',reason)
    unsupported.append(dict(record=n//824,reason=reason,ix=ix,sequence_pointer=int.from_bytes(before[offset+3:offset+5],'little'),observed_tstates=cost,caller_unwind=bool(unwind)));continue
   assert bool(unwind)==predicted.get('unwind',False),(region,n//824,'caller unwind')
   assert de_after==predicted['de'],(region,n//824,'DE',de_after,predicted['de'])
   assert cost==predicted['tstates'],(region,n//824,cost,predicted['tstates'])
   assert after==predicted['state'],(region,n//824,'RAM')
   checked+=1
  assert checked>0 and checked+len(unsupported)==len(raw)//824
  rows.append(dict(region=region,captured_cases=len(raw)//824,validated_cases=checked,unsupported_command_cases=unsupported,IRQ_reader_calls=len(pairs),return_sites=dict(returns),min_tstates=min(pairs),max_tstates=max(pairs),raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,checked,'full reader state/cost matches;',len(unsupported),'unsupported command paths retained',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['validated_cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled6D->96/full-mask paid route PAL/NTSC. Read-only8000 entry/0205-or-01A5 return records;independent complete reader instruction cost,400-byte state and returnedDE predictions. Unsupported commands retained explicitly;not silently ignored.','Complete source cycle arrays identical to archivedv0179. Includes original gating,priority/tempo/fade/dispatch/priority-effect queue and active channel work. One route is not exhaustive driver or natural progression coverage.','R-dependent sequencer commands,standalone8211/nonzero restoration paths,other noise commands/invalid dispatch indices,futureIRQ/loading integration and hardware remain open.'])
 (ROOT/'analysis/live_audio_reader_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
