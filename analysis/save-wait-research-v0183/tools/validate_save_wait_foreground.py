"""Verify save/spin work and close foreground loading with predicted readers."""
import hashlib,json,struct
from actor_reference import ROOT
from save_wait_cost import save_wait_cost
from audio_reader_cost import reader_cost
from paid_exit_foreground_cost import paid_exit_foreground_cost
from audio_irq_wrapper_cost import audio_irq_wrapper_cost

def main():
 rom=(ROOT/'input/original.sms').read_bytes();hero=json.loads((ROOT/'analysis/live_hero_initialization_cost_report.json').read_text());rows=[];wait_count=reader_count=0
 for case in hero['rows']:
  town,mask,region,target=case['town'],case['mask'],case['region'],case['target'];folder=ROOT/f'validation/save-wait/{town:02x}-{mask:02x}'
  cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json'
  assert cycles==json.loads(reference.read_text()),('source trace changed',town,mask,region)
  def entry(pc,after=0):return next(e for e in cycles if e[1]==pc and e[4]==target and e[2]>after)
  raw=(folder/f'{region}-save-wait-records.bin').read_bytes();assert len(raw)%112==0;waits=[]
  for n in range(0,len(raw),112):
   w=struct.unpack_from('<14Q',raw,n);prediction=save_wait_cost(w[4],w[5])
   work=(w[2]-w[0])-(w[3]-w[1]);prefix=(w[12]-w[0])-(w[13]-w[1])
   assert work==prediction['foreground_tstates']*15 and prefix==prediction['prefix_before_EI']*15
   assert w[7]==0 and (w[9]-w[8])&255==1 and (w[10]-w[11])&65535==22
   waits.append(dict(start=w[0],end=w[2],foreground=prediction['foreground_tstates'],taken=w[4],IRQ_master_cycles=w[3]-w[1]));wait_count+=1
  events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());pairs=[];pending=None
  for event in events:
   if event[1] in [0x1a2,0x202]:assert pending is None;pending=event
   elif event[1] in [0x1a5,0x205]:
    assert pending is not None and event[1]==pending[1]+3
    pairs.append(dict(start=pending[2],end=event[2],cost=(event[2]-pending[2])//15-17,kind=pending[1]));pending=None
  assert pending is None
  records=(folder/f'{region}-live-envelope-records.bin').read_bytes();assert len(records)==len(pairs)*824
  for i,pair in enumerate(pairs):
   ix,de,returned_de,a,cost,unwind=struct.unpack_from('<6I',records,i*824);before=records[i*824+24:i*824+424];after=records[i*824+424:i*824+824]
   prediction=reader_cost(rom,before,de)
   assert not unwind and cost==pair['cost']==prediction['tstates'] and returned_de==prediction['de'] and after==prediction['state'],(town,mask,region,i)
   pair["predicted_cost"]=prediction["tstates"];reader_count+=1
  hero_path=ROOT/case['snapshot_path'];state=hero_path.read_bytes();assert hashlib.sha256(state).hexdigest()==case['entry_sha256']
  assert any(p.read_bytes()==state for p in folder.glob(f'{region}-hero-*-before.bin')),('hero state changed',town,mask,region)
  history_start=entry(0x24c5);history_end=entry(0x1780,history_start[2]);inside=[e for e in cycles if history_start[2]<e[2]<history_end[2]]
  histories=[e for e in inside if e[1]==0x1c40];seeds=[e for e in inside if e[1]==0x4e4];misses=[e for e in inside if e[1]==0x1c88]
  assert len(histories)==len(seeds)==len(misses)==3 and all(e[6]==0xdd00 for e in misses)
  attempts=[dict(history_position=None if h[6]==0xdcef else h[6]-0xdcf0,random_position=None,seed=s[6],flag_nonzero=True) for h,s in zip(histories,seeds)]
  model=paid_exit_foreground_cost(rom,state,attempts);start=entry(0x16d0);reveal=entry(0x1fa7,start[2]);fade=entry(0xace,reveal[2])
  load_waits=[w for w in waits if start[2]<w['start']<w['end']<fade[2]];assert len(load_waits)==2
  assert all(any(e[1]==0xb95 and e[2]==w['start'] for e in cycles) and any(e[1]==0xbb3 and e[2]==w['end'] for e in cycles) for w in load_waits)
  foreground=model['to0ACE_excluding_two_save_spins']+sum(w['foreground'] for w in load_waits)
  observed=(fade[2]-start[2])-(fade[3]-start[3]);assert foreground*15==observed
  before_reveal=model['to1FA7_excluding_HUD_save_spin']+load_waits[0]['foreground'];assert before_reveal*15==(reveal[2]-start[2])-(reveal[3]-start[3])
  calls={p['start']:p for p in pairs};starts=[i for i,e in enumerate(events) if e[1]==0x137];audio_cost=full_cost=audio_count=full_count=0
  for pos,index in enumerate(starts):
   group=events[index:starts[pos+1] if pos+1<len(starts) else len(events)]
   if not start[2]<group[0][2]<fade[2]:continue
   expected=[0x137,0x1e3,0x202,0x205,0x226] if not group[0][5] else [0x137,0x1a2,0x1a5,0x1e2]
   assert [e[1] for e in group]==expected and group[-1][2]<fade[2]
   if not group[0][5]:
    wrapper=audio_irq_wrapper_cost(group[3][7]!=0);predicted=calls[group[2][2]]['predicted_cost']
    complete=wrapper['interrupt_accept_and_vector']+wrapper['to_return_excluding_reader']+predicted+wrapper['return_instruction']
    assert (group[-1][2]-group[0][2])==15*(wrapper['to_return_excluding_reader']+predicted)
    audio_cost+=complete;audio_count+=1
   else:full_cost+=72+(group[-1][2]-group[0][2])//15+10;full_count+=1
  assert (audio_cost+full_cost)*15==fade[3]-start[3]
  rows.append(dict(town=town,mask=mask,region=region,target=target,wait_records=len(waits),reader_records=len(pairs),loading_foreground_tstates=foreground,to_reveal_foreground_tstates=before_reveal,loading_waits=load_waits,loading_IRQ_master_cycles=fade[3]-start[3],loading_audio_IRQs=audio_count,loading_full_IRQs=full_count,audio_IRQ_tstates_predicted=audio_cost,full_IRQ_tstates_observed=full_cost,wall_master_cycles=fade[2]-start[2],unexplained_foreground_master_cycles=observed-foreground*15))
  print(f'{town:02X}/{mask:02X} {region}: {len(waits)} waits/{len(pairs)} readers;complete loading foreground exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=len(rows),wait_records=wait_count,reader_records=reader_count,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['24 controlled paid exits,six routes,two actor masks andtwo regions. All source cycle arrays equalv0179;hero input states identical to prior captures. Independent originalforeground instruction models now include both0B95..0BB3 spans. All captured8000 reader calls predict400 bytes/DE/cost. Audio-only loadingIRQ costs are predicted from reader plus instruction-derived wrapper/vector;remaining full gatedIRQ spans are observed. Their sum reconstructs all IRQ work exactly.','Loop branch counts,history/RNG inputs and IRQ timings are observed inputs. This closes foreground accounting,not autonomous future frame prediction. Full gatedIRQ VDP/input/palette/raster work remains measured rather than modeled.','No native delay integrated,full progression/hardware/PSG waveform unproved. Other graphics classes/story states/R-based controls and unsupported noise/restoration commands remain open.'])
 (ROOT/'analysis/save_wait_foreground_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Verified',len(rows),'paths,',wait_count,'save waits and',reader_count,'reader calls')
if __name__=='__main__':main()
