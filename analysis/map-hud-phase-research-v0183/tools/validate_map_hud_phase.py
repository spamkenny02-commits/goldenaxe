"""Validate graphics/world-map phase chain without intermediate observed inputs."""
import hashlib,json,struct
from actor_reference import ROOT
from map_hud_phase import predict_map_hud
from validate_reveal_phase_prediction import check_checkpoint

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/map-hud-phase/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';assert cycles==json.loads(reference.read_text())
    start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target)
    raw=(folder/f'{region}-foreground-phase-records.bin').read_bytes();context=(folder/f'{region}-hud-context-records.bin').read_bytes();assert len(raw)%800==0 and len(context)==len(raw)//800*16;records=[]
    for i in range(0,len(raw),800):
     pc,time=struct.unpack_from('<2Q',raw,i);records.append(dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,i+16),ram=raw[i+64:i+400],sound=raw[i+400:i+800],context=context[i//800*16:i//800*16+16]))
    initial=next(r for r in records if r['pc']==0x16d0 and r['time']==start)
    points=predict_map_hud(rom,initial['phase'],initial['ram'],initial['sound'],target,initial['context'])
    for pc,prediction in points.items():
     actual=next(r for r in records if r['pc']==pc and r['time']>start)
     assert actual['context']==initial['context'],(town,mask,region,'HUD context changed')
     check_checkpoint(prediction,actual,actual['time']-start,(town,mask,region))
    end=next(r for r in records if r['pc']==0x24bf and r['time']>start);prediction=points[0x24bf]
    irq=json.loads((folder/f'{region}-audio-irq-events.json').read_text());observed=[i[2]-start for i in irq if i[1]==0x137 and start<i[2]<end['time']]
    assert observed==[i['entry_offset_master'] for i in prediction['events']]
    rows.append(dict(town=town,target=target,mask=mask,region=region,checkpoints=len(points),foreground_tstates=prediction['foreground_tstates'],wall_master_cycles=prediction['wall_master_cycles'],predicted_IRQs=len(observed),predicted_full_IRQs=sum(e['kind']=='full' for e in prediction['events']),wait_taken=points[0xbb3]['taken']))
    print(f'{town:02X}/{mask:02X}',region,'16D0->24BF graphics/map/HUD phase/state/IRQ timing exact',flush=True)
 assert rows
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=len(rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Changed class0 graphics/display off ordinary paid-exit rooms/C0AC0. Only16D0 phase/336RAM/400audio/16HUD context input; sixteen checkpoint phases and all audio IRQs predicted through graphics/map/HUD/save-wait/transfer/palette; room andsaved bit0 supplied as scoped inputs.','331 RAM bytes/all400 audio bytes compared at each checkpoint; C01B andC020..23 excluded. Decoded motif0 copied to DDBC/DDFC for defaultFF map metadata; diagnostic extraRAM captures are not prediction inputs. Other decoded RAM/VRAM/palette/SRAM byte outputs outside snapshots not modeled. Original mode4/VINT-only,non-nested scope; dummy controller inputs used by full IRQ. Bank shadows/class change outside captured RAM supplied by scope.','Next actor/history work,native timing integration,other graphics classes andfull progression/hardware unproved.'])
 (ROOT/'analysis/map_hud_phase_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
