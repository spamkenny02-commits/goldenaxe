"""Verify history/RNG decisions from one loader-entry state, no observed draws."""
import hashlib,json,struct
from actor_reference import ROOT,load_room_actors
from loader_hero_refresh_phase import predict_loader_hero
from validate_reveal_phase_prediction import check_checkpoint

def main():
 rom=(ROOT/'input/original.sms').read_bytes();rows=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   folder=ROOT/f'validation/loader-hero-refresh/{town:02x}-{mask:02x}'
   if not folder.exists():continue
   for region in ['auto','pal']:
    cycles=json.loads((folder/f'{region}-cycle-events.json').read_text());assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
    raw=(folder/f'{region}-foreground-phase-records.bin').read_bytes();meta=(folder/f'{region}-foreground-m1-records.bin').read_bytes();hud=(folder/f'{region}-hud-context-records.bin').read_bytes();history=(folder/f'{region}-history-context-records.bin').read_bytes();actor_context=(folder/f'{region}-actor-load-context-records.bin').read_bytes();assert len(actor_context)==len(raw)//800*769
    assert len(raw)%800==0 and len(meta)==len(hud)==len(raw)//800*16 and len(history)==len(raw)//800*277;records=[]
    for n in range(0,len(raw),800):
     pc,t=struct.unpack_from('<2Q',raw,n);m1,r,_=struct.unpack_from('<Q2I',meta,n//800*16);context=history[n//800*277:(n//800+1)*277]
     records.append(dict(pc=pc,time=t,phase=struct.unpack_from('<12I',raw,n+16),ram=raw[n+64:n+400],sound=raw[n+400:n+800],M1=m1,R=r,hud=hud[n//800*16:(n//800+1)*16],context=context,actors=actor_context[n//800*769:n//800*769+768],active_count=actor_context[n//800*769+768]))
    start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target);initial=next(r for r in records if r['pc']==0x16d0 and r['time']==start);context=initial['context'];assert int.from_bytes(context[:2],'little')==target
    entry_raw=(folder/f'{region}-loader-entry-records.bin').read_bytes();assert len(entry_raw)%8200==0
    initial_ram=next(entry_raw[n+8:n+8200] for n in range(0,len(entry_raw),8200) if struct.unpack_from('<Q',entry_raw,n)[0]==start)
    assert initial_ram[:80]+initial_ram[0x1d00:0x1e00]==initial['ram'] and initial_ram[0x1e00:0x1f90]==initial['sound']
    loader_result=predict_loader_hero(rom,initial['phase'],initial_ram,initial['sound'],initial['R']);graphics_result=loader_result['prior'];actor_result=graphics_result['prior'];result=actor_result['prior'];cursor=start
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
    for item in graphics_result['graphics_points']:
     p=item['prediction'];actual=next(r for r in records if r['pc']==item['pc'] and r['time']>cursor);cursor=actual['time'];tag=(town,mask,region,hex(item['pc']))
     check_checkpoint(p,actual,actual['time']-start,tag)
     assert p['refresh']==actual['R'] and p['foreground_M1']+p['IRQ_M1']==actual['M1']-initial['M1'],(tag,'M1/R',p['foreground_M1']+p['IRQ_M1'],actual['M1']-initial['M1'],p['refresh'],actual['R'])
     assert item['actors']==actual['actors'],(tag,'actor allocation')
    expected,patterns,allocation,count,resources=load_room_actors(rom,target,actor_result['persistence']);assert expected==actual['actors']
    graph=(folder/f'{region}-actor-graphics-records.bin').read_bytes();assert len(graph)%8208==0
    g=next(graph[n:n+8208] for n in range(0,len(graph),8208) if struct.unpack_from('<Q',graph,n)[0]==cursor)
    assert struct.unpack_from('<I',g,8)[0]==allocation
    assert g[16:16+allocation*32]==patterns[0x2000:0x2000+allocation*32],(town,mask,region,'VRAM patterns')
    actual=next(r for r in records if r['pc']==0x2c63 and r['time']>cursor);p=loader_result['hero_entry'];check_checkpoint(p,actual,actual['time']-start,(town,mask,region,'hero entry'));assert p['refresh']==actual['R'] and p['foreground_M1']+p['IRQ_M1']==actual['M1']-initial['M1'];cursor=actual['time']
    file=next(folder.glob(f'{region}-hero-*-before.bin'));observed_entry=file.read_bytes();indices=list(range(0x41,0x6c))+list(range(0x300,0x4b0));predicted_entry=loader_result['hero_entry_ram']
    assert all(predicted_entry[i]==observed_entry[i] for i in indices),(town,mask,region,'predicted hero input',[(hex(i),predicted_entry[i],observed_entry[i]) for i in indices if predicted_entry[i]!=observed_entry[i]][:10])
    assert predicted_entry[0x1600:0x1b00]==observed_entry[0x1600:0x1b00]
    gear=[0xbf,0xdf,0xe1,0xec,0xf0,0xf1,0xf2,0xe0+predicted_entry[0xdf],0x30a,0x311,0x313,0x318];assert all(predicted_entry[i]==observed_entry[i] for i in gear)
    for item_pc,p in loader_result['hero_points'].items():
     actual=next(r for r in records if r['pc']==item_pc and r['time']>cursor);cursor=actual['time'];check_checkpoint(p,actual,actual['time']-start,(town,mask,region,hex(item_pc)))
     assert p['refresh']==actual['R'] and p['foreground_M1']+p['IRQ_M1']==actual['M1']-initial['M1']
    observed_return=file.with_name(file.name.replace('-before','-after')).read_bytes();assert all(p['hero_ram'][i]==observed_return[i] for i in indices)
    assert len(result['draws'])==3
    observed=[e for e in cycles if e[1]==0x4e4 and start<e[2]<cursor];assert [e[6] for e in observed]==[d['seed'] for d in result['draws']]
    events=json.loads((folder/f'{region}-audio-irq-events.json').read_text());assert [e[2]-start for e in events if e[1]==0x137 and start<e[2]<cursor]==[e['entry_offset_master'] for e in p['events']]
    rows.append(dict(town=town,mask=mask,region=region,hero_checkpoints=len(loader_result['hero_points'])+1,graphics_checkpoints=len(graphics_result['graphics_points']),pattern_bytes=allocation*32,actor_checkpoints=len(actor_result['actor_points']),history_checkpoints=len(result['history_points']),loader_checkpoints=len(result['loader_points']),draws=result['draws'],foreground_M1=p['foreground_M1'],IRQ_M1=p['IRQ_M1'],exit_R=p['refresh']));print(f'{town:02X}/{mask:02X}',region,'16D0->24E7 actors/history/RNG/M1/R/phase/state exact',flush=True)
 assert rows
 report=dict(cases=len(rows),draws=sum(len(r['draws']) for r in rows),rows=rows,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),production_ROM_changed=False,full_game_ported=False,limits=['Single16D0 full8192RAM/R/raster/audio input; room/HUD/history/persistence derived from initial RAM. No intermediate observed draws,hero RAM orcollision map supplied. Controlled class0 paid exits.','Collision1280 bytes and475 hero entry/return bytes derived from initialRAM/ROM. Gear inputs,331RAM/400audio,history/persistence,actors andwrittenVRAM checked. Script/music/tail/reveal/native integration,other contexts,unsupported audio andfull game remain open.'])
 (ROOT/'analysis/loader_hero_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
