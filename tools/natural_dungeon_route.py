"""Read ROM maps and drive an unmodified game toward dungeon entrance1."""
import argparse,contextlib,io,json,collections
from functools import lru_cache
from run_core import ROOT,run
from extract_world import initial_room
from extract_title import rle_planes
from movement_reference import Hero,collision_cache,choose_collision_direction
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

class World:
    def __init__(self,door_index=1):
        self.rom=(ROOT/'input/original.sms').read_bytes();_,self.meta,_,self.initial_map,self.arrays,_=initial_room(self.rom)
        doors=json.loads((ROOT/'analysis/doors_reference.json').read_bytes());self.doors=doors
        self.goal=next(d for d in doors['direct_unconditional_dungeon_doors'] if d['index']==door_index)
        self.house_mouths={(d['room'],d['x'],d['y']+8) for d in doors['direct_unconditional_doors']}
    @lru_cache(None)
    def tilemap(self,room):
        index=self.arrays['world_room_index'];p=int.from_bytes(index[room*2:room*2+2],'little')
        if p==65535:return None
        cells=bytearray(160);rle_planes(self.arrays['world_room_streams'],p,cells,0,1);out=bytearray(self.initial_map)
        for y in range(20):
            for x in range(32):
                a=cells[(y//2)*16+x//2]*8+(y&1)*4+(x&1)*2;off=(y*32+x)*2;out[off:off+2]=self.meta[a:a+2]
        return bytes(out)
    def edge(self,node,d):
        room,x,y,phase=node
        if d==0 and node[:3] in self.house_mouths:return None
        cache=collision_cache(self.tilemap(room),Hero(x=x<<8,y=y<<8))
        if choose_collision_direction(d,cache)!=d:return None
        x+=[0,0,-8,8][d];y+=[-8,8,0,0][d]
        if x<16:room=(room&240)|((room-1)&15);x=240
        elif x>=241:room=(room&240)|((room+1)&15);x=16
        elif y<16:room=(room-16)&255;y=160
        elif y>=161:room=(room+16)&255;y=16
        if room<16 or room&15==15 or self.tilemap(room) is None:return None
        if room!=node[0]:
            if node[0]!=0x77 or room==0x76:phase=0
            else:
                phase+=1
                correct=(phase==1 and room==0x78 and node[2]>=96) or (phase==2 and room==0x67) or (phase==3 and room==0x78 and node[2]<96) or (phase==4 and room==0x87) or (phase==5 and room==0x67)
                if not correct:phase=0
                if not(correct and phase==5):room=0x77
        return room,x,y,phase
    def route(self,start):
        if len(start)==3:start=(*start,0)
        goal=self.goal['room'],self.goal['x'],self.goal['y']+8
        queue=collections.deque([start]);parents={start:None};found=None
        while queue:
            here=queue.popleft()
            if here[:3]==goal:found=here;break
            for d in [0,1,2,3]:
                nxt=self.edge(here,d)
                if nxt is not None and nxt not in parents:parents[nxt]=(here,d);queue.append(nxt)
        if found is None:return None,len(parents)
        path=[]
        while parents[found] is not None:
            previous,d=parents[found];path.append((previous,d,found));found=previous
        return list(reversed(path)),len(parents)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',action='store_true');parser.add_argument('--sms',action='store_true');parser.add_argument('--pal',action='store_true');parser.add_argument('--frames',type=int,default=12000);parser.add_argument('--trial',default='01');parser.add_argument('--door-index',type=int,default=1);parser.add_argument('--retry-deaths',type=int,default=0,help='Use normal Continue after death, at most this many times');parser.add_argument('--prefix-combat',help='Natural completed combat trace, replayed from cold boot');args=parser.parse_args()
    world=World(args.door_index);start=(0x95,136,112);prefix_end=0;prefix_inputs=[];prefix_presses=[]
    if args.prefix_combat:
        prefix=ROOT/'validation/natural-dungeon-combat'/args.prefix_combat
        prior=json.loads((prefix/'report.json').read_bytes());capture=json.loads((prefix/'capture.json').read_bytes());recorded=json.loads((prefix/'controls.json').read_bytes())
        assert prior['failure'] is None and prior['room_cleared'] and not capture['test_ram_writes'] and capture['sram_input'] is None
        assert capture['rom_sha256']==sha((ROOT/('input/original.sms' if args.sms else 'gaw-megadrive.bin')).read_bytes())
        st=prior['last_state'];start=(st['room'],st['x'],st['y']);assert start[0]<256
        prefix_end=capture['frames'];prefix_presses=list(map(tuple,capture['presses']));prefix_inputs=[()]*(prefix_end+1)
        for i,row in enumerate(recorded):
            end=recorded[i+1]['frame']-1 if i+1<len(recorded) else prefix_end
            prefix_inputs[row['frame']:end+1]=[tuple(row['buttons'])]*(end-row['frame']+1)
            prefix_presses.extend((row['frame'],end,b) for b in row['buttons'])
    route_start=max(2500,prefix_end+1)
    path,visited=world.route(start);assert path is not None,('No base-map walking route',visited)
    rooms=list(dict.fromkeys([a[0] for a,d,b in path]+[path[-1][2][0]]))
    result=dict(source_sha256=sha(world.rom),goal=world.goal,waypoints=len(path),visited_nodes=visited,rooms=[f'{r:02x}' for r in rooms],route=path,scope='Static base-ROM walking proposal with original collision/sliding rules. Does not include actors, quest edits, terrain-dependent speed or prove a playable route.')
    folder=ROOT/'validation/natural-dungeon-route';folder.mkdir(exist_ok=True);(folder/f'plan-door{args.door_index}-{args.trial}.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='route'})
    if args.plan:return
    tag='sms' if args.sms else 'md';rom=ROOT/'input/original.sms' if args.sms else ROOT/'gaw-megadrive.bin';sy=None if args.sms else symbols(ROOT/'megadrive/out/release/symbol.txt')
    state={};events=[];samples=[];captures=set();controls=[];cursor=0;cached_frame=-1;cached_buttons=[];last_progress=route_start;reached_at=None;ready_at=None;room_entry_at=None;saw_target_reset=False;probe_before=None;probe_after=None;failure=None
    previous_key=None;observed_frame=0;death_active=False;deaths=0;menu_since=None
    def observe(f,r):
        nonlocal previous_key,reached_at,ready_at,room_entry_at,saw_target_reset,probe_before,probe_after,failure,observed_frame,death_active,deaths,menu_since
        observed_frame=f
        if args.sms:
            state.update(room=int.from_bytes(r[0xb9:0xbb],'little'),game_state=r[0x1d],hero_state=r[0x301],counter=r[0x304],x=int.from_bytes(r[0x312:0x314],'little')>>8,y=int.from_bytes(r[0x310:0x312],'little')>>8,health=r[0x318],gold=r[0xdd],maze=r[0x6c])
        else:
            word=lambda n:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(2)),'big')
            state.update(room=word('room_id'),game_state=word('game_state'),hero_state=word('hero_state'),counter=word('hero_counter'),x=word('hero_x')>>8,y=word('hero_y')>>8,health=word('hero_health'),gold=word('hero_gold'),maze=r[sy['forest_maze_progress']^1],reveal_phase=word('resume_phase'),door_loading=r[sy['door_transition_loading']^1])
        if f<route_start:return
        row=dict(frame=f,waypoint=cursor,**state)
        if f%5==0:samples.append(row)
        key=state['room'],state['game_state'],state['health']
        if key!=previous_key:
            events.append(row);captures.add(f+1);previous_key=key;print(tag,'event',row,flush=True)
        if state['room']==world.goal['target'] and room_entry_at is None:room_entry_at=f;captures.add(f+1)
        if state['room']==world.goal['target'] and state['game_state']==12:
            if reached_at is None:reached_at=f;captures.add(f+1)
            if state['hero_state']==0:saw_target_reset=True
            settled=args.sms or not state['reveal_phase'] and not state['door_loading']
            if saw_target_reset and settled and state['hero_state']==1 and ready_at is None:ready_at=f;captures.add(f+1)
        if ready_at is not None and f in [ready_at+59,ready_at+84,ready_at+99]:captures.add(f+1)
        if ready_at is not None and f==ready_at+60:probe_before=dict(state)
        if ready_at is not None and f==ready_at+85:probe_after=dict(state)
        dying=state['game_state']==20 or (not state['health'] and state['hero_state'] in [8,9])
        if dying and not death_active:death_active=True;deaths+=1
        if state['game_state']==20 and menu_since is None:menu_since=f
        if state['health'] and state['game_state']==12 and state['hero_state']==1:death_active=False;menu_since=None
        if deaths>args.retry_deaths:failure='hero_died'
    def choose(f):
        nonlocal path,cursor,cached_frame,cached_buttons,last_progress,failure
        if f<=prefix_end:return prefix_inputs[f]
        if f==cached_frame:return cached_buttons
        cached_frame=f;cached_buttons=[]
        if ready_at is not None and ready_at+70<=f<=ready_at+74:cached_buttons=[4];return cached_buttons
        if f<2501 or not state or reached_at is not None or failure:return cached_buttons
        if death_active:
            last_progress=f
            if state['game_state']==20 and menu_since is not None and f-menu_since>=180 and f%30==0:cached_buttons=[8]
            return cached_buttons
        if state['game_state']!=12 or state['hero_state'] not in [0,1]:return cached_buttons
        point=(state['room'],state['x'],state['y'])
        while cursor<len(path) and point==tuple(path[cursor][2][:3]):cursor+=1;last_progress=f
        if cursor==len(path):cached_buttons=[4]
        else:
            previous,d,nxt=path[cursor]
            if not state['counter'] and point!=tuple(previous[:3]):
                matches=[n for n,e in enumerate(path) if tuple(e[0][:3])==point]
                if matches:
                    resumed=min(matches,key=lambda n:abs(n-cursor));events.append(dict(frame=f,reason='recover_after_displacement',previous_waypoint=cursor,resumed_waypoint=resumed,actual=point));cursor=resumed;last_progress=f;previous,d,nxt=path[cursor]
                else:
                    replacement,examined=world.route((*point,state['maze']))
                    if replacement:
                        events.append(dict(frame=f,reason='replan_after_displacement',actual=point,remaining_waypoints=len(replacement),visited_nodes=examined));path=replacement;cursor=0;last_progress=f;previous,d,nxt=path[0]
                    else:
                        failure='unexpected_position';events.append(dict(frame=f,failure=failure,expected=previous,actual=point,waypoint=cursor));return []
            cached_buttons=[4+d]
        if f-last_progress>300:
            failure='no_waypoint_progress';events.append(dict(frame=f,failure=failure,waypoint=cursor,**state));return []
        return cached_buttons
    def controller(f):
        buttons=choose(f)
        if not controls or controls[-1]['buttons']!=buttons:controls.append(dict(frame=f,buttons=list(buttons)))
        return buttons
    def stop():return bool(failure) or ready_at is not None and observed_frame-ready_at>=100
    directory=folder/(tag+('-pal' if args.pal else '')+'-'+args.trial)
    assert not directory.exists(),('Keep existing trial evidence; choose a new --trial',directory)
    with contextlib.redirect_stdout(io.StringIO()):run(rom,args.frames,directory,captures,(prefix_presses if args.prefix_combat else ([(200,220,0)] if args.sms else [])+PRESSES[:8]),ram_observer=observe,input_provider=controller,stop_when=stop,core_options={'genesis_plus_gx_region_detect':'pal' if args.pal else 'auto'})
    (directory/'events.json').write_text(json.dumps(events,indent=2)+'\n');(directory/'samples.json').write_text(json.dumps(samples,indent=2)+'\n');(directory/'controls.json').write_text(json.dumps(controls,indent=2)+'\n')
    from PIL import Image
    visible=False
    if ready_at is not None:
        final=Image.open(directory/f'frame_{ready_at+60:05d}.png').convert('RGB');visible=final.getbbox() is not None and final.crop((0,160 if args.sms else 176,256,192 if args.sms else 208)).getbbox() is not None
    probe=bool(probe_before and probe_after and probe_before['room']==probe_after['room']==world.goal['target'] and probe_before['x']==probe_after['x']==128 and probe_before['y']==152 and probe_after['y']==144)
    report=dict(normal_continues=deaths,retry_deaths=args.retry_deaths,door_index=args.door_index,recorded_combat_prefix=args.prefix_combat,prefix_end=prefix_end,region='pal' if args.pal else 'auto',directional_probe_succeeded=probe,probe_before=probe_before,probe_after=probe_after,rendered_final_frame_nonblack=visible,rom_sha256=sha(rom.read_bytes()),reference_sha256=sha(world.rom),reached_entrance=ready_at is not None,first_published_target_room_frame=room_entry_at,first_target_state12_frame=reached_at,first_controllable_frame=ready_at,door_transition_frames=None if ready_at is None else ready_at-room_entry_at,failure=failure,waypoints_reached=cursor,waypoints_planned=len(path),last_state=state,ram_injections=False,sram_checkpoint_injection=False,scope='Read-only state-driven directional controller along ROM-derived static path, normal boot/name/opening. No combat strategy or whole-dungeon claim.')
    (directory/'route_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

if __name__=='__main__':main()
