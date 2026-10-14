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
 revisit='--revisit' in sys.argv
 cold='--cold' in sys.argv
 persistence='--persistence' in sys.argv or revisit or cold
 saved_high='--saved-high' in sys.argv
 persistence_suffix='-cold-persistence' if cold else '-revisit' if revisit else '-persistence-high' if saved_high else '-persistence'
 for region in ['auto','pal']:
  hint='--hint' in sys.argv
  matrix=[(0x50,0,1,1,24,0)] if hint else [(0x27,22,1,1,24,0),(0xb1,23,1,2,24,0),(0x50,2,1,1,56,0),(0x6a,3,2,1,24,0),(0x92,12,1,1,24,0),(0x4c,26,1,1,24,128)]
  if persistence and not revisit and not cold:matrix += [(0xc7,12,1,1,24,0),(0x55,6,1,1,24,0)]
  if '--repeat-only' in sys.argv:matrix=[r for r in matrix if r[0]==0x6a]
  selected=next((int(v.split('=',1)[1],16) for v in sys.argv if v.startswith('--town=')),None)
  if selected is not None:matrix=[r for r in matrix if r[0]==selected]
  if '--first-only' in sys.argv:matrix=matrix[:1]
  for town,item,basic,armor,capacity,defeat in matrix:
   candidates=[d for d in doors if d['room']==town and d['target'] in [9,15,79]]
   context_fixture=not candidates;door=next(d for d in doors if d['room']==0x4c and d['target']==9) if context_fixture else candidates[0]
   door_town=door['room'];house=door['target'];x,y=(168,56) if house==9 else (104,56) if house==15 else ((136,72) if hint else (120,72))
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][door_town*2:door_town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   traces={};patterns={};source_clock=[];births={};cell_samples={};reward_counts={};map_samples={};walk_results={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0xe4,b'\x01'),(3100,0xe0,bytes([basic])),(3100,0xf1,bytes([armor])),(3100,0xbf,b'\x01'),(3100,0xda,bytes([capacity])),(3100,0xd4,bytes([defeat])),(3100,0xe8,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['hero_items']+4,b'\x01'),(3100,sy['hero_items'],bytes([basic])),(3100,sy['game_save_state']+15,b'\x01'),(3100,sy['game_save_state']+0x24,bytes([defeat])),(3100,sy['hero_items']+8,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_basic_level',basic),(3100,'hero_armor_level',armor),(3100,'hero_max_health',capacity),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    if persistence:writes.append((3100,0x100+town if tag=='sms' else sy['game_save_state']+0x50+town,bytes([1 if revisit else 128 if saved_high else 0])))
    # Town27's gift entrance is on water;revisit fixtures include the original
    # traversal item before entering,not a collision/terrain bypass during play.
    if revisit:writes.append((3100,0xec if tag=='sms' else sy['hero_items']+12,b'\1'))
    if context_fixture:
     if tag=='sms':
      writes=[(f,a,door_town.to_bytes(2,'little') if f==3120 and a==0xb9 else v) for f,a,v in writes]
      writes.append((3390,0xbb,town.to_bytes(2,'little')))
     else:
      writes=[(f,a,door_town.to_bytes(2,'big') if f==3120 and a==sy['room_id'] else v) for f,a,v in writes]
      add(3390,'house_return_room',town)
    if cold:writes=[entry for entry in writes if entry[0]!=3100]
    rows={};tiles={};arrival=[None];samples={};room_maps={};requests=[0];previous_active=[False]
    live_buttons=[set()];walk=dict(stage='corridor',outside_frame=None,reentered_frame=None,finished_frame=None,outside_zero_seen=False,inside_zero_seen=False);probe_start=[None]
    def observe(f,r):
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[a] for a in [0xe0,0xe4,0xf1,0xf2,0xbf,0xe8,0xe2,0xda]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=(r[0xa3]==item and fields[0 if item in [2,3] else 2 if item in [22,23] else 5 if item==12 else 3]==(2 if item in [2,22] else 3 if item in [3,23,26] else 1)) if not hint else f>=3430 and current_room==house
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_basic_level'),data('hero_items',17)[4],w('hero_armor_level'),w('hero_shield_level'),data('game_save_state',16)[15],data('hero_items',17)[8],data('hero_items',17)[2],w('hero_max_health')];current_room=w('room_id');active=(w('item_reward_active') and w('item_reward_number')==item) if not hint else w('house_dialogue_active') and w('house_dialogue_index')==0x8ed9
     if persistence:
      fields.append(r[0x100+town] if tag=='sms' else data('game_save_state',0x250)[0x50+town])
      if tag=='sms':active=int.from_bytes(r[0x308:0x30a],'little')==0x8495
      if active and not previous_active[0]:requests[0]+=1
      previous_active[0]=bool(active)
     if revisit and f>=5000:
      px=r[0x313] if tag=='sms' else w('hero_x')>>8
      py=r[0x311] if tag=='sms' else w('hero_y')>>8
      state=r[0x301] if tag=='sms' else w('hero_state')
      live_buttons[0]=set();stage=walk['stage']
      if current_room==door_town and walk['outside_frame'] is None:
       walk['outside_frame']=f;walk['stage']='outside_wait'
      if current_room==house and walk['outside_frame'] is not None and walk['reentered_frame'] is None:
       walk['reentered_frame']=f;walk['stage']='inside_wait'
      stage=walk['stage']
      if stage=='corridor':
       if py<88:live_buttons[0]={5}
       else:walk['stage']='exit_align'
      elif stage=='exit_align':
       if px<136:live_buttons[0]={7}
       elif px>136:live_buttons[0]={6}
       else:walk['stage']='exit_walk'
      elif stage=='exit_walk':live_buttons[0]={5}
      elif stage=='outside_wait':
       walk['outside_zero_seen'] |= state==0
       if walk['outside_zero_seen'] and state==1:
        walk['stage']='outside_step';walk['outside_origin']=[px,py];walk['outside_trial']=0;walk['outside_trial_start']=f
      elif stage=='outside_step':
       directions=[5,7,6,4];direction=directions[walk['outside_trial']%4]
       distance=abs(px-walk['outside_origin'][0])+abs(py-walk['outside_origin'][1])
       if distance>=16:
        walk['return_direction']={4:5,5:4,6:7,7:6}[direction];walk['stage']='door_return'
       elif f-walk['outside_trial_start']>=40 and distance==0:
        walk['outside_trial']+=1;walk['outside_trial_start']=f
       else:live_buttons[0]={direction}
      elif stage=='outside_align':
       if px<door['x']:live_buttons[0]={7}
       elif px>door['x']:live_buttons[0]={6}
       else:walk['stage']='door_return'
      elif stage=='door_return':live_buttons[0]={walk.get('return_direction',4)}
      elif stage=='inside_wait':
       walk['inside_zero_seen'] |= state==0
       if walk['inside_zero_seen'] and state==1:walk['stage']='approach_corridor'
      elif stage=='approach_corridor':
       if py>88:live_buttons[0]={4}
       else:walk['stage']='approach_align'
      elif stage=='approach_align':
       if px<x:live_buttons[0]={7}
       elif px>x:live_buttons[0]={6}
       else:walk['stage']='approach_gift'
      elif stage=='approach_gift':
       if py>y:live_buttons[0]={4}
       else:walk['stage']='probe';probe_start[0]=f
      elif stage=='probe':
       if f-probe_start[0]<20:live_buttons[0]={4}
       else:walk['stage']='finished';walk['finished_frame']=f
      walk['last_position']=[px,py];walk['last_room']=current_room
     if active and arrival[0] is None:arrival[0]=f
     if f in ([3850,3960,4000] if hint else [3500,3800,3900]+([4250,4800] if persistence else [])+([6500] if revisit else [])):
      rows[f]=dict(fields=fields,room=current_room)
      if persistence:samples[f]=bytes(r[0x1c00:0x1ca0]) if tag=='sms' else data('scratch',0x8a0)[0x800:0x8a0]
      if persistence and f in [4250,4800,6500]:room_maps[f]=bytes(r[0x1600:0x1b00]) if tag=='sms' else data('sms_vram',0x4000)[0x3800:0x3d00]
      if hint and f==3850:tiles[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else data('scratch',1040)
    def vram(f,v):
     if hint or cold or f!=3500:return
     indices=list(range(208,236))+list(range(444,448))+list(range(496,502));tiles[f]=[sms_pixels(v,n) if tag=='sms' else md_pixels(v,n+16) for n in indices]
    extra=[(4000,4004,0),(4070,4074,0),(4300,4320,4),(4700,4704,8)] if persistence else []
    boot=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)] if cold else PRESSES[:8]
    saved=ROOT/f'validation/quest-gift-save-{town:02x}-{region}-{tag}.srm' if cold else None
    with contextlib.redirect_stdout(io.StringIO()):run(rom,6800 if revisit else 5000 if persistence else 4000,ROOT/f'validation/house-quest{persistence_suffix if persistence else "-hint" if hint else ""}-{town:02x}-{region}-{tag}',({3500,3850,3960,4000} if hint else {3500,3800,3900,4250,4800,6500} if revisit else {3500,3800,3900,4250,4800} if persistence else {3500,3800,3900}),([(200,220,0)] if tag=='sms' else [])+boot+[(3125,3145,4),(3410,3410 if hint else 3430,4)]+([(3600,3604,8),(3900,3904,8)] if hint else [(3700,3704,8)])+extra,ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region},input_provider=(lambda f:live_buttons[0]) if revisit else None,sram_in=saved)
    if revisit:assert walk['finished_frame'] is not None and walk['finished_frame']<6500,(region,town,tag,'walk incomplete',walk)
    assert (arrival[0] is None if cold else arrival[0] is not None),(region,hex(town),tag,'unexpected gift request',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];cell_samples[tag]=samples;reward_counts[tag]=requests[0];map_samples[tag]=room_maps;walk_results[tag]=walk if revisit else None
   cell_differences={};persistent_map_differences={}
   if persistence:
    (ROOT/f'validation/house-quest{persistence_suffix}-last-diagnostic.json').write_text(json.dumps(dict(region=region,town=town,traces=traces,cells={k:{f:v.hex() for f,v in a.items()} for k,a in cell_samples.items()},reward_counts=reward_counts),indent=2)+'\n')
    assert reward_counts=={'sms':0 if cold else 1,'md':0 if cold else 1},('gift repeated',region,town,reward_counts)
    assert all(r['fields'][-1]&2 for r in traces['md'].values()),('visit flag not marked',region,town,traces)
    for f,a in cell_samples['sms'].items():
     b=cell_samples['md'][f];diff=[n for n in range(160) if a[n]!=b[n]]
     assert all(0x24<=a[n]<0x30 and a[n]^b[n]==1 for n in diff),('static transformed room cells',region,town,f,diff)
     cell_differences[f]=diff
    for f,a in map_samples['sms'].items():
     b=map_samples['md'][f];animated=set()
     for n,value in enumerate(cell_samples['sms'][f]):
      if 0x24<=value<0x30:
       for dy in range(2):
        for dx in range(2):animated.add(((n//16)*2+dy)*32+(n%16)*2+dx)
     diff=[n for n in range(640) if a[n*2:n*2+2]!=b[n*2:n*2+2]]
     assert set(diff)<=animated,('static transformed room map',region,town,f,diff)
     persistent_map_differences[f]=diff
   assert traces['sms']==traces['md'],(region,hex(town),'gift fields/restore',traces)
   assert patterns['sms']==patterns['md'],(region,hex(town),'reward icon/font/hero pixels','retained differing patterns')
   assert all(r['room']==house for r in traces['md'].values())
   if item in [22,23]:assert traces['md'][3900]['fields'][4]==0 and traces['md'][3900]['fields'][0]==basic
   if item in [2,3]:assert traces['md'][3900]['fields'][2]==armor
   if hint:
    a=(ROOT/f'validation/house-quest-hint-{town:02x}-{region}-sms/ram_04000.bin').read_bytes();b=(ROOT/f'validation/house-quest-hint-{town:02x}-{region}-md/ram_04000.bin').read_bytes();restored=bytes(b[(sy['sms_vram']+0x3800+n)^1] for n in range(1280))
    animated=set()
    for n in range(160):
     if 0x24<=a[0x1c00+n]<0x30:
      for dy in range(2):
       for dx in range(2):animated.add(((n//16)*2+dy)*32+(n%16)*2+dx)
    map_differences=[n for n in range(640) if restored[n*2:n*2+2]!=a[0x1600+n*2:0x1602+n*2]]
    assert set(map_differences)<=animated,(region,'long hint static restored room map',map_differences,animated)
   cases.append(dict(region=region,town=town,house=house,item=item,request_frames=births,equipment_inventory_curse_capacity_and_room_samples_exact=6 if revisit else 5 if persistence else 3,reward_pattern_tiles_exact=0 if hint or cold else 38,long_dialogue_bitmap_bytes_exact=1040 if hint else 0,restored_static_map_words_exact=640-len(animated) if hint else None,animated_map_difference_indices=map_differences if hint else [],normal_door_UP_and_C_return=True,door_town=door_town,outside_context_replaced_after_door=context_fixture,initial_clock_aligned=True,persistent_flag_and_static_cells_exact=persistence,persistence_animated_cell_differences=cell_differences,persistence_animated_map_differences=persistent_map_differences,reward_count=reward_counts if persistence else None,inventory_roundtrip_and_second_UP=persistence,controller_walk_exit_reentry=walk_results if revisit else None,cold_saved_state_only=cold));print(region,hex(town),item,'quest gift state/room persistence exact',flush=True)
 if hint:
  limits=['Controlled actual town50 door/house resources, magic owned and HP capacity24. One-frame UP starts original265-byte refusal text; C pulses3600/3900 acknowledge intermediate/final pages. Hero fixture and initial clock aligned at3400; no direct dialogue/text/state mutation after setup.', 'Stable final1040 bitmap bytes at3850 and restored equipment/room fields at3960/4000 compare in PAL/NTSC. Animated NPC map cells are excluded from static restoration and raw differing word indices retained. Full dialogue publication timing, all intermediate pixels/audio and natural quest progression remain unproved.']
 else:limits=['Six controlled real town-door gifts with initial clock alignment; no direct gift or post-setup VRAM mutation.', 'Three equipment/curse/room field samples and38 font/icon/hero tiles per gift compare. Complete natural quest progression, full frames/audio and hardware timing remain unproved.']
 if persistence:limits += ['Static cells/maps compare with only remaining NPC24..2F XOR1 animation poses and their map words excluded;raw differences retained. Gift cell31 is never excluded. Window/route timings and complete natural progression are not asserted.']
 if persistence and not revisit and not cold:limits += ['Six actual town-door contexts plus two explicit outside-context fixtures per region. C7 oil/55 remedy enter4C->09 then set outside context at3390;natural reachability is unproved. Exactly one held-gift phase;no exterior/SRAM roundtrip in this mode.']
 if revisit:limits += ['Six actual doors;after5000 a read-only RAM observer selects ordinary directional buttons to walk out,step away,re-enter and approach the NPC. No RAM writes after3400. Setup includes already-visited world bit1 and original traversal itemC0EC for the water entrance;these are explicit progression fixtures. SRAM is separate.']
 if cold:limits += ['Actual quest-gift SRAM files are loaded into a fresh core through normal Continue. Subsequent controlled exterior/door/hero relocation uses only3120/3400 writes;all3100 inventory/equipment/flag fixtures removed. No saved gift/visit bit is injected. Two normal UP attempts and menu yield zero reward phases. Journey from saved checkpoint to each town is not asserted.']
 report=dict(long_hint=hint,persistence=persistence,revisit=revisit,cold=cold,initial_outside_flag=None if cold else 1 if revisit else 128 if saved_high else 0,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/f'validation/house_quest{persistence_suffix.replace("-","_") if persistence else "_hint" if hint else ""}_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
