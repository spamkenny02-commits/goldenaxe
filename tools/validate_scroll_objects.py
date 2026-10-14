"""Visible enemies/loot disappear at exterior scroll start, in all four directions."""
import contextlib,hashlib,io,json,re,sys
from run_core import ROOT,run
from validate_actor_tick import PRESSES

def main():
 pal='--pal' in sys.argv;suffix='-pal' if pal else '';options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'}
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 original=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin'
 template=bytearray((ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630])
 actors=bytearray(768)
 for slot,(x,y) in [(0,(80,64)),(8,(160,112))]:
  e=bytearray(template);e[3]=1;e[4]=120;e[5]=0;e[6]=255;e[0x10:0x18]=bytes(8);e[0x11]=y;e[0x13]=x;actors[slot*48:(slot+1)*48]=e
 loot=bytearray(336);loot[0]=8;loot[1]=4;loot[2]=0x92;loot[3]=1;loot[8:10]=bytes.fromhex('ce84');loot[14]=240;loot[0x11]=80;loot[0x13]=128
 results=[]
 for label,x,y in [('left',14,80),('right',242,80),('up',128,14),('down',128,162)]:
  records={}
  for tag,rom in [('sms',original),('md',md)]:
   samples={};current=None
   writes=[(3127,0x600,bytes(actors)),(3127,0x4b0,bytes(loot)),(3131,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little'))] if tag=='sms' else [(3127,sy['world_actor_state'],bytes(actors)),(3127,sy['world_loot_state'],bytes(loot)),(3131,sy['hero_y'],(y<<8).to_bytes(2,'big')),(3131,sy['hero_x'],(x<<8).to_bytes(2,'big'))]
   def ram(f,d):
    nonlocal current
    if f<3127:return
    if tag=='md':
     d=bytearray(d);d[::2],d[1::2]=d[1::2],d[::2]
     val=lambda k:int.from_bytes(d[sy[k]:sy[k]+2],'big')
     flags=[d[sy['world_actor_state']+i*48+3] for i in range(16)]
     transient=[d[sy['world_loot_state']+i*48+3] for i in range(7)]+[d[sy['world_spell_state']+3]]
     state=val('game_state');room=val('room_id');step=val('transition_step');stage=val('transition_stage')
     types=bytes(d[sy['world_actor_state']+i*48] for i in range(16));mask=d[sy['game_save_state']+0x150+0xa4]
    else:
     flags=[d[0x600+i*48+3] for i in range(16)];transient=[d[0x4b0+i*48+3] for i in range(7)]+[d[0x333]]
     state=d[0x1d];room=int.from_bytes(d[0xb9:0xbb],'little');step=stage=None;types=bytes(d[0x600+i*48] for i in range(16));mask=d[0x2a4]
    current=dict(frame=f,state=state,room=room,flags=flags,transient_flags=transient,step=step,stage=stage,actor_types=types.hex(),saved_mask=mask)
    samples[f]=current
   def vram(f,v):
    if f<3127:return
    entries=[]
    if tag=='sms':
     for i in range(64):
      y=v[0x3f00+i]
      if y==208:break
      entries.append(dict(y=y,x=v[0x3f80+i*2],tile=v[0x3f81+i*2]))
     others=[e for e in entries if e['tile']<240]
    else:
     i=0;seen=set()
     while i not in seen and len(seen)<80:
      seen.add(i);p=0xf400+i*8;y=int.from_bytes(v[p:p+2],'little')&511;x=int.from_bytes(v[p+6:p+8],'little')&511;tile=int.from_bytes(v[p+4:p+6],'little')&2047
      if x and y:entries.append(dict(y=y-128,x=x-128,tile=tile))
      i=int.from_bytes(v[p+2:p+4],'little')&127
      if not i:break
     others=[e for e in entries if 272<=e['tile']<512]
    current['nonhero_sprites']=others;current['sprite_count']=len(entries)
   folder=ROOT/f'validation/{tag}-scroll-objects-{label}{suffix}'
   with contextlib.redirect_stdout(io.StringIO()):run(rom,3230,folder,{3129,3135,3145},([(200,220,0)] if tag=='sms' else [])+PRESSES,ram_writes=writes,ram_observer=ram,vram_observer=vram,core_options=options)
   records[tag]=samples
  checks={}
  for tag,samples in records.items():
   assert samples[3129]['nonhero_sprites'],(tag,label,'fixture must be visible before crossing')
   transition=[d for d in samples.values() if d['state']==10]
   assert transition,(tag,label,'no scroll')
   # Source state 10 includes setup work before the rebuilt SAT is uploaded.
   # It can retain the old SAT during setup, before map scrolling begins.
   clean=next(d['frame'] for d in transition if not d['nonhero_sprites'])
   stable=[d for d in transition if d['frame']>=clean] if tag=='sms' else [d for d in transition if d['frame']>transition[0]['frame']]
   errors=[d for d in stable if d['nonhero_sprites']]
   assert not errors,(tag,label,'non-hero sprites during scroll',errors[:3])
   assert transition[0]['saved_mask']==128,(tag,label,'living primary actor lost from persistence')
   old=[d for d in transition if d['actor_types']==bytes(actors[::48]).hex()]
   assert old and all(not any(d['flags']+d['transient_flags']) for d in old),(tag,label,'old object flags not cleared')
   post=[d for d in samples.values() if d['frame']>transition[-1]['frame'] and d['state']==12]
   assert post,(tag,label,'never resumes gameplay')
   if label!='up':assert any(d['nonhero_sprites'] for d in post),(tag,label,'destination actors never become visible')
   checks[tag]=dict(first_transition_frame=transition[0]['frame'],first_clean_sat_frame=clean,last_transition_frame=transition[-1]['frame'],checked_transition_frames=len(stable),nonhero_sprites_before_scroll=len(samples[3129]['nonhero_sprites']),nonhero_sprite_errors=len(errors),old_object_flags_cleared=True,primary_living_mask_preserved=True,hero_sprite_frames=sum(bool(d['sprite_count']) for d in stable),destination_nonhero_sprite_frames=sum(bool(d['nonhero_sprites']) for d in post),gameplay_resumes=True)
  results.append(dict(direction=label,checks=checks))
  print('Scroll objects hidden',label,suffix,checks)
 report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),region='pal' if pal else 'auto',source_routine='21A1..21C2 / 0938',cases=results,hardware_sat_checked=True,fixtures='Two visible frozen actors, including an auxiliary slot, and one dropped coin; real edge crossing. Test-only initial object/edge position RAM writes.',scope='Old objects hidden throughout four exterior scroll directions, hero retained, persistence mask retained; all enemy AI and whole-game fidelity remain unproven.')
 (ROOT/f'validation/scroll_objects{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
