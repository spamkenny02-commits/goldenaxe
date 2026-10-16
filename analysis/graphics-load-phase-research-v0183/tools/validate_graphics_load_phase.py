"""Validate complete16D0 graphics phase chain without intermediate observed inputs."""
import hashlib,json,struct
from actor_reference import ROOT
from graphics_load_phase import predict_graphics_load
from validate_reveal_phase_prediction import check_checkpoint

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/graphics-load-phase/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';assert cycles==json.loads(reference.read_text())
    start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target)
    raw=(folder/f'{region}-foreground-phase-records.bin').read_bytes();assert len(raw)%800==0;records=[]
    for i in range(0,len(raw),800):
     pc,time=struct.unpack_from('<2Q',raw,i);records.append(dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,i+16),ram=raw[i+64:i+400],sound=raw[i+400:i+800]))
    initial=next(r for r in records if r['pc']==0x16d0 and r['time']==start)
    points=predict_graphics_load(rom,initial['phase'],initial['ram'],initial['sound'])
    for pc,prediction in points.items():
     actual=next(r for r in records if r['pc']==pc and r['time']>start)
     check_checkpoint(prediction,actual,actual['time']-start,(town,mask,region))
    end=next(r for r in records if r['pc']==0x24b9 and r['time']>start);prediction=points[0x24b9]
    irq=json.loads((folder/f'{region}-audio-irq-events.json').read_text());observed=[i[2]-start for i in irq if i[1]==0x137 and start<i[2]<end['time']]
    assert observed==[i['entry_offset_master'] for i in prediction['events']]
    rows.append(dict(town=town,target=target,mask=mask,region=region,checkpoints=len(points),foreground_tstates=prediction['foreground_tstates'],wall_master_cycles=prediction['wall_master_cycles'],predicted_IRQs=len(observed)))
    print(f'{town:02X}/{mask:02X}',region,'16D0->24B9 graphics phase/state/IRQ timing exact',flush=True)
 assert rows
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=len(rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Changed class0 graphics/display off ordinary paid-exit rooms/C0AC0. Only16D0 phase/RAM/audio input; six checkpoint phases and all audio IRQs predicted through patterns,metatiles,terrain andSRAM copy.','331 RAM bytes/all400 audio bytes compared at each checkpoint; C01B andC020..23 excluded. Decoded RAM/VRAM/palette/SRAM bytes outside these snapshots not modeled. Bank shadows/class change outside captured RAM supplied by scope.','Next map/HUD/actor/history work,native timing integration,other graphics classes andfull progression/hardware unproved.'])
 (ROOT/'analysis/graphics_load_phase_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
