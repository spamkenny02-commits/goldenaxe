"""Predict original palette loop decisions from observed IRQ-entry raster phase."""
import hashlib,json,struct
from actor_reference import ROOT
from full_irq_cost import full_irq_cost
from irq_raster_phase import predict_palette_wait

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/irq-raster/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';assert cycles==json.loads(reference.read_text())
    raw=(folder/f'{region}-full-irq-records.bin').read_bytes();phases=(folder/f'{region}-irq-raster-records.bin').read_bytes();assert len(raw)%800==0 and len(phases)==len(raw)//800*32
    checked=0;skipped=0;counts=[];hardware=set()
    for i in range(len(raw)//800):
     points=struct.unpack_from('<12Q',raw,i*800);values=struct.unpack_from('<8I',raw,i*800+96);before=raw[i*800+128:i*800+464];phase=struct.unpack_from('<8I',phases,i*32);hardware.add(phase[7])
     prefix=full_irq_cost(rom,before,0,0 if before[0x33] else 1,0,16,values[4],0)
     model=predict_palette_wait(phase,sum(list(prefix['stages'].values())[:4]),before[0x33],values[4])
     assert (model['taken'],model['exits'])==values[:2],(region,i,phase,model,values[:2])
     predicted=full_irq_cost(rom,before,model['taken'],model['exits'],values[2],values[3],values[4],(points[9]-points[8])//15-17)
     assert predicted['stages']['palette']*15==points[6]-points[5]
     checked+=1;skipped+=bool(before[0x33]);counts.append(model['taken'])
    rows.append(dict(town=town,mask=mask,target=target,region=region,cases=checked,palette_skipped=skipped,taken_min_max=[min(counts),max(counts)],hardware=sorted(hardware),phase_sha256=hashlib.sha256(phases).hexdigest(),fullIRQ_sha256=hashlib.sha256(raw).hexdigest()))
    print(f'{town:02X}/{mask:02X}',region,checked,'palette decisions/stage costs predicted from entry phase',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=sum(r['cases'] for r in rows),paths=len(rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['24 controlled paid exits,six routes/two masks,PAL/NTSC. Complete source cycle arrays identical to v0179. Reads IRQ-entry CPU/VDP counters only;predicts all original0186 taken/exit decisions and palette stage costs without their observed counts as inputs.','Mode4/192 lines,noninterlaced;262/313 lines,VC overflowDA/F2. IN sampling follows the local GPG SMS port implementation (instruction end);hardware validation not claimed.','Entry raster phase remains observed. Future IRQ acceptance/wait polling/native loading prediction and full game remain open. Other VDP modes/latched counters/MD compatibility mode unsupported.'])
 (ROOT/'analysis/irq_raster_phase_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
