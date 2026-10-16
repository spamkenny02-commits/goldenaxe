"""Predict graphics/map/HUD/wait M1/R from one entry, including scheduled audio IRQs."""
import hashlib,json,struct
from actor_reference import ROOT
from map_hud_phase import predict_map_hud
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
    context=(folder/f'{region}-hud-context-records.bin').read_bytes();assert len(context)==len(raw)//800*16
    meta=(folder/f'{region}-foreground-m1-records.bin').read_bytes();assert len(meta)==len(raw)//800*16;records=[]
    for n in range(0,len(raw),800):
     pc,time=struct.unpack_from('<2Q',raw,n);m1,r,_=struct.unpack_from('<Q2I',meta,n//800*16)
     records.append(dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,n+16),ram=raw[n+64:n+400],sound=raw[n+400:n+800],M1=m1,R=r,context=context[n//800*16:n//800*16+16]))
    start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target);initial=next(r for r in records if r['pc']==0x16d0 and r['time']==start)
    points=predict_map_hud(rom,initial['phase'],initial['ram'],initial['sound'],target,initial['context'],refresh=initial['R'])
    for pc,p in points.items():
     end=next(r for r in records if r['pc']==pc and r['time']>start);assert end['context']==initial['context'];check_checkpoint(p,end,end['time']-start,(town,mask,region,pc))
     assert p['refresh']==end['R'],(town,mask,region,hex(pc),'R',p['refresh'],end['R'])
     assert p['foreground_M1']+p['IRQ_M1']==end['M1']-initial['M1'],(town,mask,region,hex(pc),'M1',p['foreground_M1'],p['IRQ_M1'],end['M1']-initial['M1'])
    p=points[0x24bf];end=next(r for r in records if r['pc']==0x24bf and r['time']>start)
    irq=json.loads((folder/f'{region}-audio-irq-events.json').read_text());observed=[e[2]-start for e in irq if e[1]==0x137 and start<e[2]<end['time']];assert observed==[e['entry_offset_master'] for e in p['events']]
    assert len(points)==16
    rows.append(dict(town=town,mask=mask,region=region,checkpoints=len(points),foreground_M1=p['foreground_M1'],IRQ_M1=p['IRQ_M1'],entry_R=initial['R'],exit_R=end['R'],IRQs=len(observed),wall_master_cycles=p['wall_master_cycles'],HUD_context=initial['context'].hex(),full_IRQs=sum(e['kind']=='full' for e in p['events']),wait_taken=points[0xbb3]['taken']));print(f'{town:02X}/{mask:02X}',region,'16D0->24BF M1/R/phase/state exact',flush=True)
 assert rows
 report=dict(cases=len(rows),rows=rows,source_sha256=hashlib.sha256(rom).hexdigest(),md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),production_ROM_changed=False,full_game_ported=False,limits=['Changed class0 graphics/map/HUD/wait/transfer/palette; C0AC=0, C041!=5, room and saved bit0=1 supplied. One observed entry R/raster/RAM/audio and16-byte HUD context; subsequent R,phase and IRQ schedule predicted. Original capture records and full source cycle traces unchanged.','No hardware acknowledgement increment claimed; local GPG convention retained. Actors/history,R-based unsupported audio commands and native integration remain open.'])
 (ROOT/'analysis/map_hud_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
