"""Actual181/15C sentinel fixed placements and resources."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
from audit_item_reward_visuals import sms_pixels,md_pixels
def main(target=0x181,actor_type=0x57,tile_count=44,initial_flash=0,name='dungeon-sentinel-approach-57',verify_boss_sat=False,from_east=False,expected_sat_count=15):
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source)
 def room_cells(room):
  out=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,out,0,1);return bytes(out)
 outside=room_cells(16);osms,omd=maps(outside,ext)
 door=next(x for x in json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_dungeon_doors'] if x['room']==16)
 cases=[]
 for region in ['auto','pal']:
  traces={};patterns={};arrivals={};satellites={};approaches={};starts={};actual_sats={};source_clock=[];initial_animations={}
  for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
   writes=[]
   def add(f,k,v,n=2):writes.append((f,sy[k],v.to_bytes(n,'big')))
   if tag=='sms':
    writes=[(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,outside),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),
     (3400,0xb9,(target-1).to_bytes(2,'little')),(3400,0xa4,b'\x61\xb7'),(3400,0x100+(target&255),b'\x10'),(3400,0x6e,b'\xff\xff\0'),(3400,0x600,bytes(768)),(3400,0xa2,b'\0'),(3400,0x301,b'\0'),(3400,0x303,b'\x03\0'),(3400,0x30a,b'\x03'),(3400,0x310,(80<<8).to_bytes(2,'little')+(241<<8).to_bytes(2,'little')+bytes(4)),(3400,0x1600,bytes(1280))]
   else:
    for f,k,v in [(3120,'room_id',16),(3120,'world_graphics_class',0),(3120,'hero_y',(door['y']+8)<<8),(3120,'hero_x',door['x']<<8),(3400,'room_id',target-1),(3400,'world_actor_count',0),(3400,'hero_state',0),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_direction',3),(3400,'hero_y',80<<8),(3400,'hero_x',241<<8),(3400,'hero_dy',0),(3400,'hero_dx',0)]:add(f,k,v)
    writes += [(3120,sy['scratch']+0x800,outside),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768)),(3400,sy['game_save_state']+0x50+(target&255),b'\x10'),(3400,sy['room_metadata'],b'\xff\xff\0'),(3400,sy['sms_vram']+0x3800,bytes(1280)),(3400,sy['world_actor_state'],bytes(768))]
   if from_east:
    replacements={0xb9:(target+1).to_bytes(2,'little'),0x30a:b'\x02',0x310:(80<<8).to_bytes(2,'little')+(14<<8).to_bytes(2,'little')+bytes(4)} if tag=='sms' else {sy['room_id']:(target+1).to_bytes(2,'big'),sy['hero_direction']:(2).to_bytes(2,'big'),sy['hero_x']:(14<<8).to_bytes(2,'big')}
    writes=[(f,a,replacements.get(a,b) if f==3400 else b) for f,a,b in writes]
   hx,hy=(80,64) if actor_type==0x57 else (32,80)
   if tag=='sms':writes += [(3600,0x301,b'\x01'),(3600,0x303,b'\x03\0\0'),(3600,0x318,b'\x18'),(3600,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
   else:
    for k,value in [('hero_state',1),('hero_flags',3),('hero_counter',0),('hero_hurt',0),('hero_health',24),('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0)]:add(3600,k,value)
   writes += [(3600,(0x600 if tag=='sms' else sy['world_actor_state'])+i,b'\0') for i in [11,14]]
   rows={};tiles={};sprites={};arrival=[None];approach={};start=[None];actual_sat={}
   def observe(f,r):
    if f==3599:
     if tag=='sms':
      source_clock.append(r[0x2f]);initial_animations[tag]=[r[0x60b],r[0x60e]]
     else:
      initial_animations[tag]=[r[(sy['world_actor_state']+i)^1] for i in [11,14]]
      read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0]
      writes.append((3600,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
    if f<3400:return
    if tag=='sms':actors=bytes(r[0x600:0x900]);room=int.from_bytes(r[0xb9:0xbb],'little');state=r[0x1d]
    else:
     def data(k,n):return bytes(r[(sy[k]+i)^1] for i in range(n))
     actors=data('world_actor_state',768);room=int.from_bytes(data('room_id',2),'big');state=int.from_bytes(data('game_state',2),'big')
    if 3600<=f<3700:
     approach[f]=actors[:48]
     if start[0] is None and actors[1]==10:start[0]=f
    if arrival[0] is None and room==target and actors[0]==actor_type and actors[1]==2 and actors[5]==initial_flash:arrival[0]=f
    if arrival[0] is not None and 0<=f-arrival[0]<30:rows[f-arrival[0]]=actors[:48]
   def vram(f,v):
    if arrival[0] is None:return
    step=f-arrival[0]
    if step in [5,15,25]:tiles[step]=[sms_pixels(v,256+n) if tag=='sms' else md_pixels(v,272+n) for n in range(tile_count)]
    if 3600<=f<3700:
     entries=[]
     if tag=='sms':
      for n in range(64):
       if v[0x3f00+n]==0xd0:break
       tile=v[0x3f81+n*2]
       if tile<8:entries.append([v[0x3f00+n],v[0x3f80+n*2],tile])
     else:
      word=lambda a:int.from_bytes(bytes([v[a^1],v[(a+1)^1]]),'big');n=0
      for count in range(80):
       a=0xf400+n*8;tile=(word(a+4)&0x7ff)-272
       if 0<=tile<8:entries.append([(word(a)-145)&255,(word(a+6)-128)&255,tile])
       n=word(a+2)&127
       if not n:break
     actual_sat[f]=entries
   with contextlib.redirect_stdout(io.StringIO()):run(rom,3800,ROOT/f'validation/{name}-entry-{region}-{tag}',{3510,3540},([(200,220,0)] if tag=='sms' else [])+PRESSES+[(3125,3129,4),(3400,3403,6 if from_east else 7),(3600,3625,7)],ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
   assert arrival[0] is not None and len(rows)==30,(tag,region,arrival[0],len(rows))
   traces[tag]=rows;patterns[tag]=tiles;arrivals[tag]=arrival[0];satellites[tag]=sprites
   approaches[tag]=approach;starts[tag]=start[0];actual_sats[tag]=actual_sat
  assert traces['sms']==traces['md'],(region,'first hunter appearance records excluding random fields differ')
  assert patterns['sms']==patterns['md'],(region,'loaded boss pattern pixels differ')
  assert starts['sms']==starts['md'] and starts['sms'] is not None,(region,'normal-button proximity activation time',starts)
  begin=starts['sms'];span=33 if actor_type==0x57 else 32
  for f in range(begin,begin+span):
   a,b=approaches['sms'][f],approaches['md'][f];assert a==b,(region,'approach record',f,[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y][:15])
   assert actual_sats['sms'][f]==actual_sats['md'][f],(region,'actual activation SAT',f,actual_sats['sms'][f],actual_sats['md'][f])
  cases.append(dict(region=region,room=target,type=actor_type,arrival_frames=arrivals,relative_first_actor_all_48_bytes_exact=30,excluded_random_record_offsets=[],loaded_pattern_tiles_exact=tile_count,pattern_samples=3,normal_button_activation_frames=starts,activation_record_and_sat_frames_exact=span,explicit_initial_approach_clock_alignment=True,initial_animation_before_reset=initial_animations,explicit_common_animation_reset_offsets=[11,14],activation_sat={tag:{f:actual_sats[tag][f] for f in range(begin,begin+span)} for tag in actual_sats}))
  print(region,hex(target),'production scroll/load, 30 appearance records with fixed X/Y/direction and',tile_count,'loaded tiles exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=[f'Normal dungeon doorway entry after exterior relocation; controlled relocation to room{target-1:03x} boundary with cleared actors and passable departure map. Right scroll and actual destination{target:03x} scripts/resources/actor loading execute normally.',f'Actor timelines aligned to first initialized core frame, not absolute loading cadence; Thirty first sentinel records compare all48 bytes including fixed X/Y/direction and hidden flags; no random actor fields are excluded. Other actor records are not compared. First {tile_count} sprite pattern pixels sampled at three relative frames. At3600 hero state/position/HP and first-sentinel animation offsets11/14 are normalized (80,64 for57;32,80 for58), native clock explicitly aligned, and normal right input approaches the loaded sentinel with original fixed position/state/flags. After explicit common animation reset, activation time and33/32 full first-record/SAT frames compare without timeline shift. Other actors, full natural travel/fight, full framebuffer, audio and full transition timing remain unproved.'])
 if from_east:report['limits'][0]=f'Normal dungeon doorway entry after exterior relocation; controlled relocation to room{target+1:03x} boundary with cleared actors and passable departure map. Left scroll and actual destination{target:03x} scripts/resources/actor loading execute normally.'
 (ROOT/f'validation/{name.replace("-","_")}_entry_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
 main()
 main(target=0x15c,actor_type=0x58,name='dungeon-sentinel-approach-58')
