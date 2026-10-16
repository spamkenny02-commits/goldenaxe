"""Predict hero M1/R/IRQ phases from its observed entry RAM and phase."""
import hashlib,json,struct
from actor_reference import ROOT
from hero_refresh_phase import predict_hero
from validate_reveal_phase_prediction import check_checkpoint

def main():
 source=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/hero-refresh/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
    raw=(folder/f'{region}-foreground-phase-records.bin').read_bytes();meta=(folder/f'{region}-foreground-m1-records.bin').read_bytes();assert len(meta)==len(raw)//800*16;records=[]
    for n in range(0,len(raw),800):
     pc,t=struct.unpack_from('<2Q',raw,n);m1,r,_=struct.unpack_from('<Q2I',meta,n//800*16);records.append(dict(pc=pc,time=t,phase=struct.unpack_from('<12I',raw,n+16),ram=raw[n+64:n+400],sound=raw[n+400:n+800],M1=m1,R=r))
    initial=next(r for r in records if r['pc']==0x2c63);file=next(folder.glob(f'{region}-hero-*-before.bin'));before=file.read_bytes();after=file.with_name(file.name.replace('-before','-after')).read_bytes()
    assert initial['ram']==before[:80]+before[0x1d00:0x1e00]
    points=predict_hero(source,initial['phase'],before,initial['sound'],initial['R'])
    for pc,p in points.items():
     actual=next(r for r in records if r['pc']==pc and r['time']>initial['time']);tag=(town,mask,region,hex(pc));check_checkpoint(p,actual,actual['time']-initial['time'],tag)
     assert p['refresh']==actual['R'] and p['foreground_M1']+p['IRQ_M1']==actual['M1']-initial['M1'],(tag,'M1/R',p['foreground_M1']+p['IRQ_M1'],actual['M1']-initial['M1'],p['refresh'],actual['R'])
    p=points[0x24e7];end=next(r for r in records if r['pc']==0x24e7 and r['time']>initial['time']);indices=list(range(0x41,0x6c))+list(range(0x300,0x4b0));assert all(p['hero_ram'][i]==after[i] for i in indices)
    events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());assert [e[2]-initial['time'] for e in events if e[1]==0x137 and initial['time']<e[2]<end['time']]==[e['entry_offset_master'] for e in p['events']]
    rows.append(dict(town=town,mask=mask,region=region,checkpoints=len(points),foreground_M1=p['foreground_M1'],IRQ_M1=p['IRQ_M1'],IRQs=len(p['events'])));print(f'{town:02X}/{mask:02X}',region,'hero M1/R/phase/475 bytes exact',flush=True)
 assert rows
 report=dict(cases=len(rows),rows=rows,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),production_ROM_changed=False,full_game_ported=False,limits=['Observed hero2C63 entry fullRAM/R/raster/audio supplied. Hero instruction plan predicts six checkpoints and475 relevant output bytes. Not yet chained from16D0 initial loader RAM/map; other contexts/hardware/full game/native integration remain open.'])
 (ROOT/'analysis/hero_refresh_phase_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
