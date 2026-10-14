"""Normal doors and UP interactions for six quest gifts in real house resources."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
from audit_item_reward_visuals import sms_pixels,md_pixels
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  hint=True
  for town,item,basic,armor,capacity,defeat in ([(0xb3,0,1,1,24,0)] if hint else [(0x27,22,1,1,24,0),(0xb1,23,1,2,24,0),(0x50,2,1,1,56,0),(0x6a,3,2,1,24,0),(0x92,12,1,1,24,0),(0x4c,26,1,1,24,128)]):
   door=next(d for d in doors if d['room']==town and d['target']==143);house=door['target'];x,y=(168,56) if house==9 else (104,56) if house==15 else ((136,72) if hint else (120,72))
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   traces={};patterns={};source_clock=[];births={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0xe4,b'\x01'),(3100,0xe0,bytes([basic])),(3100,0xf1,bytes([armor])),(3100,0xbf,b'\x01'),(3100,0xda,bytes([capacity])),(3100,0xd4,bytes([defeat])),(3100,0xe8,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['hero_items']+4,b'\x01'),(3100,sy['hero_items'],bytes([basic])),(3100,sy['game_save_state']+15,b'\x01'),(3100,sy['game_save_state']+0x24,bytes([defeat])),(3100,sy['hero_items']+8,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_basic_level',basic),(3100,'hero_armor_level',armor),(3100,'hero_max_health',capacity),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    rows={};tiles={};arrival=[None]
    def observe(f,r):
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[a] for a in [0xe0,0xe4,0xf1,0xf2,0xbf,0xe8,0xe2,0xda]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=(r[0xa3]==item and fields[0 if item in [2,3] else 2 if item in [22,23] else 5 if item==12 else 3]==(2 if item in [2,22] else 3 if item in [3,23,26] else 1)) if not hint else f>=3430 and current_room==house
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_basic_level'),data('hero_items',17)[4],w('hero_armor_level'),w('hero_shield_level'),data('game_save_state',16)[15],data('hero_items',17)[8],data('hero_items',17)[2],w('hero_max_health')];current_room=w('room_id');active=(w('item_reward_active') and w('item_reward_number')==item) if not hint else w('house_dialogue_active') 
     if active and arrival[0] is None:arrival[0]=f
     if f in ([3850,3960,4000] if hint else [3500,3800,3900]):
      rows[f]=dict(fields=fields,room=current_room)
      if hint and f==3850:tiles[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else data('scratch',1040)
    def vram(f,v):
     if hint or f!=3500:return
     indices=list(range(208,236))+list(range(444,448))+list(range(496,502));tiles[f]=[sms_pixels(v,n) if tag=='sms' else md_pixels(v,n+16) for n in indices]
    with contextlib.redirect_stdout(io.StringIO()):run(rom,4000,ROOT/f'validation/plain-house{"-hint" if hint else ""}-{town:02x}-{region}-{tag}',({3500,3850,3960,4000} if hint else {3500,3800,3900}),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(3125,3145,4),(3410,3410 if hint else 3430,4)]+([(3600,3604,8),(3900,3904,8)] if hint else [(3700,3704,8)]),ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    assert arrival[0] is not None,(region,hex(town),tag,'gift not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0]
   assert traces['sms']==traces['md'],(region,hex(town),'gift fields/restore',traces)
   assert patterns['sms']==patterns['md'],(region,hex(town),'reward icon/font/hero pixels','retained differing patterns')
   assert all(r['room']==house for r in traces['md'].values())
   if item in [22,23]:assert traces['md'][3900]['fields'][4]==0 and traces['md'][3900]['fields'][0]==basic
   if item in [2,3]:assert traces['md'][3900]['fields'][2]==armor
   if hint:
    a=(ROOT/f'validation/plain-house-hint-{town:02x}-{region}-sms/ram_04000.bin').read_bytes();b=(ROOT/f'validation/plain-house-hint-{town:02x}-{region}-md/ram_04000.bin').read_bytes();restored=bytes(b[(sy['sms_vram']+0x3800+n)^1] for n in range(1280))
    animated=set()
    for n in range(160):
     if 0x24<=a[0x1c00+n]<0x30:
      for dy in range(2):
       for dx in range(2):animated.add(((n//16)*2+dy)*32+(n%16)*2+dx)
    map_differences=[n for n in range(640) if restored[n*2:n*2+2]!=a[0x1600+n*2:0x1602+n*2]]
    assert set(map_differences)<=animated,(region,'long hint static restored room map',map_differences,animated)
   cases.append(dict(region=region,town=town,house=house,text_pc=0x9740,request_frames=births,equipment_inventory_curse_capacity_and_room_samples_exact=3,reward_pattern_tiles_exact=0 if hint else 38,long_dialogue_bitmap_bytes_exact=1040 if hint else 0,restored_static_map_words_exact=640-len(animated) if hint else None,animated_map_difference_indices=map_differences if hint else [],normal_door_UP_and_C_return=True,initial_clock_aligned=True));print(region,hex(town),'plain263-byte dialogue, bitmap and static restoration exact',flush=True)
 if hint:
  limits=['Controlled actual townB3 door/house resources, magic owned and HP capacity24. One-frame UP starts original263-byte mountain/climbing dialogue; C pulses3600/3900 acknowledge intermediate/final pages. Hero fixture and initial clock aligned at3400; no direct dialogue/text/state mutation after setup.', 'Stable final1040 bitmap bytes at3850 and restored equipment/room fields at3960/4000 compare in PAL/NTSC. Animated NPC map cells are excluded from static restoration and raw differing word indices retained. Full dialogue publication timing, all intermediate pixels/audio and natural quest progression remain unproved.']
 else:limits=['Six controlled real town-door gifts with initial clock alignment; no direct gift or post-setup VRAM mutation.', 'Three equipment/curse/room field samples and38 font/icon/hero tiles per gift compare. Complete natural quest progression, full frames/audio and hardware timing remain unproved.']
 report=dict(long_hint=hint,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/'validation/plain_house_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
