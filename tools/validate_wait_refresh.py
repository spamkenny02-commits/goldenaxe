"""Original 0B95..0BB3 M1/R with predicted polling and IRQ scheduling."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from wait_raster_prediction import predict_save_wait
from validate_reveal_phase_prediction import check_checkpoint

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/wait-refresh/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
    raw=(folder/f'{region}-foreground-phase-records.bin').read_bytes();assert raw==(ROOT/f'validation/map-hud-phase/{town:02x}-{mask:02x}/{region}-foreground-phase-records.bin').read_bytes()
    meta=(folder/f'{region}-foreground-m1-records.bin').read_bytes();assert len(meta)==len(raw)//800*16
    waits=(folder/f'{region}-save-wait-records.bin').read_bytes();assert waits==(ROOT/f'validation/wait-raster/{town:02x}-{mask:02x}/{region}-save-wait-records.bin').read_bytes()
    entries={};returns={}
    for n in range(0,len(raw),800):
     pc,time=struct.unpack_from('<2Q',raw,n)
     if pc not in [0xb95,0xbb3]:continue
     m1,r,_=struct.unpack_from('<Q2I',meta,n//800*16);record=dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,n+16),ram=raw[n+64:n+400],sound=raw[n+400:n+800],M1=m1,R=r)
     (entries if pc==0xb95 else returns)[time]=record
    events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());histogram=collections.Counter();irq_count=0
    for n in range(0,len(waits),112):
     w=struct.unpack_from('<14Q',waits,n);initial=entries[w[0]];end=returns[w[2]]
     p=predict_save_wait(rom,initial['phase'],initial['ram'],initial['sound'],initial['R']);tag=(town,mask,region,n//112)
     check_checkpoint(p,end,end['time']-initial['time'],tag)
     assert (p['taken'],p['exits'])==w[4:6] and p['IRQ_tstates']*15==w[3]-w[1],(tag,'polling')
     assert p['refresh']==end['R'] and p['foreground_M1']+p['IRQ_M1']==end['M1']-initial['M1'],(tag,'M1/R',p['foreground_M1'],p['IRQ_M1'],end['M1']-initial['M1'],p['refresh'],end['R'])
     actual=[e[2]-initial['time'] for e in events if e[1]==0x137 and initial['time']<e[2]<end['time']];assert actual==[e['entry_offset_master'] for e in p['events']]
     irq_count+=len(actual);histogram[p['foreground_M1']]+=1
    rows.append(dict(town=town,mask=mask,region=region,cases=len(waits)//112,IRQs=irq_count,foreground_M1_histogram=dict(histogram)));print(f'{town:02X}/{mask:02X}',region,len(waits)//112,'wait M1/R/polling/phase/state exact',flush=True)
 assert rows
 report=dict(cases=len(rows),wait_calls=sum(r['cases'] for r in rows),IRQ_calls=sum(r['IRQs'] for r in rows),rows=rows,source_sha256=hashlib.sha256(rom).hexdigest(),md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),production_ROM_changed=False,full_game_ported=False,limits=['Observed wait-entry R/raster/RAM/audio; polling and IRQ acceptance predicted, full/audio IRQ M1 composed. 331 RAM and400 audio bytes compared; input/status bytes excluded.','Other contexts,physical acknowledge,full loader R propagation and native integration remain open.'])
 (ROOT/'analysis/wait_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
