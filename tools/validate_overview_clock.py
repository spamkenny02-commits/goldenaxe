"""Overview logical clock and marker cycle with only a pre-activation alignment."""
import argparse,contextlib,io,json
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--rom');p.add_argument('--symbols');p.add_argument('--pal',action='store_true');p.add_argument('--sweep',action='store_true');p.add_argument('--held-close',action='store_true');p.add_argument('--close-b',action='store_true');p.add_argument('--graphics',type=int,default=0);p.add_argument('--treasure',action='store_true');p.add_argument('--edited',action='store_true');p.add_argument('--all-flags',action='store_true');p.add_argument('--ice',action='store_true');p.add_argument('--diagnostic',action='store_true');a=p.parse_args()
    native_rom=ROOT/a.rom if a.rom else ROOT/'gaw-megadrive.bin';sy=symbols(ROOT/a.symbols if a.symbols else ROOT/'megadrive/out/release/symbol.txt');clock=0;cases={};parts={};generations={};traces={}
    for tag in ['sms','md']:
        source=tag=='sms';out=ROOT/f'validation/overview-clock-{a.tag}-{tag}';assert not out.exists()
        writes=[(2810,0xdf,b'\13'),(2810,0xeb,b'\1'),(2810,0xf5,bytes([a.treasure])),(2810,0x600,bytes(768))] if source else [(2810,sy['hero_selected_item'],(11).to_bytes(2,'big')),(2810,sy['hero_items']+11,b'\1'),(2810,sy['game_save_state']+0x45,bytes([a.treasure])),(2810,sy['world_actor_state'],bytes(768)),(2850,sy['vtimer'],clock.to_bytes(4,'big')),(2850,sy['world_clock_shift'],bytes(4))]
        if a.all_flags:writes.append((2810,0x110 if source else sy['game_save_state']+0x60,bytes([1])*240))
        if a.ice:writes.append((2810,0xac if source else sy['ice_bell_state'],b'\1' if source else b'\0\1'))
        if a.edited:writes.append((2810,0x111 if source else sy['game_save_state']+0x61,b'\1'))
        if a.graphics:writes.append((2810,0x40 if source else sy['world_graphics_class'],bytes([a.graphics]) if source else a.graphics.to_bytes(2,'big')))
        state={};rows=[];last_room=None;rooms=[]
        def observe(f,r):
            nonlocal clock,last_room
            if source and f==2849:clock=r[0x2f]
            if f<2849:return
            data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k));word=lambda n:int.from_bytes(data(n,2),'big')
            room=int.from_bytes(r[0xb9:0xbb],'little') if source else word('room_id')
            if room!=last_room:rooms.append(dict(frame=f,room=room));last_room=room
            state.update(frame=f,clock=r[0x2f] if source else word('overview_clock') if word('world_overview_active') and 'overview_clock' in sy else (int.from_bytes(data('vtimer',4),'big')-int.from_bytes(data('world_clock_shift',4),'big'))&255,room=room,hero=r[0x301] if source else word('hero_state'),selected=r[0xdf] if source else word('hero_selected_item'),owned=r[0xeb] if source else data('hero_items',17)[11],game=r[0x1d] if source else word('game_state'),x=int.from_bytes(r[0x312:0x314],'little') if source else word('hero_x'),y=int.from_bytes(r[0x310:0x312],'little') if source else word('hero_y'),health=r[0x318] if source else word('hero_health'),gold=r[0xdd] if source else word('hero_gold'),magic=r[0xdb] if source else word('hero_magic'),audio_error=0 if source else word('sound_unhandled_command'),overview=0 if source else word('world_overview_active'),pacing_error=0 if source else word('overview_pacing_error'))
            rows.append(state.copy())
            if f==3700:
                parts[tag]=dict(selected=state['selected'],patterns=None if source else data('sms_vram',5120).hex(),map=None if source else data('sms_vram',0x3d00)[0x3800:].hex())
        with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms' if source else native_rom,4201,out,({2859,3000,4000,3700,3701,3716,3717,3732,3733,4200,4201}|(set(range(3700,3734)) if a.sweep else set())),([(200,220,0)] if source else [])+PRESSES[:8]+[(2860,2861,8),(4000,7601,0 if a.close_b else 8)]+([(3000,3600,0)] if a.held_close else []),ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
        if source:
            v=(out/'vram_03700.bin').read_bytes();parts[tag]['patterns']=v[:5120].hex();parts[tag]['map']=v[0x3800:0x3d00].hex()
        (out/'states.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'rooms.json').write_text(json.dumps(rooms,indent=2)+'\n');cases[tag]=state.copy();generations[tag]=rooms;traces[tag]=rows
    pixels=[]
    for f in (range(3700,3733) if a.sweep else [3700,3716,3732]):
        left=Image.open(ROOT/f'validation/overview-clock-{a.tag}-sms/frame_{f:05}.png').convert('RGB');right=Image.open(ROOT/f'validation/overview-clock-{a.tag}-md/frame_{f:05}.png').convert('RGB').crop((0,16,256,208));palette=set(left.getdata());conv={v:min(palette,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(right.getdata())};pixels.append(dict(frame=f,differences=sum(x!=conv[y] for x,y in zip(left.getdata(),right.getdata()))))
    patterns=parts['sms']['patterns']==parts['md']['patterns'];tilemap=parts['sms']['map']==parts['md']['map']
    byframe={tag:{x['frame']:x for x in rows} for tag,rows in traces.items()}
    offsets={(byframe['md'][f]['clock']-byframe['sms'][f]['clock'])&255 for f in range(3500,4000)}
    phase_offset=next(iter(offsets)) if len(offsets)==1 else None
    logical_pixels=[]
    if phase_offset in [0,1]:
        for f in (range(3700,3733) if a.sweep else [3700,3716,3732]):
            sf=f+phase_offset;assert byframe['sms'][sf]['clock']==byframe['md'][f]['clock']
            left=Image.open(ROOT/f'validation/overview-clock-{a.tag}-sms/frame_{sf:05}.png').convert('RGB');right=Image.open(ROOT/f'validation/overview-clock-{a.tag}-md/frame_{f:05}.png').convert('RGB').crop((0,16,256,208));palette=set(left.getdata());conv={v:min(palette,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(right.getdata())};logical_pixels.append(dict(source_frame=sf,native_frame=f,differences=sum(x!=conv[y] for x,y in zip(left.getdata(),right.getdata())),clock=byframe['md'][f]['clock']))
    visual_ok=bool(logical_pixels) and all(not x['differences'] for x in logical_pixels)
    returned=all(x['room']==0x95 and x['hero']==1 and x['selected']==0 and x['owned']==1 and x['game']==12 and x['x']==136<<8 and x['y']==112<<8 and not x['audio_error'] for x in cases.values())
    generation_clocks={};generation_expected=(byframe['sms'][2859]['clock']+3)&255
    if not a.graphics:
        for tag in ['sms','md']:
            first=generations[tag][1]['frame'];last=generations[tag][-1]['frame'];values={byframe[tag][f]['clock'] for f in range(first,last)};generation_clocks[tag]=sorted(values)
        generation_ok=all(v==[generation_expected] for v in generation_clocks.values())
    else:generation_ok=True
    if a.graphics:
        returned=all(x['room']==0x95 and x['hero']==1 and x['selected']==11 and x['owned']==1 and x['game']==12 and not x['audio_error'] for x in cases.values());passed=returned
    elif a.held_close:passed=returned and all(v['selected']==0 for v in parts.values()) and visual_ok
    else:passed=patterns and tilemap and returned and all(v['selected']==11 for v in parts.values()) and visual_ok
    ui_clock_mismatches=[f for f in range(3500,4000) if byframe['sms'][f]['clock']!=byframe['md'][f]['clock']]
    passed=passed and generation_ok and phase_offset in [0,1] and not cases['md']['pacing_error']
    result=dict(steady_clock_phase_offset=phase_offset,generation_counter_values=generation_clocks,generation_expected_counter=generation_expected,generation_counter_frozen=generation_ok,logical_clock_pixel_comparisons=logical_pixels,physical_frames_exact=False,ui_clock_mismatches=ui_clock_mismatches,initial_clock_alignment_frame=2850,clock_alignment_after_activation=False,all_room_flags=a.all_flags,ice=a.ice,md_sha256=sha(native_rom.read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=passed,region='pal' if a.pal else 'auto',graphics=a.graphics,marker_sweep=a.sweep,held_close_during_generation=a.held_close,close_button='B' if a.close_b else 'C',sample_selections={k:v['selected'] for k,v in parts.items()},treasure=a.treasure,edited_room_11=a.edited,controlled_ownership_quest_flags_and_one_clock_alignment=True,overview_planar_5120_bytes_exact=patterns,overview_tilemap_1280_bytes_exact=tilemap,pixel_comparisons=pixels,return_verified=returned,final=cases,room_progress=generations,full_game_verified=False)
    (ROOT/f'analysis/overview_clock_{a.tag}_report.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='room_progress'});assert passed or a.diagnostic

if __name__=='__main__':main()
