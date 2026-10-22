"""Original/native overview pixels and return, with controlled ownership/flags."""
import argparse,contextlib,io,json
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--pal',action='store_true');p.add_argument('--sweep',action='store_true');p.add_argument('--held-close',action='store_true');p.add_argument('--close-b',action='store_true');p.add_argument('--graphics',type=int,default=0);p.add_argument('--treasure',action='store_true');p.add_argument('--edited',action='store_true');p.add_argument('--diagnostic',action='store_true');a=p.parse_args()
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');clock=0;cases={};parts={};generations={}
    for tag in ['sms','md']:
        source=tag=='sms';out=ROOT/f'validation/world-overview-{a.tag}-{tag}';assert not out.exists()
        writes=[(2810,0xdf,b'\13'),(2810,0xeb,b'\1'),(2810,0xf5,bytes([a.treasure])),(2810,0x600,bytes(768))] if source else [(2810,sy['hero_selected_item'],(11).to_bytes(2,'big')),(2810,sy['hero_items']+11,b'\1'),(2810,sy['game_save_state']+0x45,bytes([a.treasure])),(2810,sy['world_actor_state'],bytes(768)),(7000,sy['vtimer'],clock.to_bytes(4,'big')),(7000,sy['world_clock_shift'],bytes(4))]
        if a.edited:writes.append((2810,0x111 if source else sy['game_save_state']+0x61,b'\1'))
        if a.graphics:writes.append((2810,0x40 if source else sy['world_graphics_class'],bytes([a.graphics]) if source else a.graphics.to_bytes(2,'big')))
        state={};rows=[];last_room=None;rooms=[]
        def observe(f,r):
            nonlocal clock,last_room
            if source and f==6999:clock=r[0x2f]
            if f<2859:return
            data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k));word=lambda n:int.from_bytes(data(n,2),'big')
            room=int.from_bytes(r[0xb9:0xbb],'little') if source else word('room_id')
            if room!=last_room:rooms.append(dict(frame=f,room=room));last_room=room
            state.update(frame=f,room=room,hero=r[0x301] if source else word('hero_state'),selected=r[0xdf] if source else word('hero_selected_item'),owned=r[0xeb] if source else data('hero_items',17)[11],game=r[0x1d] if source else word('game_state'),x=int.from_bytes(r[0x312:0x314],'little') if source else word('hero_x'),y=int.from_bytes(r[0x310:0x312],'little') if source else word('hero_y'),health=r[0x318] if source else word('hero_health'),gold=r[0xdd] if source else word('hero_gold'),magic=r[0xdb] if source else word('hero_magic'),audio_error=0 if source else word('sound_unhandled_command'),overview=0 if source else word('world_overview_active'))
            if f%10==0:rows.append(state.copy())
            if f==7000:
                parts[tag]=dict(selected=state['selected'],patterns=None if source else data('sms_vram',5120).hex(),map=None if source else data('sms_vram',0x3d00)[0x3800:].hex())
        with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),8500,out,({2859,3000,4000,7000,7016,7032,8500}|(set(range(7000,7033)) if a.sweep else set())),([(200,220,0)] if source else [])+PRESSES[:8]+[(2860,2861,8),(7600,7601,0 if a.close_b else 8)]+([(3000,3600,0)] if a.held_close else []),ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
        if source:
            v=(out/'vram_07000.bin').read_bytes();parts[tag]['patterns']=v[:5120].hex();parts[tag]['map']=v[0x3800:0x3d00].hex()
        (out/'states.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'rooms.json').write_text(json.dumps(rooms,indent=2)+'\n');cases[tag]=state.copy();generations[tag]=rooms
    pixels=[]
    for f in (range(7000,7033) if a.sweep else [7000,7016,7032]):
        left=Image.open(ROOT/f'validation/world-overview-{a.tag}-sms/frame_{f:05}.png').convert('RGB');right=Image.open(ROOT/f'validation/world-overview-{a.tag}-md/frame_{f:05}.png').convert('RGB').crop((0,16,256,208));palette=set(left.getdata());conv={v:min(palette,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(right.getdata())};pixels.append(dict(frame=f,differences=sum(x!=conv[y] for x,y in zip(left.getdata(),right.getdata()))))
    patterns=parts['sms']['patterns']==parts['md']['patterns'];tilemap=parts['sms']['map']==parts['md']['map']
    returned=all(x['room']==0x95 and x['hero']==1 and x['selected']==0 and x['owned']==1 and x['game']==12 and x['x']==136<<8 and x['y']==112<<8 and not x['audio_error'] for x in cases.values())
    if a.graphics:
        returned=all(x['room']==0x95 and x['hero']==1 and x['selected']==11 and x['owned']==1 and x['game']==12 and not x['audio_error'] for x in cases.values())
        passed=returned
    elif a.held_close:passed=returned and all(v['selected']==0 for v in parts.values()) and all(not x['differences'] for x in pixels)
    else:passed=patterns and tilemap and returned and all(v['selected']==11 for v in parts.values()) and all(not x['differences'] for x in pixels)
    result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=passed,region='pal' if a.pal else 'auto',graphics=a.graphics,marker_sweep=a.sweep,held_close_during_generation=a.held_close,close_button='B' if a.close_b else 'C',sample_selections={k:v['selected'] for k,v in parts.items()},treasure=a.treasure,edited_room_11=a.edited,controlled_ownership_quest_flags_and_one_clock_alignment=True,overview_planar_5120_bytes_exact=patterns,overview_tilemap_1280_bytes_exact=tilemap,pixel_comparisons=pixels,return_verified=returned,final=cases,room_progress=generations,full_game_verified=False)
    (ROOT/f'analysis/world_overview_{a.tag}_report.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='room_progress'});assert passed or a.diagnostic

if __name__=='__main__':main()
