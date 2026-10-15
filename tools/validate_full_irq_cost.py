"""Compare complete gatedIRQ stages/state to independent source cost models."""
import hashlib,json,struct
from actor_reference import ROOT
from full_irq_cost import full_irq_cost
from audio_reader_cost import reader_cost

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/full-irq/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';assert cycles==json.loads(reference.read_text())
    raw=(folder/f'{region}-live-envelope-records.bin').read_bytes();events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());calls={};pending=None;index=0
    for event in events:
     if event[1] in [0x1a2,0x202]:pending=event
     elif event[1] in [0x1a5,0x205]:
      assert pending is not None;start=index*824;ix,de,finalde,a,cost,unwind=struct.unpack_from('<6I',raw,start);predicted=reader_cost(rom,raw[start+24:start+424],de)
      assert cost==predicted['tstates'] and finalde==predicted['de'] and raw[start+424:start+824]==predicted['state'] and not unwind
      calls[pending[2]]=predicted['tstates'];pending=None;index+=1
    assert pending is None and index*824==len(raw)
    data=(folder/f'{region}-full-irq-records.bin').read_bytes();assert len(data)%800==0 and len(data)//800==sum(e[1]==0x1a2 for e in events);checked=0;unsupported=[]
    for start in range(0,len(data),800):
     points=struct.unpack_from('<12Q',data,start);values=struct.unpack_from('<8I',data,start+96);before=data[start+128:start+464];after=data[start+464:start+800]
     try:prediction=full_irq_cost(rom,before,*values[:4],values[4],calls[points[8]])
     except NotImplementedError as error:unsupported.append(dict(record=start//800,reason=str(error)));continue
     costs=list(prediction['stages'].values());times=[points[0]]+list(points[2:11]);observed=[(b-a)//15 for a,b in zip(times,times[1:])]
     assert observed==costs,(region,start//800,'stages',observed,costs)
     assert after==prediction['state'],(region,start//800,'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(after,prediction['state'])) if a!=b][:8])
     assert ((points[11]>>16)-(points[11]&65535))&65535==2
     checked+=1
    rows.append(dict(town=town,mask=mask,target=target,region=region,captured_cases=len(data)//800,validated_cases=checked,unsupported_cases=unsupported,reader_cases=index,raw_sha256=hashlib.sha256(data).hexdigest()))
    print(f'{town:02X}/{mask:02X}',region,checked,'fullIRQ stages/state exact;',len(unsupported),'unsupported',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),cases=sum(r['validated_cases'] for r in rows),paths=len(rows),reader_cases=sum(r['reader_cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['24 controlled paid-exit paths,six routes,two masks,PAL/NTSC. Original ROM and emulated instructions unchanged.336-byte C000..C04F/DD00..DDFF state andnine completeIRQ stage costs predicted;all reader costs independently modeled.','Palette loop decisions andjoy/reset hardware inputs supplied from read-only capture,not predicted. Queue RAM outside captured ranges explicitly unsupported. No raster-phase/native loading correction or full game/hardware assertion.'])
 (ROOT/'analysis/full_irq_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
