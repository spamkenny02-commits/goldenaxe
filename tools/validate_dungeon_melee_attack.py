"""Actual12C/113/11C entry: teleport emitters, random placement excluded."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
from audit_item_reward_visuals import sms_pixels,md_pixels
def main(target=0x117,actor_type=0x5f,tile_count=48,initial_flash=0,name='dungeon-melee-attack-5f',verify_boss_sat=False,from_east=False,expected_sat_count=15,mode="allowed"):
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source)
 def room_cells(room):
  out=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,out,0,1);return bytes(out)
 outside=room_cells(16);osms,omd=maps(outside,ext)
 door=next(x for x in json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_dungeon_doors'] if x['room']==16)
 cases=[]
 for region in ['auto','pal']:
  traces={};patterns={};arrivals={};satellites={};cycles={};sats={};source_clock=[];door_sound={}
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
   e=bytearray(768);e[0]=actor_type;e[1]=10;e[3]=0x23;e[4]=0;e[8:10]=bytes.fromhex('d997');e[0x11]=80;e[0x13]=128;e[10]=0;e[12]=4;e[13]=11;e[0x18:0x1b]=source[0x320ea+(actor_type-32)*4:0x320ea+(actor_type-32)*4+3]
   def word(address):return int.from_bytes(source[0x30000+(address&0x3fff):0x30002+(address&0x3fff)],'little')
   address=word(word(0x97d9+e[10]*2));off=0x30000+(address&0x3fff);e[0x1b:0x1d]=source[off+1:off+3]
   if tag=='sms':writes += [(3700,0x600,e),(3700,0x301,b'\x01'),(3700,0x303,b'\x03\0\0'),(3700,0x30a,b'\x01\0'),(3700,0x310,(64<<8).to_bytes(2,'little')+(128<<8).to_bytes(2,'little')+bytes(4))]
   else:
    writes.append((3700,sy['world_actor_state'],e))
    for k,value in [('hero_state',1),('hero_flags',3),('hero_counter',0),('hero_hurt',0),('hero_animation',0),('hero_direction',1),('hero_y',64<<8),('hero_x',128<<8),('hero_dy',0),('hero_dx',0)]:add(3700,k,value)
   if tag=='sms':writes += [(3400,0x305,b'\xff'),(3400,0x318,b'\x18'),(3650,0x301,b'\x01'),(3650,0x303,b'\x03\0\xff'),(3650,0x310,(64<<8).to_bytes(2,'little')+(128<<8).to_bytes(2,'little')+bytes(4)),(3700,0x318,b'\x18')]
   else:
    add(3400,'hero_hurt',255);add(3400,'hero_health',24);add(3700,'hero_health',24)
    for k,value in [('hero_state',1),('hero_flags',3),('hero_counter',0),('hero_hurt',255),('hero_y',64<<8),('hero_x',128<<8),('hero_dy',0),('hero_dx',0)]:add(3650,k,value)
   rows={};tiles={};sprites={};arrival=[None];cycle={};cycle_sat={};setup_sound={}
   def observe(f,r):
    if f==3699:
     if tag=='sms':source_clock.append(r[0x2f])
     else:
      read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0]
      writes.append((3700,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
    if 3650<=f<=3660:
     setup_sound[f]=[r[0x1e08],r[0x1e05]] if tag=='sms' else [int.from_bytes(bytes(r[(sy['sound_effect_request']+i)^1] for i in range(2)),'big'),r[(sy['sound_ram']+5)^1]]
    if f<3400:return
    if tag=='sms':actors=bytes(r[0x600:0x900]);room=int.from_bytes(r[0xb9:0xbb],'little');state=r[0x1d]
    else:
     def data(k,n):return bytes(r[(sy[k]+i)^1] for i in range(n))
     actors=data('world_actor_state',768);room=int.from_bytes(data('room_id',2),'big');state=int.from_bytes(data('game_state',2),'big')
    if 3700<=f<3734:
     if tag=='sms':cycle[f]=actors+bytes([r[0x301],r[0x30b],r[0xdd],r[0x1e08],r[0x1e05],r[0x318],r[0x305]])+bytes(r[0x310:0x318])
     else:
      def w(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
      cycle[f]=actors+bytes([w('hero_state'),w('hero_animation'),w('hero_gold'),w('sound_effect_request'),r[(sy['sound_ram']+5)^1],w('hero_health'),w('hero_hurt')])+b''.join(w(k).to_bytes(2,'little') for k in ['hero_y','hero_x','hero_dy','hero_dx'])
    if arrival[0] is None and room==target and actors[0]==actor_type and actors[1]==2 and actors[5]==initial_flash:arrival[0]=f
    if arrival[0] is not None and 0<=f-arrival[0]<30:rows[f-arrival[0]]=bytes(v for i,v in enumerate(actors[:48]) if i not in [10,17,19])
   def vram(f,v):
    if arrival[0] is None:return
    step=f-arrival[0]
    if step in [5,15,25]:tiles[step]=[sms_pixels(v,256+n) if tag=='sms' else md_pixels(v,272+n) for n in range(tile_count)]
    if 3700<=f<3734:
     entries=[]
     if tag=='sms':
      for n in range(64):
       if v[0x3f00+n]==0xd0:break
       tile=v[0x3f81+n*2]
       if tile<48 or tile>=240:entries.append([v[0x3f00+n],v[0x3f80+n*2],tile])
     else:
      word=lambda a:int.from_bytes(bytes([v[a^1],v[(a+1)^1]]),'big');n=0
      for count in range(80):
       a=0xf400+n*8;tile=(word(a+4)&0x7ff)-272
       if 0<=tile<48 or 240<=tile<256:entries.append([(word(a)-145)&255,(word(a+6)-128)&255,tile])
       n=word(a+2)&127
       if not n:break
     cycle_sat[f]=entries
   with contextlib.redirect_stdout(io.StringIO()):run(rom,3800,ROOT/f'validation/{name}-entry-{region}-{tag}',{3510,3540,3698,3699,3700,3701,3702,3703,3704,3710},([(200,220,0)] if tag=='sms' else [])+PRESSES+[(3125,3129,4),(3400,3403,6 if from_east else 7)],ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
   assert arrival[0] is not None and len(rows)==30,(tag,region,arrival[0],len(rows))
   traces[tag]=rows;patterns[tag]=tiles;arrivals[tag]=arrival[0];satellites[tag]=sprites
   cycles[tag]=cycle;sats[tag]=cycle_sat;door_sound[tag]=setup_sound
  assert traces['sms']==traces['md'],(region,'first hunter appearance records excluding random fields differ')
  assert patterns['sms']==patterns['md'],(region,'loaded boss pattern pixels differ')
  (ROOT/f'validation/melee-attack-sat-diagnostic-{region}.json').write_text(json.dumps(sats,indent=2)+'\n')
  assert door_sound['sms']==door_sound['md'],(region,'door A5 effect queue/current state',door_sound)
  assert cycles['md'][3733][1]==4 and cycles['md'][3733][10]==1,(region,'attack reset/reversal')
  assert cycles['md'][3733][773]<24,(region,'hero attack damage not exercised')
  for f in range(3700,3734):
   a,b=cycles['sms'][f],cycles['md'][f];assert a==b,(region,'cycle actor',f,[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y][:15])
  differences=[dict(frame=f,sms=sats['sms'][f],md=sats['md'][f]) for f in range(3701,3734) if sats['sms'][f]!=sats['md'][f]]
  diagnostic=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),region=region,type=actor_type,room=target,all_768_actor_bytes_and_hero_state_animation_gold_HP_hurt_position_velocity_and_effects_exact_frames=34,sat_exact_frames=33-len(differences),sat_differences=differences,hero_final_HP=cycles['md'][3733][773],attack_reset_and_reversal_exact=True,full_game_ported=False,limits=['Controlled actual-room attack, initial clock alignment.','Sprite order difference retained as unresolved renderer discrepancy; no relaxed SAT assertion.' if differences else 'All33 post-fixture actual SAT frames match, including order; strict assertion unchanged.'])
  (ROOT/f'validation/{name.replace("-","_")}_{region}_diagnostic.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
  assert not differences,(region,'actual SAT',differences[0] if differences else None)
  cases.append(dict(region=region,room=target,type=actor_type,arrival_frames=arrivals,relative_first_actor_frames_except_random_fields_exact=30,excluded_random_record_offsets=[10,17,19],loaded_pattern_tiles_exact=tile_count,pattern_samples=3,enemy_attack_animation_and_damage=True,setup_door_sound_request_and_effect_exact=door_sound,controlled_cycle_actor_hero_gold_sound_frames_exact=34,controlled_cycle_sat_frames_exact=33,hero_and_melee_sat_order_compared=True,explicit_initial_clock_alignment=True,excluded_fixture_sat_frame=3700,fixture_frame_sat={tag:sats[tag][3700] for tag in sats}))
  print(region,hex(target),'production scroll/load, 30 appearance records excluding random X/Y/direction and',tile_count,'loaded tiles exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled exterior doorway/departure setup, normal right scroll and real destination scripts/resources. First30 appearance frames exclude random X/Y/direction; initialization alignment does not prove absolute loading cadence.','At3400 hero HP24/invulnerability255 protect setup. Hero alone relocates3650 to128,64 allowing foreground work to settle. At3700 all actors are replaced by one melee actor128,80 in attack state10, facing up, descriptor97D9 period11/count4; hero128,64 facing down/state1/hurt0/HP24. Native clock aligns explicitly. No attack button is pressed. Real room terrain/resources remain.34 frames compare all768 actor bytes, hero state/animation/gold/HP/hurt/XY/velocities and secondary request/current effect. Attack hurts hero and ends with opposite heading/state4.33 actual SAT frames3701..3733 compare hero and first48 enemy tiles including ordering/overlap; injection3700 SAT is excluded and recorded because source still has prior sprites.','Full natural approach/attack decisions, original RNG/global clock, full framebuffer/audio and hardware timing remain unproved.'])
 (ROOT/f'validation/{name.replace("-","_")}_entry_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
 main()
 main(target=0x138,actor_type=0x60,tile_count=48,name='dungeon-melee-attack-60')
