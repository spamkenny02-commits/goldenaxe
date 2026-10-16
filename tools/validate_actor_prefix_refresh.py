"""Verify history/RNG decisions from one loader-entry state, no observed draws."""
import hashlib,json,struct
from actor_reference import ROOT
from actor_prefix_refresh_phase import predict_actor_prefix
from validate_reveal_phase_prediction import check_checkpoint

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/actor-prefix-refresh/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
    raw=(folder/f'{region}-foreground-phase-records.bin').read_bytes();meta=(folder/f'{region}-foreground-m1-records.bin').read_bytes();hud=(folder/f'{region}-hud-context-records.bin').read_bytes();history=(folder/f'{region}-history-context-records.bin').read_bytes();actor_context=(folder/f'{region}-actor-load-context-records.bin').read_bytes();assert len(actor_context)==len(raw)//800*769
    assert len(raw)%800==0 and len(meta)==len(hud)==len(raw)//800*16 and len(history)==len(raw)//800*277;records=[]
    for n in range(0,len(raw),800):
     pc,t=struct.unpack_from('<2Q',raw,n);m1,r,_=struct.unpack_from('<Q2I',meta,n//800*16);context=history[n//800*277:(n//800+1)*277]
     records.append(dict(pc=pc,time=t,phase=struct.unpack_from('<12I',raw,n+16),ram=raw[n+64:n+400],sound=raw[n+400:n+800],M1=m1,R=r,hud=hud[n//800*16:(n//800+1)*16],context=context,actors=actor_context[n//800*769:n//800*769+768],active_count=actor_context[n//800*769+768]))
    start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target);initial=next(r for r in records if r['pc']==0x16d0 and r['time']==start);context=initial['context'];assert int.from_bytes(context[:2],'little')==target
    actor_result=predict_actor_prefix(rom,initial['phase'],initial['ram'],initial['sound'],target,initial['hud'],initial['R'],context[2:18],context[18:274]);result=actor_result['prior'];cursor=start
    for pc,p in result['loader_points'].items():
     actual=next(r for r in records if r['pc']==pc and r['time']>start);check_checkpoint(p,actual,actual['time']-start,(town,mask,region,hex(pc)))
     assert p['refresh']==actual['R'] and p['foreground_M1']+p['IRQ_M1']==actual['M1']-initial['M1']
     assert actual['hud']==initial['hud'] and actual['context'][2:274]==initial['context'][2:274]
    for item in result['history_points']:
     p=item['prediction'];actual=next(r for r in records if r['pc']==item['pc'] and r['time']>cursor);cursor=actual['time'];tag=(town,mask,region,hex(item['pc']))
     check_checkpoint(p,actual,actual['time']-start,tag)
     assert p['refresh']==actual['R'] and p['foreground_M1']+p['IRQ_M1']==actual['M1']-initial['M1'],(tag,'M1/R',p['refresh'],actual['R'],p['foreground_M1']+p['IRQ_M1'],actual['M1']-initial['M1'])
     assert actual['context'][2:18]==item['history'] and actual['context'][18:274]==item['flags'],(tag,'history/persistence')
     if item['expected_A'] is not None:assert actual['context'][274]==item['expected_A'],(tag,'RNG output')
     if item['expected_HL'] is not None:assert int.from_bytes(actual['context'][275:277],'little')==item['expected_HL'],(tag,'RNG seed register')
    for item in actor_result['actor_points']:
     p=item['prediction'];actual=next(r for r in records if r['pc']==item['pc'] and r['time']>cursor);cursor=actual['time'];tag=(town,mask,region,hex(item['pc']))
     check_checkpoint(p,actual,actual['time']-start,tag)
     assert p['refresh']==actual['R'] and p['foreground_M1']+p['IRQ_M1']==actual['M1']-initial['M1'],(tag,'M1/R')
     assert actual['actors']==item['actors'],(tag,'actors')
     if item['active_count'] is not None:assert actual['active_count']==item['active_count'],(tag,'active count')
    assert len(result['draws'])==3
    observed=[e for e in cycles if e[1]==0x4e4 and start<e[2]<cursor];assert [e[6] for e in observed]==[d['seed'] for d in result['draws']]
    events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());assert [e[2]-start for e in events if e[1]==0x137 and start<e[2]<cursor]==[e['entry_offset_master'] for e in p['events']]
    rows.append(dict(town=town,mask=mask,region=region,actor_checkpoints=len(actor_result['actor_points']),history_checkpoints=len(result['history_points']),loader_checkpoints=len(result['loader_points']),draws=result['draws'],foreground_M1=p['foreground_M1'],IRQ_M1=p['IRQ_M1'],exit_R=p['refresh']));print(f'{town:02X}/{mask:02X}',region,'16D0->1853 actors/history/RNG/M1/R/phase/state exact',flush=True)
 assert rows
 report=dict(cases=len(rows),draws=sum(len(r['draws']) for r in rows),rows=rows,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),production_ROM_changed=False,full_game_ported=False,limits=['Single16D0 R/raster/RAM/audio/HUD plus room/history/persistence context input; no observed intermediate draws/search positions. Controlled class0 paid exits.','331 RAM/400 audio/history16/persistence256 checked at history checkpoints. Other RAM/VDP outputs,Actor graphics/hero/tail/native integration,unsupported audio andfull game remain open.'])
 (ROOT/'analysis/actor_prefix_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
