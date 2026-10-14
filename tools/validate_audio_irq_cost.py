"""Validate IRQ wrapper instruction costs; measure original reader workload."""
import hashlib,json
from actor_reference import ROOT
from audio_irq_wrapper_cost import audio_irq_wrapper_cost

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 source=(ROOT/'input/original.sms').read_bytes()
 assert source[0x137:0x13e]==bytes.fromhex('3a2ec0b7cae301')
 assert source[0x38:0x45]==bytes.fromhex('f5dbbfb7f25e02321bc0c33701')
 assert source[0x1e3:0x227]==bytes.fromhex('c5d5e508d9f5c5d5e5dde5fde53afffff53afcfff5e6f732fcff3e0632ffffcd00803a30c0b728043d3230c0f132fcfff132fffffde1dde1e1d1c1f1d908e1d1c1f1fbc9')
 rows=[];comparisons=0
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/audio-irq/{town:02x}-{mask:02x}'
   reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    path=folder/f'{region}-audio-irq-events.json';events=json.loads(path.read_text())
    cycle_path=folder/f'{region}-cycle-events.json';cycles=json.loads(cycle_path.read_text())
    assert cycles==json.loads((reference/f'{region}-cycle-events.json').read_text()),(town,mask,region,'observer changed source trace')
    entry=next(e for e in cycles if e[1]==0x16d0 and e[4]==target)
    end=next(e for e in cycles if e[1]==0xace and e[2]>entry[2] and e[4]==target)
    starts=[i for i,e in enumerate(events) if e[1]==0x137];audio=[];full=[];partial=0
    def ticks(a,b):
     delta=b[2]-a[2];assert delta>=0 and delta%15==0
     return delta//15
    for n,index in enumerate(starts):
     group=events[index:starts[n+1] if n+1<len(starts) else len(events)]
     a=group[0]
     expected=[0x137,0x1e3,0x202,0x205,0x226] if not a[5] else [0x137,0x1a2,0x1a5,0x1e2]
     if [e[1] for e in group]!=expected:
      assert n==len(starts)-1 and [e[1] for e in group]==expected[:len(group)],('unexpected IRQ sequence',town,mask,region,group)
      partial+=1;continue
     if not a[5]:
      gate,save,call,after,ret=group;cost=audio_irq_wrapper_cost(after[7]!=0)
      reader=ticks(call,after)-cost['audio_call']
      assert reader>0 and gate[4]==save[4] and call[4]==after[4] and ret[4]==gate[4]+2
      assert ticks(gate,save)==cost['gate']
      assert ticks(save,call)==cost['save_and_map']
      assert ticks(after,ret)==cost['delay']+cost['restore']
      assert ticks(gate,ret)==cost['to_return_excluding_reader']+reader
      assert all(e[5]==0 and e[6]==gate[6] for e in group),('audio-only clock changed',group)
      assert ret[7]==max(after[7]-1,0) and ret[13]==gate[13],('delay/bank restoration',group)
      comparisons+=6
      audio.append(dict(frame=a[0],start_master=a[2],return_master=ret[2],reader_tstates_observed=reader,wrapper_tstates_to_RET=cost['to_return_excluding_reader'],whole_IRQ_tstates=cost['interrupt_accept_and_vector']+cost['to_return_excluding_reader']+reader+cost['return_instruction'],delay_nonzero=after[7]!=0,clock=gate[6],music_before=call[8],request_before=call[9],fade_before=call[10:13],fade_after=after[10:13]))
     else:
      gate,call,after,ret=group
      assert ret[5]==0 and ret[6]==(gate[6]+1)&255,('gated IRQ did not tick once',group)
      full.append(dict(frame=a[0],start_master=a[2],return_master=ret[2],reader_call_wall_tstates=ticks(call,after),whole_IRQ_tstates=72+ticks(gate,ret)+10,clock_before=gate[6],clock_after=ret[6]))
    loading_audio=[r for r in audio if entry[2]<r['start_master']<r['return_master']<end[2]]
    assert loading_audio,(town,mask,region,'no loading audio IRQ')
    reader_values=[r['reader_tstates_observed'] for r in loading_audio]
    loading_full=[r for r in full if entry[2]<r['start_master']<r['return_master']<end[2]]
    observed_IRQ_master=end[3]-entry[3]
    reconstructed_IRQ_tstates=sum(r['whole_IRQ_tstates'] for r in loading_audio+loading_full)
    IRQ_residual=observed_IRQ_master-reconstructed_IRQ_tstates*15
    assert IRQ_residual==0,(town,mask,region,'IRQ budget does not close',IRQ_residual)
    rows.append(dict(town=town,target=target,mask=mask,region=region,audio_only_IRQs=len(audio),full_gated_IRQs=len(full),partial_final_IRQs=partial,loading_audio_only_IRQs=len(loading_audio),loading_reader_min_max_tstates=[min(reader_values),max(reader_values)],loading_audio_only_total_tstates=sum(r['whole_IRQ_tstates'] for r in loading_audio),loading_source_total_IRQ_master_cycles=observed_IRQ_master,loading_reconstructed_IRQ_tstates=reconstructed_IRQ_tstates,loading_IRQ_unexplained_master_cycles=IRQ_residual,audio_only_records=audio,full_gated_records=full,source_cycle_trace_identical_to_archived_v0179=True,audio_events_sha256=sha(path),source_cycle_events_sha256=sha(cycle_path)))
    print(f'{town:02X}/{mask:02X} {region}: {len(audio)} audio-only IRQs, loading reader {min(reader_values)}..{max(reader_values)} T',flush=True)
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'versions/v0180-3f155979/source'/p.name).read_bytes(),('production changed',p.name)
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),cases=len(rows),wrapper_and_state_comparisons=comparisons,loading_IRQ_budget_comparisons=24,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['24 actual original source/native paid-exit paths,controlled initial room/hero/clock/destination masks. Complete original cycle traces identical to archived v0179 source traces,so new instrumentation does not alter these observed instructions/cycles.','Original0137..0226 audio-only wrapper costs independently derived from instructions and checked around measured bank6 reader calls;C02F unchanged,delay decrement,bank/SP restoration checked. Reader cost is measured,not independently predicted. Full gated IRQ includes VDP/input work and is not modeled by this report.','All IRQ master cycles between16D0 and0ACE reconstruct exactly from measured reader/full-gated spans and instruction-derived wrapper/vector/return costs on24 paths. This closes observed accounting,not future workload prediction. All tracks/SFX,historical refresh/native scheduling,physical loading prediction and full faithful port remain open.'])
 (ROOT/'analysis/audio_irq_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(len(rows),'paths;',comparisons,'wrapper/state comparisons')

if __name__=='__main__':main()
