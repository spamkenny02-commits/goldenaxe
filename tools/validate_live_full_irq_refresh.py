"""Gated IRQ M1/R on paid passage routes with unchanged source trace evidence."""
import hashlib,json,struct,collections
from actor_reference import ROOT
from validate_full_irq_refresh import check

def main():
 source=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/full-irq-refresh-live/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
    raw=(folder/f'{region}-full-irq-records.bin').read_bytes();assert len(raw)%800==0
    assert raw==(ROOT/f'validation/wait-raster/{town:02x}-{mask:02x}/{region}-full-irq-records.bin').read_bytes()
    metadata=(folder/f'{region}-full-irq-m1-records.bin').read_bytes();assert len(metadata)==len(raw)//800*152
    readers=(folder/f'{region}-live-envelope-records.bin').read_bytes();assert readers==(ROOT/f'validation/wait-raster/{town:02x}-{mask:02x}/{region}-live-envelope-records.bin').read_bytes()
    events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());calls=[e for e in events if e[1] in [0x1a2,0x202]];assert len(readers)==len(calls)*824
    lookup={e[2]:readers[n*824:(n+1)*824] for n,e in enumerate(calls)};histogram=collections.Counter();workloads=collections.Counter()
    for n in range(0,len(raw),800):
     record=raw[n:n+800];points=struct.unpack_from('<12Q',record);prediction=check(source,record,metadata[n//800*152:(n//800+1)*152],lookup[points[8]],(town,mask,region,n//800))
     histogram[prediction['to_RET_M1']]+=1
     for k,v in prediction['M1_stages'].items():workloads[f'{k}:{v}']+=1
    rows.append(dict(town=town,mask=mask,region=region,cases=len(raw)//800,M1_histogram=dict(histogram),stages=dict(workloads),M1_sha256=hashlib.sha256(metadata).hexdigest()));print(f'{town:02X}/{mask:02X}',region,len(raw)//800,'full IRQ nine stages M1/R exact;source trace unchanged',flush=True)
 assert rows
 report=dict(cases=len(rows),IRQ_calls=sum(r['cases'] for r in rows),rows=rows,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),production_ROM_changed=False,full_game_ported=False,limits=['Controlled paid exits; captured IRQ entry R/raster and input ports supplied. Palette polling predicted from raster and independent prefix costs. Nine stages include graphics queue, SAT/HUD/tiles/audio/input/timers; original 336-byte state and reader states/costs unchanged.','Does not yet predict foreground refresh or initial RNG from load entry. Physical interrupt acknowledgement and native integration/full game remain unproved.'])
 (ROOT/'analysis/live_full_irq_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
