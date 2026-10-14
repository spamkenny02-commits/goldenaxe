"""Actual fairy contexts, prelude/reward icon and capacity/refill/restoration."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels
from validate_key_door_gameplay import initial_room,rle_planes,maps
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  matrix=[('%02x'%t,t,24,3,16,2) for t in [0x18,0x1d,0x82,0xc9,0x32,0xc0,0xe5,0xec]]
  matrix += [('life-limit',0x18,124,100,16,2),('life-full',0x18,128,128,16,2),('magic-limit',0x32,24,3,124,2),('magic-full',0x32,24,3,128,128)]
  if '--walk-only' in sys.argv:matrix=[('walk-life',0x18,24,3,24,2)]
  for name,town,capacity,health,magic_capacity,magic in matrix:
   house=175;item=42 if town in [0x18,0x1d,0x82,0xc9] else 28
   door=next(d for d in doors if d['room']==town and d['target']==house);x,y=136,88 if '--walk-only' in sys.argv else 72
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   traces={};patterns={};source_clock=[];births={};health_changes={};held_tiles={};cell_samples={};huds={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0xda,bytes([capacity])),(3100,0x318,bytes([health])),(3100,0xdc,bytes([magic_capacity])),(3100,0xdb,bytes([magic])),(3100,0x100+town,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['game_save_state']+0x50+town,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_max_health',capacity),(3100,'hero_health',health),(3100,'hero_max_magic',magic_capacity),(3100,'hero_magic',magic),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    rows={};tiles={};arrival=[None];changes=[];last_health=[health];held=[];samples={};hud=[None]
    def observe(f,r):
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[a] for a in [0x318,0xda,0xdb,0xdc,0x100+town]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=r[0xa3]==item;room_cells=bytes(r[0x1c00:0x1ca0])
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_health'),w('hero_max_health'),w('hero_magic'),w('hero_max_magic'),data('game_save_state',0x250)[0x50+town]];current_room=w('room_id');active=w('item_reward_active') and w('item_reward_number')==item;room_cells=data('scratch',0x8a0)[0x800:0x8a0]
     if tag=='md' and f==4300:
      v=data('sms_vram',0x4000);hud[0]=[int.from_bytes(v[0x3d00+n*2:0x3d02+n*2],'little')&0x1fff for n in range(128)]
     if fields[0]!=last_health[0]:changes.append((f,fields[0]));last_health[0]=fields[0]
     if active and arrival[0] is None:arrival[0]=f
     if f in [3700,4300,4800]:
      rows[f]=dict(fields=fields,room=current_room);samples[f]=room_cells
     if f==3500:tiles[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else data('scratch',1040)
    def vram(f,v):
     if tag=='sms' and f==4300:hud[0]=[int.from_bytes(v[0x3d00+n*2:0x3d02+n*2],'little')&0x1fff for n in range(128)]
     if f==3700:
      held.extend(sms_pixels(v,n) if tag=='sms' else md_pixels(v,n+16) for n in list(range(208,236))+list(range(444,448))+list(range(496,502)))
    presses=([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(3125,3145,4),(3600,3604,8),(3900,3904,8)]
    if '--walk-only' in sys.argv:presses.append((3410,3470,4))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,4800,ROOT/f'validation/fairy-{name}-{region}-{tag}',{3500,3700,4300,4800},presses,ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    assert arrival[0] is not None,(region,name,tag,'fairy not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];health_changes[tag]=changes;held_tiles[tag]=held;cell_samples[tag]=samples;huds[tag]=hud[0]
   assert huds['sms']==huds['md'],(region,name,'final HUD visual tile words',huds)
   assert traces['sms']==traces['md'],(region,name,'fields',traces)
   assert patterns['sms']==patterns['md'],(region,name,'prelude bitmap')
   assert held_tiles['sms']==held_tiles['md'],(region,name,'reward font/icon/hero tiles')
   assert [h for f,h in health_changes['sms']]==[h for f,h in health_changes['md']],(region,name,'refill values')
   for tag,changes in health_changes.items():assert all(changes[n][0]-changes[n-1][0]==2 for n in range(1,len(changes))),(tag,changes)
   assert all(r['room']==house for r in traces['md'].values())
   a=(ROOT/f'validation/fairy-{name}-{region}-sms/ram_04300.bin').read_bytes();b=(ROOT/f'validation/fairy-{name}-{region}-md/ram_04300.bin').read_bytes();restored=bytes(b[(sy['sms_vram']+0x3800+n)^1] for n in range(1280))
   animated=set()
   for n in range(160):
    if 0x24<=a[0x1c00+n]<0x30:
     for dy in range(2):
      for dx in range(2):animated.add(((n//16)*2+dy)*32+(n%16)*2+dx)
   map_differences=[n for n in range(640) if restored[n*2:n*2+2]!=a[0x1600+n*2:0x1602+n*2]]
   assert set(map_differences)<=animated,(region,'conditional house static restored room map',map_differences,animated)
   assert traces['md'][4300]==traces['md'][4800], 'reward repeated'
   assert cell_samples['sms'][4300]==cell_samples['md'][4300], (region,name,'transformed room cells')
   cases.append(dict(region=region,scenario=name,town=town,item=item,initial_fields=[health,capacity,magic,magic_capacity],request_frames=births,health_change_frames=health_changes,refill_unit_cadence_two_frames_exact=True,final_fields=traces['md'][4800]['fields'],prelude_bitmap_bytes_exact=1040,reward_pattern_tiles_exact=38,transformed_cells_exact=160,restored_static_map_words_exact=640-len(animated),animated_map_difference_indices=map_differences,final_HUD_visual_words_exact=128,natural_approach_after_door_fixture='--walk-only' in sys.argv,no_second_reward=True));print(region,name,'fairy text/held icon/capacity/refill/restore exact',flush=True)
 limits=['Original source ROM unpatched. Controlled actual doors in all eight life/magic contexts, hero setup and initial clock aligned. Automatic trigger without UP; C3600 acknowledges prelude and3900 reward modal. Additional controlled capacity saturation/full cases, including124 boundary fixtures not claimed naturally acquired.', 'Stable1040 prelude bitmap,38 held font/icon/hero tiles, capacity/refill/visit fields, health-change values/two-frame cadence,160 transformed cells,128 final HUD visual words (bits0..12) and static restored map compare. Animated map words excluded with differences retained. Full frame/music/hardware timing and natural progression unproved.']
 if '--walk-only' in sys.argv:limits[0]='Unpatched original source. Controlled town18 actual door entry and hero placed at136/88, then normal UP movement3410..3470 approaches the fairy; no direct fairy action, visit flag, text or reward state injection. Initial clock aligned, C3600/3900 acknowledgements.'
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/('validation/fairy_walk_gameplay_report.json' if '--walk-only' in sys.argv else 'validation/fairy_gameplay_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
