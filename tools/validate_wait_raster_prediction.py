"""Check autonomous wait-loop decisions and IRQ timing from observed wait-entry state."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from wait_raster_prediction import predict_save_wait

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/wait-raster/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';assert cycles==json.loads(reference.read_text())
    raw=(folder/f'{region}-save-wait-records.bin').read_bytes();entries=(folder/f'{region}-wait-entry-records.bin').read_bytes();assert len(raw)%112==0 and len(entries)==len(raw)//112*784
    irq=json.loads((folder/f'{region}-audio-irq-events.json').read_text());tested=0;predicted_IRQs=0;contexts=collections.Counter();kinds=collections.Counter()
    for i in range(len(raw)//112):
     w=struct.unpack_from('<14Q',raw,i*112);phase=struct.unpack_from('<12I',entries,i*784);state=entries[i*784+48:i*784+384];sound=entries[i*784+384:i*784+784]
     p=predict_save_wait(rom,phase,state,sound)
     assert (p['taken'],p['exits'])==w[4:6],(region,i,'loops',p,w[4:6],phase)
     assert p['wall_master_cycles']==w[2]-w[0] and p['IRQ_tstates']*15==w[3]-w[1],(region,i,'timing',p,w)
     assert p['gate']==w[7] and p['clock']==w[9]
     observed=[e for e in irq if e[1]==0x137 and w[0]<e[2]<w[2]]
     assert [e[2]-w[0] for e in observed]==[e['entry_offset_master'] for e in p['events']],(region,i,'IRQ phase')
     assert [bool(e[5]) for e in observed]==[e['kind']=='full' for e in p['events']]
     tested+=1;predicted_IRQs+=len(p['events']);contexts[str(tuple(phase[8:11]))]+=1;kinds[','.join(e['kind'] for e in p['events'])]+=1
    rows.append(dict(town=town,mask=mask,target=target,region=region,contexts=dict(contexts),IRQ_sequences=dict(kinds),cases=tested,predicted_IRQs=predicted_IRQs,entry_sha256=hashlib.sha256(entries).hexdigest(),wait_sha256=hashlib.sha256(raw).hexdigest()));print(f'{town:02X}/{mask:02X}',region,tested,'wait loops/wall/IRQ phase predicted',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=sum(r['cases'] for r in rows),paths=len(rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['24 controlled paid exits,six routes/two masks,PAL/NTSC. Only post-interrupt-check wait-entry raster,CPU IRQ latch/IFF state,336 RAM bytes and400 driver bytes supplied. Predicts loop decisions,accepted IRQ offsets,costs and total wall time;observed branch counts/IRQ timings are comparison data only.','Mode4/192 lines,VINT enabled,HINT disabled,no NMI/reset/nested interrupt. VINT asserted at physical line193 per local GPG SMS scheduling. Input-port values affect postIRQ state but not supported nonreset timing;dummy joy0 used.','Wait-entry state/phase remains observed. Future phase through foreground loading,other modes/R-based controls/unsupported driver paths,native loading integration,hardware/full game remain open.'])
 (ROOT/'analysis/wait_raster_prediction_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
