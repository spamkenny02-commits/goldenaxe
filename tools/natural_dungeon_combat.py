"""Controller-only combat, rewards and dungeon traversal from a recorded new game."""
import argparse,collections,contextlib,io,json
from run_core import ROOT,run
from verify_natural_dungeon_route import CASES
from movement_reference import Hero,collision_cache,choose_collision_direction
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def walk(tilemap,start,goal,enemies=()):
    queue=collections.deque([start]);parent={start:None};finish=None
    while queue:
        p=queue.popleft()
        if goal(p):finish=p;break
        cache=collision_cache(tilemap,Hero(x=p[0]<<8,y=p[1]<<8))
        for d,(dx,dy) in enumerate([(0,-8),(0,8),(-8,0),(8,0)]):
            nxt=p[0]+dx,p[1]+dy
            if nxt in parent or not(8<=nxt[0]<=248 and 8<=nxt[1]<=168):continue
            if any(abs(nxt[0]-e['x'])<12 and abs(nxt[1]-e['y'])<12 for e in enemies):continue
            if choose_collision_direction(d,cache)!=d:continue
            parent[nxt]=(p,d);queue.append(nxt)
    if finish is None:return None
    path=[]
    while parent[finish] is not None:previous,d=parent[finish];path.append(d);finish=previous
    return list(reversed(path))

