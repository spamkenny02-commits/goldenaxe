"""Check04E1 output on unchanged paid-exit runs; entry R remains observed."""
import hashlib,json,struct
from actor_reference import ROOT
from source_rng_reference import source_rng
from source_rng_refresh import source_rng_from_entry,advance_refresh

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/rng-refresh-live/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';assert cycles==json.loads(reference.read_text())
    begin=next(e[2] for e in cycles if e[1]==0x24c5 and e[4]==target);endtime=next(e[2] for e in cycles if e[1]==0x1780 and e[2]>begin)
    raw=(folder/f'{region}-rng-refresh-records.bin').read_bytes();assert len(raw)%64==0;group=[];total=history=interrupted=history_interrupted=0;history_rows=[]
    for offset in range(0,len(raw),64):
     e=struct.unpack_from('<8Q',raw,offset)
     if e[0]==0x4e1:group=[e];continue
     if not group:continue
     group.append(e)
     if e[0]!=0x4fd:continue
     assert [x[0] for x in group]==[0x4e1,0x4f7,0x4fd];entry,sample,finish=group
     prediction=source_rng(entry[3],advance_refresh(sample[6],1))
     assert (finish[3],finish[4],finish[5])==(prediction['seed'],prediction['seed'],prediction['value'])
     assert ((finish[1]-entry[1])-(finish[2]-entry[2]))//15+10==prediction['foreground_tstates']
     hasIRQ=finish[2]!=entry[2];total+=1;interrupted+=hasIRQ
     if not hasIRQ:
      local=source_rng_from_entry(entry[3],entry[6]);assert (local['sampled_refresh'],local['value'],local['refresh_at_RET_entry'])==(advance_refresh(sample[6],1),finish[5],finish[6])
     if begin<entry[1]<finish[1]<endtime:
      history+=1;history_interrupted+=hasIRQ;history_rows.append(dict(seed=entry[3],entry_R=entry[6],sampled_R=advance_refresh(sample[6],1),next_seed=finish[3],value=finish[5],IRQ_inside=hasIRQ))
     group.clear()
    assert history==3,(town,mask,region,history)
    rows.append(dict(town=town,target=target,mask=mask,region=region,calls=total,IRQ_inside_calls=interrupted,history_calls=history,history_IRQ_inside=history_interrupted,history_rows=history_rows))
    print(f'{town:02X}/{mask:02X}',region,total,'RNG calls;',history,'history;',interrupted,'interrupted',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=len(rows),calls=sum(r['calls'] for r in rows),history_calls=sum(r['history_calls'] for r in rows),IRQ_inside_calls=sum(r['IRQ_inside_calls'] for r in rows),history_IRQ_inside=sum(r['history_IRQ_inside'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['24 controlled paid exits,six routes/two masks/PAL/NTSC; source traces identical to v0179. Seed recurrence/helper foreground cost/output from observed R sample checked on every complete captured RNG call. Uninterrupted helper R sample/output predicted from observed entry R.','All72 history calls isolated by24C5..1780 window. Future entry R from16D0 and IRQ-dependent fetch accumulation not yet predicted; interrupted helpers use observed read R. No native RNG replacement or real hardware proof.'])
 (ROOT/'analysis/live_rng_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
