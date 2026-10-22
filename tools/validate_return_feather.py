"""Source/native feather activation with controlled checkpoint, stats and actors."""
import argparse,contextlib,io,json
from PIL import Image
from pathlib import Path
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha
from extract_world import initial_room
from extract_title import rle_planes
from validate_key_door_gameplay import maps

def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--pal',action='store_true');p.add_argument('--checkpoint',type=lambda x:int(x,0),default=0x95);p.add_argument('--graphics',type=int,default=0);p.add_argument('--hurt',type=int,default=0);p.add_argument('--moving',action='store_true');p.add_argument('--diagnostic',action='store_true');a=p.parse_args()
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');rom=(ROOT/'input/original.sms').read_bytes();_,meta,_,_,arrays,_=initial_room(rom)
    room=0x94;cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);tilemap,_=maps(cells,meta)
    actors=bytearray(768)
    if not a.graphics:
        for slot in [0,2,7]:
            off=slot*48;actors[off]=0x20;actors[off+3]=1;actors[off+6]=255;actors[off+0x11]=24;actors[off+0x13]=24;actors[off+0x18]=10
    traces={};captures={};clock=0
    for tag in ['sms','md']:
        source=tag=='sms';out=ROOT/f'validation/return-feather-{a.tag}-{tag}';assert not out.exists()
        if source:
            writes=[(2810,0xb9,room.to_bytes(2,'little')),(2810,0xa4,rom[0xb762+room*2:0xb764+room*2]),(2810,0xc2,a.checkpoint.to_bytes(2,'little')),(2810,0x40,bytes([a.graphics])),(2810,0x1600,tilemap),(2810,0x1c00,bytes(cells)),(2810,0x600,bytes(actors)),(2810,0x330,bytes(48)),(2810,0x318,bytes([17])),(2810,0xdb,bytes([11,24,37,2])),(2810,0xdf,b'\11'),(2810,0xe9,b'\1'),(2810,0x301,b'\1'),(2810,0x304,b'\0'),(2810,0x305,bytes([a.hurt])),(2810,0x310,bytes.fromhex('00700088')),(2810,0x314,bytes(4))]
        else:
            w=lambda n,v:(2810,sy[n],v.to_bytes(2,'big'))
            writes=[w('room_id',room),w('save_runtime_checkpoint',a.checkpoint),w('world_graphics_class',a.graphics),w('hero_health',17),w('hero_magic',11),w('hero_gold',37),w('hero_keys',2),w('hero_selected_item',9),w('hero_state',1),w('hero_counter',0),w('hero_hurt',a.hurt),w('hero_x',136<<8),w('hero_y',112<<8),w('hero_dx',0),w('hero_dy',0),(2810,sy['hero_items']+9,b'\1'),(2810,sy['world_actor_state'],bytes(actors)),(2810,sy['world_spell_state'],bytes(48)),(2810,sy['scratch']+0x800,bytes(cells)),(2810,sy['sms_vram']+0x3800,tilemap)]
        if a.moving:
            writes.extend([(2860,0x304,b'\4'),(2860,0x314,bytes.fromhex('00000002'))] if source else [(2860,sy['hero_counter'],(4).to_bytes(2,'big')),(2860,sy['hero_dy'],bytes(2)),(2860,sy['hero_dx'],(512).to_bytes(2,'big'))])
        rows=[]
        def observe(f,r):
            nonlocal clock
            if source and f==2859:clock=r[0x2f]
            if f<2850:return
            data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k));word=lambda n:int.from_bytes(data(n,2),'big')
            row=dict(frame=f,room=int.from_bytes(r[0xb9:0xbb],'little') if source else word('room_id'),game=r[0x1d] if source else word('game_state'),hero=r[0x301] if source else word('hero_state'),selected=r[0xdf] if source else word('hero_selected_item'),owned=r[0xe9] if source else data('hero_items',17)[9],health=r[0x318] if source else word('hero_health'),magic=r[0xdb] if source else word('hero_magic'),gold=r[0xdd] if source else word('hero_gold'),keys=r[0xde] if source else word('hero_keys'),x=int.from_bytes(r[0x312:0x314],'little') if source else word('hero_x'),y=int.from_bytes(r[0x310:0x312],'little') if source else word('hero_y'),mask=r[0x294] if source else data('game_save_state',0x250)[0x150+room],hurt=r[0x305] if source else word('hero_hurt'),audio_error=0 if source else word('sound_unhandled_command'))
            rows.append(row)
            if f in [3300,3400]:captures[tag,f]=bytes(r)
        presses=([(200,220,0)] if source else [])+PRESSES[:8]+[(2860,2861,8),(3340,3350,4)]
        with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),3400,out,{2859,2870,2890,2950,3100,3300,3400},presses,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
        (out/'states.json').write_text(json.dumps(rows,indent=2)+'\n');traces[tag]=rows
    results={}
    for tag,rows in traces.items():
        at=lambda f:next(x for x in rows if x['frame']==f);last=at(3300)
        if a.graphics:ok=last['room']==room and last['owned']==1 and last['selected']==9
        else:ok=last['room']==a.checkpoint and last['owned']==last['selected']==0 and last['game']==12 and last['hero']==1 and last['x']==(138 if a.moving else 136)<<8 and last['y']==112<<8 and last['mask']==0xa1
        conserved=all(last[k]==at(2859)[k] for k in ['health','magic','gold','keys'])
        results[tag]=dict(behavior_pass=ok,resources_preserved=conserved,last=last,movement_probe=at(3400)['y']!=last['y'])
    hurt_after_load={}
    if not a.graphics:
        hurt_after_load={tag:next(x['hurt'] for x in rows if x['frame']>2860 and x['owned']==0 and x['game']==12 and x['hero']==0) for tag,rows in traces.items()}
    map_exact=None;pixel_differences=None
    if not a.graphics:
        root=ROOT/f'validation/return-feather-{a.tag}'
        source_vram=(Path(str(root)+'-sms')/'vram_03300.bin').read_bytes()
        raw=captures['md',3300];address=sy['sms_vram']+0x3800;native_map=bytes(raw[(address+i)^1] for i in range(1536))
        map_exact=native_map==source_vram[0x3800:0x3e00]
        left=Image.open(Path(str(root)+'-sms')/'frame_03300.png').convert('RGB');right=Image.open(Path(str(root)+'-md')/'frame_03300.png').convert('RGB').crop((0,16,256,208));colors=set(left.getdata());conv={v:min(colors,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(right.getdata())};pixel_differences=sum(x!=conv[y] for x,y in zip(left.getdata(),right.getdata()))
    passed=(a.graphics or map_exact and len(set(hurt_after_load.values()))==1) and all(x['behavior_pass'] and x['resources_preserved'] and (a.graphics or x['movement_probe']) for x in results.values())
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),passed=passed,region='pal' if a.pal else 'auto',checkpoint=a.checkpoint,graphics=a.graphics,initial_hurt=a.hurt,moving=a.moving,hurt_after_load=hurt_after_load,controlled_room_ownership_checkpoint_stats_and_actors=True,settled_map_and_hud_bytes_exact=1536 if map_exact else 0,settled_palette_normalized_pixel_differences=pixel_differences,results=results,full_game_verified=False)
    (ROOT/f'analysis/return_feather_{a.tag}_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
    if not a.diagnostic:assert passed

if __name__=='__main__':main()
