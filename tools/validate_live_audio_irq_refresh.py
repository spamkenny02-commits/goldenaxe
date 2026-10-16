"""Check vector andaudio-only wrapper M1/R stages with full reader composition."""
import hashlib,json,struct
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from audio_irq_wrapper_refresh import audio_irq_wrapper_refresh
from source_rng_refresh import advance_refresh

def main():
 source=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/audio-irq-refresh-live/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    baseline=ROOT/f'validation/reader-refresh-live/{town:02x}-{mask:02x}'
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
    events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());assert events==json.loads((baseline/f'{region}-audio-irq-events.json').read_text())
    raw=(folder/f'{region}-live-envelope-records.bin').read_bytes();assert raw==(baseline/f'{region}-live-envelope-records.bin').read_bytes() and len(raw)%824==0
    reader_m1=(folder/f'{region}-live-envelope-m1-records.bin').read_bytes();assert reader_m1==(baseline/f'{region}-live-envelope-m1-records.bin').read_bytes()
    meta=(folder/f'{region}-audio-irq-m1-records.bin').read_bytes();assert len(meta)==len(events)*40
    starts=[i for i,e in enumerate(events) if e[1]==0x137];assert len(starts)==len(raw)//824
    audio=zero=nonzero=0;fetches_total=0
    def observation(index):return struct.unpack_from('<5Q',meta,index*40)
    for call,index in enumerate(starts):
     end=starts[call+1] if call+1<len(starts) else len(events);group=events[index:end];entry=observation(index)
     assert entry[0]-entry[2]==6 and entry[1]==advance_refresh(entry[3],6) and group[0][2]-entry[4]==59*15,(town,mask,region,call,'vector')
     offset=call*824;ix,de_before,de_after,a,cost,unwind=struct.unpack_from('<6I',raw,offset);before=raw[offset+24:offset+424];after=raw[offset+424:offset+824]
     reader=reader_refresh(source,before,de_before);reader_fetches,reader_R_before,reader_R_after=struct.unpack_from('<3I',reader_m1,call*12)
     assert not unwind and (cost,de_after,after,reader_fetches)==(reader['tstates'],reader['de'],reader['state'],reader['m1_fetches']) and reader_R_after==advance_refresh(reader_R_before,reader_fetches)
     if group[0][5]:continue
     assert [e[1] for e in group]==[0x137,0x1e3,0x202,0x205,0x226]
     timer=group[3][7];wrapper=audio_irq_wrapper_refresh(timer!=0);stage=wrapper['M1_stages']
     counts=[stage['gate'],stage['save_and_map'],stage['audio_call']+reader_fetches,stage['delay']+stage['restore']]
     costs=[wrapper['gate'],wrapper['save_and_map'],wrapper['audio_call']+cost,wrapper['delay']+wrapper['restore']]
     for j in range(4):
      previous,current=observation(index+j),observation(index+j+1)
      assert current[0]-previous[0]==counts[j] and current[1]==advance_refresh(previous[1],counts[j]),(town,mask,region,call,j,'wrapper M1/R')
      assert group[j+1][2]-group[j][2]==costs[j]*15,(town,mask,region,call,j,'wrapper cost')
     assert group[4][7]==max(timer-1,0) and observation(index+3)[1]==reader_R_after
     audio+=1;zero+=not timer;nonzero+=bool(timer);fetches_total+=wrapper['whole_IRQ_excluding_reader_M1']+reader_fetches
    rows.append(dict(town=town,target=target,mask=mask,region=region,vector_calls=len(starts),reader_calls=len(starts),audio_only_IRQs=audio,zero_timer_IRQs=zero,nonzero_timer_IRQs=nonzero,instruction_M1_audio_IRQ_total=fetches_total,IRQ_meta_sha256=hashlib.sha256(meta).hexdigest()));print(f'{town:02X}/{mask:02X}',region,len(starts),'vectors/readers;',audio,'audio-only wrapper M1/R/cost stages exact',flush=True)
 assert rows
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=len(rows),vector_calls=sum(r['vector_calls'] for r in rows),reader_calls=sum(r['reader_calls'] for r in rows),audio_only_IRQs=sum(r['audio_only_IRQs'] for r in rows),zero_timer_IRQs=sum(r['zero_timer_IRQs'] for r in rows),nonzero_timer_IRQs=sum(r['nonzero_timer_IRQs'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled paid exits,six routes/two masks/PAL/NTSC. Original vectors,fullreader andaudio-only wrapper observed read-only. Old reader state/M1 andIRQ event records byte-identical,sourcecycles equalv0179. Six vector instructions plusfour audio-only stage M1/R/cost spans asserted.','LocalGPG IM1 accept has no explicit R++ andis not included in six vector-instruction fetches;hardware acknowledgement refresh not proved. Final RET is counted from original opcode/isolated wrapper execution,not an observed post-RET live checkpoint.','Full gatedIRQ body/foreground M1 propagation andload-entry R remain open;entry R observed. Unsupported reader commands/restoration,native RNG replacement,waveform/hardware/full progression remain unproved.'])
 (ROOT/'analysis/live_audio_irq_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
