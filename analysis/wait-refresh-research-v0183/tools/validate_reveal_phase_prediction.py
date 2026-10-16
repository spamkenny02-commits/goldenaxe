"""Predict original1FA7..0ACE phase flow from a single reveal-entry snapshot."""
import hashlib,json,struct
from actor_reference import ROOT
from reveal_phase_prediction import predict_reveal

def raster(p):return (p[1]*3420+((p[0]-p[2]+0x80000000)&0xffffffff)-0x80000000)%(p[3]*3420)
def check_checkpoint(prediction,actual,span,tag):
 assert prediction['wall_master_cycles']==span,(tag,hex(actual['pc']),'wall',prediction['wall_master_cycles'],span)
 assert raster(prediction['phase'])==raster(actual['phase']),(tag,hex(actual['pc']),'raster',prediction['phase'],actual['phase'])
 assert prediction['phase'][3:9]==actual['phase'][3:9] and prediction['phase'][10:]==actual['phase'][10:],(tag,hex(actual['pc']),'VDP/IFF/latch')
 assert prediction['sound']==actual['sound'],(tag,hex(actual['pc']),'sound')
 assert all(prediction['ram'][i]==actual['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,hex(actual['pc']),'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(prediction['ram'],actual['ram'])) if a!=b][:12])

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/reveal-phase/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';assert cycles==json.loads(reference.read_text())
    start=next(e[2] for e in cycles if e[1]==0x1fa7 and e[4]==target);raw=(folder/f'{region}-foreground-phase-records.bin').read_bytes();assert len(raw)%800==0
    records=[]
    for i in range(0,len(raw),800):
     pc,time=struct.unpack_from('<2Q',raw,i);records.append(dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,i+16),ram=raw[i+64:i+400],sound=raw[i+400:i+800]))
    initial=next(r for r in records if r['pc']==0x1fa7 and r['time']==start);model=predict_reveal(rom,initial['phase'],initial['ram'],initial['sound'])
    def next_record(pc,after):return next(r for r in records if r['pc']==pc and r['time']>after)
    clear=next_record(0xaa4,start);end=next_record(0xace,clear['time']);restored=next_record(0xac0,clear['time']);returned=next_record(0xbb3,clear['time'])
    waits=(folder/f'{region}-save-wait-records.bin').read_bytes();entries=(folder/f'{region}-wait-entry-records.bin').read_bytes()
    windex=next(i for i in range(len(waits)//112) if clear['time']<struct.unpack_from('<Q',waits,i*112)[0]<returned['time']);w=struct.unpack_from('<14Q',waits,windex*112);e=entries[windex*784:(windex+1)*784]
    wait_entry=dict(pc=0xb95,time=w[0],phase=struct.unpack_from('<12I',e),ram=e[48:384],sound=e[384:784])
    checks=[(model['clear'],clear,clear['time']-start),(model['before_wait'],wait_entry,w[0]-start),(model['wait'],returned,returned['time']-w[0]),(model['restored'],restored,restored['time']-returned['time']),(model['after'],end,end['time']-returned['time'])]
    for prediction,actual,span in checks:check_checkpoint(prediction,actual,span,region)
    assert (model['wait']['taken'],model['wait']['exits'])==w[4:6] and model['wait']['IRQ_tstates']*15==w[3]-w[1]
    assert model['wall_master_cycles']==end['time']-start
    predicted=[(i['entry_offset_master'],False) for i in model['before_wait']['events']]+[(model['before_wait']['wall_master_cycles']+i['entry_offset_master'],i['kind']=='full') for i in model['wait']['events']]+[(model['before_wait']['wall_master_cycles']+model['wait']['wall_master_cycles']+i['entry_offset_master'],False) for i in model['after']['events']]
    irq=json.loads((folder/f'{region}-audio-irq-events.json').read_text());observed=[(i[2]-start,bool(i[5])) for i in irq if i[1]==0x137 and start<i[2]<end['time']];assert observed==predicted,(region,'IRQ phase',observed,predicted)
    rows.append(dict(town=town,mask=mask,target=target,region=region,checkpoints=len(checks),wall_master_cycles=model['wall_master_cycles'],prewait_audio_IRQs=len(model['before_wait']['events']),postwait_audio_IRQs=len(model['after']['events']),wait_taken=model['wait']['taken'],status_suppressions=model['before_wait']['status_suppressions'],vector_coalescences=model['before_wait']['vector_coalescences'],predicted_IRQs=len(predicted)))
    print(f'{town:02X}/{mask:02X}',region,'1FA7->0ACE reveal phase/state/IRQ timing exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=len(rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['24 controlled paid exits,six routes/two masks,PAL/NTSC. Only1FA7 entry phase,336-byte RAM and400-byte sound snapshot supplied. Predicts VRAM-clear/preparation/wait/restore/display-enable checkpoints and all IRQ acceptance offsets. Original cycle arrays identical to v0179.','RAM statusC01B andinputC020..C023 excluded from state assertions;dummy joy0 used in wait IRQ forecast. Palette bytes andVRAM contents not modeled here. Other assertedRAM331 bytes andall400 sound bytes compare at5 checkpoints.','IRQ-enabled mode4/HINT-disabled/nonreset/nonNMI/non-nested scope. Input reveal-entry state remains observed;earlier loading work/historyRNG/native integration/hardware and full game remain open.'])
 (ROOT/'analysis/reveal_phase_prediction_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
