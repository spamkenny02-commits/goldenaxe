"""Buy a feather, walk out, equip it and return; only initial gold is controlled."""
import argparse,contextlib,io,json
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from natural_dungeon_combat import walk
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--sms',action='store_true');p.add_argument('--tag',required=True);a=p.parse_args();source=a.sms;tag='sms' if source else 'md'
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');out=ROOT/f'validation/feather-purchase-{a.tag}-{tag}';assert not out.exists()
    state={};rows=[];controls=[];tilemap=b'';cached=-1;buttons=[];direction=1;stage='leave';stage_at=4700;cast_at=None;done=None;failure=None
    def observe(f,r):
        nonlocal tilemap,done,failure
        if f<3300:return
        data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k));word=lambda n:int.from_bytes(data(n,2),'big')
        state.update(frame=f,room=int.from_bytes(r[0xb9:0xbb],'little') if source else word('room_id'),graphics=r[0x40] if source else word('world_graphics_class'),game=r[0x1d] if source else word('game_state'),hero=r[0x301] if source else word('hero_state'),counter=r[0x304] if source else word('hero_counter'),x=r[0x313] if source else word('hero_x')>>8,y=r[0x311] if source else word('hero_y')>>8,owned=r[0xe9] if source else data('hero_items',17)[9],selected=r[0xdf] if source else word('hero_selected_item'),slot=r[0xa0] if source else word('inventory_slot'),gold=r[0xdd] if source else word('hero_gold'),health=r[0x318] if source else word('hero_health'),audio_error=0 if source else word('sound_unhandled_command'))
        state.update(resume=0 if source else word('resume_phase'),loading=0 if source else int.from_bytes(data('door_transition_loading',1),'big'))
        tilemap=bytes(r[0x1600:0x1c00]) if source else data('sms_vram',0x4000)[0x3800:0x3e00]
        if f%10==0:rows.append(dict(stage=stage,**state))
        if f==4700 and not(state['room']==0 and state['owned']==1 and state['gold']==0 and state['game']==12):failure='purchase_or_house_route_failed'
        if not state['health'] or state['audio_error']:failure='health_or_audio_failure'
        if cast_at and not state['resume'] and not state['loading'] and state['room']==0x95 and state['game']==12 and state['hero']==1 and state['owned']==state['selected']==0 and done is None:done=f
    def choose(f):
        nonlocal cached,buttons,direction,stage,stage_at,cast_at
        if cached==f:return buttons
        cached=f;buttons=[]
        if f<=4700 or failure or done:return buttons
        if stage=='leave':
            if state['graphics']==0 and state['room']==0x94 and state['game']==12 and state['hero']==1 and not state['resume'] and not state['loading']:stage='settle';stage_at=f
            elif state['graphics']==1 and state['game']==12 and state['hero']==1:
                if state['counter']:buttons=[4+direction]
                else:
                    route=walk(tilemap,(state['x'],state['y']),lambda q:q==(136,160))
                    if route:direction=route[0];buttons=[4+direction]
            return buttons
        if stage=='settle' and f-stage_at>=30:buttons=[0];stage='opening';stage_at=f;return buttons
        if stage=='opening':
            if f-stage_at<6:buttons=[0]
            else:stage='navigate'
            return buttons
        if stage=='navigate' and state['game']==16 and f-stage_at>=40 and f%10==0:
            slot=state['slot']
            if slot%4<1:buttons=[7]
            elif slot//4<2:buttons=[5]
            elif slot==9:buttons=[8];stage='close';stage_at=f
            return buttons
        if stage=='close' and f-stage_at>=20 and state['selected']==9:buttons=[0];stage='cast';stage_at=f;return buttons
        if stage=='cast' and f-stage_at>=60 and state['game']==12 and state['hero']==1:buttons=[8];cast_at=f;stage='wait';return buttons
        return buttons
    def controller(f):
        value=choose(f)
        if f>4700 and (not controls or value!=controls[-1]['buttons']):controls.append(dict(frame=f,buttons=value.copy()))
        return value
    presses=([(200,220,0)] if source else [])+PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3490,6),(3520,3650,4),(3700,3708,7),(3750,3850,4),(4000,4005,5),(4100,4110,8),(4500,4510,0)]
    writes=[(3300,0xdd,b'\x3c')] if source else [(3300,sy['hero_gold'],(60).to_bytes(2,'big'))]
    captures={3900,4300,4700}
    def stop():
        if done:captures.add(done+1)
        return bool(failure) or done is not None and state['frame']>=done+1
    with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),8000,out,captures,presses,ram_writes=writes,ram_observer=observe,input_provider=controller,stop_when=stop)
    (out/'states.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'controls.json').write_text(json.dumps(controls,indent=2)+'\n')
    report=dict(rom_sha256=sha((ROOT/('input/original.sms' if source else 'gaw-megadrive.bin')).read_bytes()),passed=done is not None and not failure,failure=failure,stage=stage,cast_frame=cast_at,ready_frame=done,only_initial_gold_controlled=True,room_position_inventory_checkpoint_injections=False,last=state)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(report);assert report['passed']

if __name__=='__main__':main()