def attack_position(p,e,reach=24,align=8):
    dx=e['x']-p[0];dy=e['y']-p[1]
    return abs(dx)<=align and reach-12<=abs(dy)<=reach or abs(dy)<=align and reach-12<=abs(dx)<=reach

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sms',action='store_true');parser.add_argument('--pal',action='store_true');parser.add_argument('--trial',required=True);parser.add_argument('--frames',type=int,default=14000);parser.add_argument('--target-room',type=lambda x:int(x,0),default=0x1d4);parser.add_argument('--reach',type=int,default=24);parser.add_argument('--align',type=int,default=8);parser.add_argument('--rooms',help='Comma-separated adjacent room IDs');parser.add_argument('--collect-key',action='store_true');parser.add_argument('--collect-item',type=int);parser.add_argument('--collect-gem',action='store_true');parser.add_argument('--exit-dungeon',action='store_true');parser.add_argument('--prefix',help='Recorded natural route directory for this ROM');parser.add_argument('--continuation',help='Replay a completed combat trial from boot before extending its route');args=parser.parse_args()
    assert args.collect_item is None or 0<=args.collect_item<17
    itinerary=[int(x,0) for x in args.rooms.split(',')] if args.rooms else list(range(0x1e4,args.target_room-1,-16))
    # Entry is checked against actual replay RAM at prefix_end; support later dungeons.
    assert itinerary and 256<=itinerary[0]<512
    assert (itinerary[-1]==0x1e4 if args.exit_dungeon else itinerary[-1]==args.target_room)
    assert all(abs(a-b) in [1,16] for a,b in zip(itinerary,itinerary[1:]))
    itinerary_index=0
    puzzle_reference=json.loads((ROOT/'analysis/room_puzzles_reference.json').read_bytes())
    assert puzzle_reference['source_sha256']==sha((ROOT/'input/original.sms').read_bytes())
    puzzles={r['room']:r for r in puzzle_reference['records']}
    region='pal' if args.pal else 'auto';prefix_name=args.continuation or args.prefix or next(a if args.sms else b for r,a,b in CASES if r==region);prefix=ROOT/('validation/natural-dungeon-combat' if args.continuation else 'validation/natural-dungeon-route')/prefix_name
    capture=json.loads((prefix/'capture.json').read_bytes());recorded=json.loads((prefix/'controls.json').read_bytes());prefix_end=capture['frames'];presses=list(map(tuple,capture['presses']))
    prefix_inputs=[()]*(prefix_end+1)
    for n,item in enumerate(recorded):
        end=recorded[n+1]['frame']-1 if n+1<len(recorded) else prefix_end
        if args.continuation:
            prefix_inputs[item['frame']:min(end,prefix_end)+1]=[tuple(item['buttons'])]*(min(end,prefix_end)-item['frame']+1)
        else:presses.extend((item['frame'],min(end,prefix_end),b) for b in item['buttons'] if item['frame']<=prefix_end)
    rom=ROOT/'input/original.sms' if args.sms else ROOT/'gaw-megadrive.bin';sy=None if args.sms else symbols(ROOT/'megadrive/out/release/symbol.txt')
    assert capture['rom_sha256']==sha(rom.read_bytes()) and not capture['test_ram_writes'] and capture['sram_input'] is None
    tag='sms' if args.sms else 'md';folder=ROOT/f'validation/natural-dungeon-combat/{tag}-{region}-{args.trial}';assert not folder.exists(),folder
    state={};actors=[];loot=[];tilemap=b'';events=[];samples=[];controls=[];captures=set();observed=0;cached=-1;buttons=[];last_direction=0;seen_room=False;seen_enemies=False;cleared=None;failure=None;menu_since=None;deaths=0;last_key=None
    if args.continuation:controls=list(recorded)
    gem_picked_at=None
    exit_reset_seen=False
    boss_frames=[];item_picked_at=None;pilot_progress_key=None;pilot_progress_frame=0
    item_reference=json.loads((ROOT/'analysis/item_rewards_reference.json').read_bytes())
    assert item_reference['source_sha256']==sha((ROOT/'input/original.sms').read_bytes())
    rewards={r['room']:r for r in item_reference['records']}
    def observe(f,r):
        nonlocal actors,loot,tilemap,observed,seen_room,seen_enemies,cleared,failure,menu_since,deaths,last_key,itinerary_index,gem_picked_at,exit_reset_seen,item_picked_at,pilot_progress_key,pilot_progress_frame
        observed=f
        if args.sms:
            data=lambda a,n:bytes(r[a:a+n]);state.update(room=int.from_bytes(r[0xb9:0xbb],'little'),game=r[0x1d],hero=r[0x301],counter=r[0x304],x=int.from_bytes(r[0x312:0x314],'little')>>8,y=int.from_bytes(r[0x310:0x312],'little')>>8,health=r[0x318],keys=r[0xde],audio_error=0)
            raw=data(0x600,768);loot_raw=data(0x4b0,336);tilemap=data(0x1600,1536)
            state['room_flags']=r[0x100+(state['room']&255)]
            state.update(dungeon=r[0x37],progress=r[0xce+r[0x37]],first_gem=r[0xcf],max_health=r[0xda],magic=r[0xdb],max_magic=r[0xdc],reward_active=0)
            state.update(weapon=r[0xe1],selected=r[0xdf],item_value=r[0xe0+args.collect_item] if args.collect_item is not None else 0)
        else:
            data=lambda a,n:bytes(r[(a+i)^1] for i in range(n));word=lambda n:int.from_bytes(data(sy[n],2),'big')
            state.update(room=word('room_id'),game=word('game_state'),hero=word('hero_state'),counter=word('hero_counter'),x=word('hero_x')>>8,y=word('hero_y')>>8,health=word('hero_health'),keys=word('hero_keys'),audio_error=word('sound_unhandled_command'))
            raw=data(sy['world_actor_state'],768);loot_raw=data(sy['world_loot_state'],336);tilemap=data(sy['sms_vram']+0x3800,1536)
            state['room_flags']=data(sy['game_save_state']+0x50+(state['room']&255),1)[0]
            dungeon=word('world_dungeon_number');state.update(dungeon=dungeon,progress=data(sy['game_save_state']+0x1e+dungeon,1)[0],max_health=word('hero_max_health'),magic=word('hero_magic'),max_magic=word('hero_max_magic'),reward_active=word('item_reward_active'),resume_phase=word('resume_phase'),door_loading=data(sy['door_transition_loading'],1)[0])
            state['first_gem']=data(sy['game_save_state']+0x1f,1)[0]
            state.update(weapon=word('hero_weapon_level'),selected=word('hero_selected_item'),item_value=data(sy['hero_items']+args.collect_item,1)[0] if args.collect_item is not None else 0)
        actors=[dict(slot=n,type=raw[n*48],flags=raw[n*48+3],hp=raw[n*48+0x18],hurt=raw[n*48+5],x=raw[n*48+0x13],y=raw[n*48+0x11]) for n in range(16) if raw[n*48]]
        loot=[dict(slot=n,type=loot_raw[n*48],x=loot_raw[n*48+0x13],y=loot_raw[n*48+0x11]) for n in range(7) if loot_raw[n*48]]
        if f==prefix_end and not(state['room']==itinerary[0] and state['game']==12 and state['health']):failure='recorded_prefix_did_not_reach_expected_room'
        if f<=prefix_end:return
        if args.collect_item is not None and state['item_value'] and item_picked_at is None:item_picked_at=f;captures.update([f+1,f+150])
        if actors and actors[0]['slot']==0 and actors[0]['type']==7:
            boss_frames.append(dict(frame=f,state=raw[1],timer=raw[0x28],counter=raw[4]))
        if state['progress']==128 and gem_picked_at is None:gem_picked_at=f;captures.update([f+1,f+150])
        if itinerary_index+1<len(itinerary) and state['room']==itinerary[itinerary_index+1]:itinerary_index+=1
        if state['game']==6:itinerary_index=0
        if state['game']==12 and state['room']!=itinerary[itinerary_index] and state['room'] in itinerary:
            candidates=[n for n,room in enumerate(itinerary) if room==state['room']]
            previous_index=itinerary_index;itinerary_index=min(candidates,key=lambda n:abs(n-previous_index))
            events.append(dict(frame=f,reason='recover_after_room_displacement',previous_itinerary_index=previous_index,itinerary_index=itinerary_index,**state))
        if state['room']==args.target_room:
            seen_room=True
            if state['hero']==0:exit_reset_seen=True
            if any(e['type']>=0x20 for e in actors):seen_enemies=True
            gem_done=not args.collect_gem or state['progress']==128 and state['max_health']>=32 and state['health']==state['max_health'] and state['magic']==state['max_magic'] and not state['reward_active']
            item_done=args.collect_item is None or item_picked_at is not None and f-item_picked_at>=300 and state['item_value'] and not state['reward_active']
            if seen_enemies and state['health'] and state['game']==12 and not any(e['slot']<8 for e in actors) and (not args.collect_key or state['keys']>0) and gem_done and item_done and cleared is None:cleared=f;captures.add(f+1)
            if args.exit_dungeon and exit_reset_seen and state['first_gem']==128 and state['max_health']==32 and state['health'] and state['game']==12 and state['hero']==1 and not state.get('resume_phase',0) and not state.get('door_loading',0) and cleared is None:cleared=f;captures.add(f+1)
        if state['game']==20:
            if menu_since is None:menu_since=f;deaths+=1
        else:menu_since=None
        if deaths>3:failure='death_retry_limit'
        if args.continuation and deaths:failure='continuation_route_died'
        if state['audio_error']:failure='native_audio_error'
        key=state['room'],state['game'],state['health'],state['keys'],state['room_flags'],state['progress'],state['max_health'],state['reward_active'],state['item_value'],state['selected'],tuple((e['slot'],e['type'],e['hp']) for e in actors if e['slot']<8),tuple((e['slot'],e['type']) for e in loot)
        row=dict(frame=f,**state,actors=actors,loot=loot,itinerary_index=itinerary_index)
        if key!=last_key:events.append(row);last_key=key;captures.add(f+1)
        progress=(key,state['x'],state['y'],tuple((e['slot'],e['type'],e['hp'],e['x'],e['y']) for e in actors if e['slot']<8))
        if progress!=pilot_progress_key:pilot_progress_key=progress;pilot_progress_frame=f
        elif f-pilot_progress_frame>2400:failure='controller_stalled'
        if f%10==0:samples.append(row)
        if cleared is not None and f==cleared+149:captures.add(f+1)
    def choose(f):
        nonlocal cached,buttons,last_direction
        if f==cached:return buttons
        cached=f;buttons=[]
        if f<=prefix_end:buttons=list(prefix_inputs[f]);return buttons
        if failure or cleared is not None:return buttons
        if args.collect_item is not None and item_picked_at is not None and f-item_picked_at<300:
            if f-item_picked_at>=200 and f%30==0:buttons=[8]
            return buttons
        if args.collect_gem and gem_picked_at is not None:
            if f-gem_picked_at>=200 and f%30==0:buttons=[8]
            return buttons
        if state.get('game')==20:
            if menu_since is not None and f-menu_since>=180 and f%30==0:buttons=[8]
            return buttons
        if state.get('game')!=12 or not state.get('health'):return buttons
        if state['hero'] not in [0,1,2,3,4,5]:return buttons
        p=state['x'],state['y']
        if state['room'] not in itinerary:return buttons
        enemies=[e for e in actors if e['type']>=0x20 and e['hp'] and e['flags']&2]
        hazards=[e for e in actors if e['type']>=0x20 and not e['hp'] and e['flags']&2]
        near=sorted(enemies,key=lambda e:abs(e['x']-p[0])+abs(e['y']-p[1]))
        if state['hero'] in [2,3,4,5] or near and (attack_position(p,near[0],args.reach,args.align) or abs(near[0]['x']-p[0])+abs(near[0]['y']-p[1])<16):
            if near:
                dx=near[0]['x']-p[0];dy=near[0]['y']-p[1];last_direction=(3 if dx>=0 else 2) if abs(dx)>abs(dy) else (1 if dy>=0 else 0)
            buttons=[4+last_direction,8] if f%3 else []
            return buttons
        if state['counter']:buttons=[4+last_direction];return buttons
        keys=[e for e in loot if e['type']==14]
        gems=[e for e in actors if e['type']==15]
        if enemies:goal=lambda q:any(attack_position(q,e,args.reach,args.align) for e in enemies)
        elif keys:goal=lambda q:any(abs(q[0]-e['x'])<8 and abs(q[1]-e['y'])<8 for e in keys)
        elif gems:goal=lambda q:any(abs(q[0]-e['x'])<=8 and abs(q[1]-e['y'])<=16 for e in gems)
        elif any(e['slot']<8 and (e['type']<0x20 or e['hp']) for e in actors):return buttons # Wait for enemies/particles, not invulnerable hazards.
        elif args.collect_item is not None and state['room'] in rewards and not state['item_value']:
            coordinate=rewards[state['room']]['coordinate']
            point=next((x,y) for y in range(8,169,8) for x in range(8,249,8) if (((y-12)&248)<<3)+(((x-12)&255)>>2&62)+126==coordinate)
            if p==point:buttons=[4];return buttons
            goal=lambda q:q==point
        elif state['room'] in puzzles and not state['room_flags']&4:
            coordinate=puzzles[state['room']]['coordinate']
            point=next((x,y) for y in range(8,169,8) for x in range(8,249,8) if (((y-12)&248)<<3)+(((x-12)&255)>>2&62)+126==coordinate)
            if p==point:buttons=[4];return buttons
            goal=lambda q:q==point
        elif itinerary_index+1<len(itinerary):
            delta=itinerary[itinerary_index+1]-state['room'];direction={-16:0,16:1,-1:2,1:3}[delta]
            goal=lambda q:q==[(128,8),(128,168),(8,88),(248,88)][direction]
        else:goal=lambda q:q==((128,168) if args.exit_dungeon else (128,96))
        route=walk(tilemap,p,goal,enemies+hazards)
        if route is None and not enemies and itinerary_index+1<len(itinerary) and state['keys']:
            delta=itinerary[itinerary_index+1]-state['room'];direction={-16:0,16:1,-1:2,1:3}[delta]
            probe=[(128,40),(128,144),(32,88),(224,88)][direction]
            if p==probe:buttons=[4+direction];return buttons
            route=walk(tilemap,p,lambda q:q==probe)
        if route:last_direction=route[0];buttons=[4+last_direction]
        return buttons
    def controller(f):
        nonlocal failure
        try:value=choose(f)
        except Exception as error:failure='controller_exception:'+repr(error);value=[]
        if f>prefix_end and (not controls or controls[-1]['buttons']!=value):controls.append(dict(frame=f,buttons=list(value)))
        return value
    def stop():return bool(failure) or cleared is not None and observed-cleared>=150
    with contextlib.redirect_stdout(io.StringIO()):run(rom,args.frames,folder,captures,presses,ram_observer=observe,input_provider=controller,stop_when=stop,core_options={'genesis_plus_gx_region_detect':region})
    for name,data in [('events',events),('samples',samples),('controls',controls),('boss_frames',boss_frames)]: (folder/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    if cleared is None and failure is None:failure='frame_limit'
    result=dict(rom_sha256=sha(rom.read_bytes()),region=region,recorded_new_game_prefix=prefix_name,prefix_end=prefix_end,itinerary=itinerary,attack_reach=args.reach,attack_alignment=args.align,collect_key_requested=args.collect_key,collect_gem_requested=args.collect_gem,collect_item_requested=args.collect_item,exit_dungeon_requested=args.exit_dungeon,target_room=args.target_room,entered_room=seen_room,seen_target_enemies=seen_enemies,room_cleared=cleared is not None,clear_frame=cleared,deaths=deaths,failure=failure,last_state=state,last_actors=actors,ram_injections=False,rom_modifications=False,sram_checkpoint_injection=False,full_dungeon_cleared=bool(args.exit_dungeon and cleared is not None))
    (folder/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
