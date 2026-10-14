"""Original/native gem appearance and actual modal collection through game loops."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 resources=json.loads((ROOT/'analysis/gem_resources.json').read_text())['records'];cases=[]
 edges='--edges' in sys.argv;walk='--walk' in sys.argv;dungeon_scene='--dungeon' in sys.argv;boss='--boss' in sys.argv;particles='--particles' in sys.argv;shift=600 if dungeon_scene else 0
 trials=[(1,120),(1,128)] if edges else [(d,24) for d in ([1] if '--focus' in sys.argv or walk or dungeon_scene else range(1,10))]
 for region in ['auto','pal']:
  for dungeon,capacity in trials:
   records={};patterns={};expected=resources[dungeon-1];item=expected['item']
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[];e=bytearray(768);e[0]=15
    if boss:
     e[0]=0x64;e[3]=0x40;e[6]=1;e[0x18]=e[0x1d]=1;e[0x11]=96;e[0x13]=128
    def add(f,k,v,n=2):writes.append((f,sy[k],v.to_bytes(n,'big')))
    if tag=='sms':
     writes=[(2800,0x600,e),(2800,0x37,bytes([dungeon])),(2800,0xae,b'\x55'),(2800,0xda,bytes([capacity,5,24])),(2800,0x318,bytes([24 if capacity==24 else capacity-8]))]+([] if walk else [(3000,0x603,b'\x07')])
    else:
     writes=[(2800,sy['world_actor_state'],e)]+([] if walk else [(3000,sy['world_actor_state']+3,b'\x07')])
     for k,v,n in [('world_dungeon_number',dungeon,2),('world_boss_state',0x55,1),('hero_max_health',capacity,2),('hero_health',24 if capacity==24 else capacity-8,2),('hero_magic',5,2),('hero_max_magic',24,2)]:add(2800,k,v,n)
    if boss and not particles:
     occupied=bytearray(384)
     for slot in range(8):occupied[slot*48]=1;occupied[slot*48+1]=2;occupied[slot*48+6]=255
     a=0x780 if tag=='sms' else sy['world_actor_state']+0x180
     writes += [(2802,a,occupied),(2985,a,bytes(384))]
    if walk:
     if tag=='sms':writes += [(2800,0x310,(80<<8).to_bytes(2,'little')+(128<<8).to_bytes(2,'little')+bytes(4)),(2800,0x1600,bytes(1280))]
     else:
      writes.append((2800,sy['sms_vram']+0x3800,bytes(1280)))
      for k,v in [('hero_y',80<<8),('hero_x',128<<8),('hero_dy',0),('hero_dx',0)]:add(2800,k,v)
    if dungeon_scene:
     from validate_key_door_gameplay import initial_room,rle_planes,maps
     source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source)
     meta=bytearray(2048);pats=bytearray(16384);end,_=rle_planes(arrays['world_dungeon_background_rle'],0,pats,0,4);rle_planes(arrays['world_dungeon_background_rle'],end,meta,0,2)
     def room_cells(room):
      out=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,out,0,1);return bytes(out)
     door=next(x for x in json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_dungeon_doors'] if x['room']==16)
     outside=room_cells(16);osms,omd=maps(outside,ext);cells=room_cells(0x115);bsms,bmd=maps(cells,meta)
     writes=[(f+shift,a,v) for f,a,v in writes]
     if tag=='sms':writes += [(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,outside),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),(3400,0xb9,b'\x15\x01'),(3400,0xa4,b'\x61\xb7'),(3400,0x115,b'\x10'),(3400,0x6e,b'\xff\xff\0'),(3400,0x1c00,cells),(3400,0x1600,bsms),(3400,0xa2,b'\x01'),(3400,0x65,b'\x86')]
     else:
      for f,k,v in [(3120,'room_id',16),(3120,'world_graphics_class',0),(3120,'hero_y',(door['y']+8)<<8),(3120,'hero_x',door['x']<<8),(3400,'room_id',0x115),(3400,'world_actor_count',1),(3400,'sound_current_track',0x86)]:add(f,k,v)
      writes += [(3120,sy['scratch']+0x800,outside),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768)),(3400,sy['game_save_state']+0x65,b'\x10'),(3400,sy['room_metadata'],b'\xff\xff\0'),(3400,sy['scratch']+0x800,cells),(3400,sy['sms_vram']+0x3800,bsms),(3400,sy['world_new_md'],bmd)]
     writes.sort(key=lambda x:x[0])
    rows={};tiles={}
    def observe(f,r):
     f-=shift
     if f not in [2801,2803,2810,2990,3100,3400] and not (boss and 2800<=f<=2990):return
     if tag=='sms':rows[f]=dict(entity=bytes(r[0x600:0x630]).hex(),particle_pool=bytes(r[0x780:0x900]).hex(),flags=bytes(r[0x100:0x200]).hex(),progress=r[0xce+dungeon],max_health=r[0xda],health=r[0x318],magic=r[0xdb],boss_state=r[0xae],reward=r[0xa3],state=r[0x1d],music=r[0x65],window_map=bytes(r[0x1b00:0x1c00]).hex())
     else:
      def data(k,n,off=0):return bytes(r[(sy[k]+off+i)^1] for i in range(n))
      def w(k):return int.from_bytes(data(k,2),'big')
      rows[f]=dict(entity=data('world_actor_state',48).hex(),particle_pool=data('world_actor_state',384,0x180).hex(),flags=data('game_save_state',256,0x50).hex(),progress=data('game_save_state',1,0x1e+dungeon)[0],max_health=w('hero_max_health'),health=w('hero_health'),magic=w('hero_magic'),boss_state=data('world_boss_state',1)[0],reward=w('item_reward_number'),state=w('game_state'),music=w('sound_current_track'),window_map=data('sms_vram',256,0x3d00).hex(),active=w('item_reward_active'))
    def vram(f,v):
     f-=shift
     if f not in [2801,2803,2810,2990,3100,3400]:return
     pixels=lambda n:sms_pixels(v,n) if tag=='sms' else md_pixels(v,16+n)
     tiles[f]=dict(icon=[pixels(444+n) for n in range(4)],font=[pixels(208+n) for n in range(28)],hero=[pixels(496+n) for n in range(6)])
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3400+shift,ROOT/f'validation/gem-{dungeon}-{capacity}-{region}-{tag}{"-boss-particles-dungeon" if boss and particles and dungeon_scene else "-boss-particles" if boss and particles else "-boss-dungeon" if boss and dungeon_scene else "-boss" if boss else "-dungeon" if dungeon_scene else "-walk" if walk else ""}',{2803+shift,2900+shift,3100+shift,3400+shift},([(200,220,0)] if tag=='sms' else [])+(PRESSES+[(3125,3129,4)] if dungeon_scene else PRESSES[:8])+([(2810,2850,4)] if walk else [])+[(3250+shift,3253+shift,8)],ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    records[tag]=rows;patterns[tag]=tiles
   for f in (range(2800,2991) if boss else [2801,2803,2810,2990]):
    for k in ['entity','flags','progress','max_health','health','magic','boss_state','state','music']:assert records['sms'][f][k]==records['md'][f][k],(region,dungeon,f,k,records['sms'][f][k],records['md'][f][k])
   for k in ['entity','flags','progress','max_health','health','magic','boss_state','state','music']:assert records['sms'][3400][k]==records['md'][3400][k],(region,dungeon,'settled',k,records['sms'][3400][k],records['md'][3400][k])
   if boss:
    trace=records['md'];assert bytes.fromhex(trace[2800]['entity'])[0]==7
    assert bytes.fromhex(trace[2801]['entity'])[0x28]==180 and trace[2801]['progress']==1
    assert bytes.fromhex(trace[2981]['entity'])[1]==4 and bytes.fromhex(trace[2982]['entity'])[0]==15
    assert bytes.fromhex(trace[2983]['entity'])[0x11]==28
   if boss and particles:
    for tag in ['sms','md']:
     seen=0
     for f in range(2801,2982):
      pool=bytes.fromhex(records[tag][f]['particle_pool'])
      for n in range(8):
       e=pool[n*48:n*48+48]
       assert e[0] in [0,1],(region,dungeon,tag,f,'particle type',e[0])
       if e[0]:
        seen+=1;assert 24<=e[0x11]<152 and 24<=e[0x13]<232,(region,dungeon,tag,f,'particle bounds')
     assert seen>0,(region,dungeon,tag,'no particles generated')
   assert records['md'][3100]['active']==1 and records['md'][3400]['active']==0
   assert records['sms'][3100]['reward']==records['md'][3100]['reward']==item
   assert records['md'][3400]['progress']==128 and records['md'][3400]['health']==records['md'][3400]['max_health']==min(capacity+8,128) and records['md'][3400]['magic']==24
   assert records['sms'][3100]['window_map']==records['md'][3100]['window_map'],(region,dungeon,'window map')
   assert patterns['sms'][3100]['icon'][0]==patterns['md'][3100]['icon'][0],(region,dungeon,'gem icon')
   for tag in ['sms','md']:
    assert patterns[tag][3100]['icon'][1:]==patterns[tag][2810]['icon'][1:],(region,dungeon,tag,'unused icon tail changed')
   for k in ['font','hero']:assert patterns['sms'][3100][k]==patterns['md'][3100][k],(region,dungeon,k)
   cases.append(dict(region=region,dungeon=dungeon,initial_capacity=capacity,item=item,physical_hero_contact_without_contact_flag_injection=walk,real_dungeon_room_after_normal_entry=dungeon_scene,lethal_boss_damage_to_death_to_gem_chain_verified=boss,boss_primary_record_frames_compared=191 if boss else 0,transient_particles_allowed=particles,appearance_and_settled_fields_exact=True,stable_reward_map_and_used_icon_font_hero_tile_pixels_exact=True,unused_icon_tail_preserved=True,records=records))
   print(region,dungeon,'appearance, reward window and final progression/stats exact',flush=True)
 result=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,full_game_ported=False,limits=['Gem or last-HP boss records, dungeon number, health and magic seeded once in an initial exterior room or boss room 115 after normal dungeon entry; collection uses physical hero contact in walk cases, otherwise an injected contact flag after appearance. Complete original/native game loops and acquisition windows execute. Boss cases normally occupy the eight transient particle slots during death to isolate deterministic timing, then clear them after gem appearance. Particle-enabled cases leave the pool untouched and verify generation/type/bounds separately; source/native random sequences and particle arrays are not asserted equal.','Stable reward map and 35 used tiles compared; unused 96 icon bytes are preserved and can already differ before the window. full framebuffer/SAT, exact modal/loading/refill timing, natural boss defeat and collection, dungeon-room-specific redraws, SRAM persistence and audio waveform remain outside this check.'])
 (ROOT/f'validation/gem{"_boss_particles_dungeon" if boss and particles and dungeon_scene else "_boss_particles" if boss and particles else "_boss_dungeon" if boss and dungeon_scene else "_boss" if boss else "_edges" if edges else "_walk" if walk else "_dungeon" if dungeon_scene else "_gameplay"}_report.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
