"""Actual CE/02 and22/07 conditional NPC frontends and once-only reward."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  matrix=[('story%d-%d'%(n,story),0xce,2,c,20,story,0,0) for n,c in enumerate([0x25c,0x2e0,0x344]) for story in [0,128]]
  matrix += [(name,0x22,7,0x2d4,gold,0,prerequisite,reward) for name,gold,prerequisite,reward in [('not-ready',20,0,0),('gift',20,128,0),('saturated',250,128,0),('wrapped',255,128,0),('already-paid',20,128,1),('nonzero-prerequisite',20,1,0)]]
  for name,town,house,coordinate,initial_gold,story,prerequisite,reward in matrix:
   door=next(d for d in doors if d['room']==town and d['target']==house);x=((coordinate-126)&63)*4+16;y=(((coordinate-126)>>6)*8)+16
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   traces={};patterns={};source_clock=[];births={};gold_changes={};huds={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0xd7,bytes([story])),(3100,0xd2,bytes([prerequisite])),(3100,0xf7,bytes([reward])),(3100,0xdd,bytes([initial_gold])),(3100,0x100+town,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['game_save_state']+0x27,bytes([story])),(3100,sy['game_save_state']+0x22,bytes([prerequisite])),(3100,sy['game_save_state']+0x47,bytes([reward])),(3100,sy['game_save_state']+0x50+town,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_gold',initial_gold),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    rows={};tiles={};arrival=[None];changes=[];last_gold=[initial_gold];hud=[None]
    def observe(f,r):
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[0xdd],r[0xf7],r[0xd2],r[0xd7]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=False
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_gold')]+[data('game_save_state',0x250)[n] for n in [0x47,0x22,0x27]];current_room=w('room_id');active=w('house_dialogue_active')
     if fields[0]!=last_gold[0]:changes.append((f,fields[0]));last_gold[0]=fields[0]
     if tag=='md' and f==4800:hud[0]=data('sms_vram',0x4000)[0x3dd0:0x3dd6]
     if active and arrival[0] is None:arrival[0]=f
     if f in [4500,4800,5400]:
      rows[f]=dict(fields=fields,room=current_room)
     if f==3500:tiles[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else data('scratch',1040)
    def vram(f,v):
     if tag=='sms' and f==4800:hud[0]=bytes(v[0x3dd0:0x3dd6])
    presses=([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(3125,3145,4),(3410,3410,4),(3600,3604,8),(4600,4604,8)]
    if house==7:presses.extend([(5000,5000,4),(5200,5204,8),(5300,5304,8)])
    with contextlib.redirect_stdout(io.StringIO()):run(rom,5400,ROOT/f'validation/conditional-house-{name}-{region}-{tag}',{3500,4500,4800,5400},presses,ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    assert tag=='sms' or arrival[0] is not None,(region,hex(town),tag,'gold interaction not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];gold_changes[tag]=changes;huds[tag]=hud[0]
   assert huds['sms']==huds['md'],('restored gold HUD',huds)
   for tag,changes in gold_changes.items():assert all(changes[n][0]-changes[n-1][0]==2 for n in range(1,len(changes))),(tag,changes)
   assert [g for f,g in gold_changes['sms']]==[g for f,g in gold_changes['md']]
   assert traces['sms']==traces['md'],(region,hex(town),'gift fields/restore',traces)
   assert patterns['sms']==patterns['md'],(region,hex(town),'dialogue bitmap','retained differing patterns')
   assert all(r['room']==house for r in traces['md'].values())
   a=(ROOT/f'validation/conditional-house-{name}-{region}-sms/ram_04800.bin').read_bytes();b=(ROOT/f'validation/conditional-house-{name}-{region}-md/ram_04800.bin').read_bytes();restored=bytes(b[(sy['sms_vram']+0x3800+n)^1] for n in range(1280))
   animated=set()
   for n in range(160):
    if 0x24<=a[0x1c00+n]<0x30:
     for dy in range(2):
      for dx in range(2):animated.add(((n//16)*2+dy)*32+(n%16)*2+dx)
   map_differences=[n for n in range(640) if restored[n*2:n*2+2]!=a[0x1600+n*2:0x1602+n*2]]
   assert set(map_differences)<=animated,(region,'conditional house static restored room map',map_differences,animated)
   assert traces['md'][4800]==traces['md'][5400], 'repeat visit changed reward'
   cases.append(dict(region=region,scenario=name,town=town,house=house,coordinate=coordinate,story=story,prerequisite=prerequisite,initial_reward_flag=reward,initial_gold=initial_gold,native_dialogue_active_first_observed_frame=births['md'],gold_change_frames=gold_changes,observed_gold_unit_count=len(gold_changes['md']),unit_cadence_two_frames_exact=True,restored_gold_HUD_exact=True,final_gold=traces['md'][5400]['fields'][0],dialogue_bitmap_bytes_exact=1040,restored_static_map_words_exact=640-len(animated),animated_map_difference_indices=map_differences,repeat_interaction_no_second_reward=house==7));print(region,name,'conditional dialogue/reward/restoration exact',flush=True)
 limits=['Original source ROM unpatched. Controlled actual CE/02 and22/07 doors, hero setup and initial clock alignment. Six before/after-story dialogues and six reward/prerequisite/repeat/saturation cases in PAL/NTSC.', 'Stable3500 bitmap, later gold/reward/prerequisite/story fields, gold-change values and two-frame unit cadence, restored HUD and static room map compare. Animated NPC words excluded with raw difference indices retained. Absolute text/entry/exit timing, full natural progression and hardware/audio/video fidelity unproved.']
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/'validation/conditional_house_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
