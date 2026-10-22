"""Normal lantern input after boot/dungeon entry; controlled dark-room fixture."""
import argparse,contextlib,io,json
from run_core import ROOT,run
from validate_playable_sprite_limit import symbols
from extract_world import initial_room
from extract_title import rle_planes
from validate_key_door_gameplay import maps
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--pal',action='store_true');p.add_argument('--boss',action='store_true');p.add_argument('--boss-death',action='store_true');p.add_argument('--diagnostic',action='store_true');a=p.parse_args();a.boss=a.boss or a.boss_death
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');rom=(ROOT/'input/original.sms').read_bytes();_,_,_,_,arrays,_=initial_room(rom)
    patterns=bytearray(16384);meta=bytearray(2048);stop,_=rle_planes(arrays['world_dungeon_background_rle'],0,patterns,0,4);rle_planes(arrays['world_dungeon_background_rle'],stop,meta,0,2)
    cells=bytearray(160);room=0x1d3;offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);tilemap,_=maps(cells,meta)
    actors=bytearray(768);actors[3]=0x40 if a.boss and not a.boss_death else 0
    traces={};clock=0
    for tag in ['sms','md']:
        source=tag=='sms';prefix_name=("sms-pal-01" if a.pal else "sms-06") if source else ("md-pal-v0230" if a.pal else "md-v0230");prefix=ROOT/"validation/natural-dungeon-route"/prefix_name
        c=json.loads((prefix/'capture.json').read_bytes());control=json.loads((prefix/'controls.json').read_bytes());presses=list(map(tuple,c['presses']))
        for n,x in enumerate(control):
            end=control[n+1]['frame']-1 if n+1<len(control) else c['frames']
            presses.extend((x['frame'],end,b) for b in x['buttons'])
        if source:
            writes=[(4300,0xb9,room.to_bytes(2,'little')),(4300,0xa4,rom[0xb762+room*2:0xb764+room*2]),(4300,0x1c00,bytes(cells)),(4300,0x1600,tilemap),(4300,0x600,bytes(actors)),(4300,0x330,bytes(48)),(4300,0x72,b'\1'),(4300,0xad,b'\0'),(4300,0xae,bytes([int(a.boss)])),(4300,0xdf,b'\3'),(4300,0xe3,b'\1'),(4300,0x1ca0,rom[0x17eb8:0x17ec8])]
        else:
            w=lambda n,v:(4300,sy[n],v.to_bytes(2,'big'))
            writes=[w('room_id',room),w('world_dungeon_dark',1),w('hero_selected_item',3),(4300,sy['hero_items']+3,b'\1'),(4300,sy['scratch']+0x800,bytes(cells)),(4300,sy['sms_vram']+0x3800,tilemap),(4300,sy['world_actor_state'],bytes(actors)),(4300,sy['world_spell_state'],bytes(48)),(4300,sy['sms_palette'],b''.join(v.to_bytes(2,'big') for v in rom[0x17eb8:0x17ec8]))]
            if a.boss_death:writes.extend([(4300,sy['world_boss_state'],b'\1'),(4300,sy['boss_death_music_hold'],b'\1')])
            writes.extend([(4400,sy['vtimer'],clock.to_bytes(4,'big')),(4400,sy['world_clock_shift'],bytes(4))])
        rows=[]
        def observe(f,r):
            nonlocal clock
            if source and f==4399:clock=r[0x2f]
            if f==4299:
                if source:assert r[0x1d]==12 and r[0x40]==2 and r[0x37]==1
                else:
                    value=lambda name:int.from_bytes(bytes(r[(sy[name]+i)^1] for i in range(2)),'big')
                    assert value('game_state')==12 and value('world_graphics_class')==2 and value('world_dungeon_number')==1
            if f<4380:return
            data=lambda name,n:bytes(r[(sy[name]+i)^1] for i in range(n));word=lambda name:int.from_bytes(data(name,2),'big')
            row=dict(frame=f,selected=r[0xdf] if source else word('hero_selected_item'),dark=r[0x72] if source else word('world_dungeon_dark'),game=r[0x1d] if source else word('game_state'),magic=r[0xdb] if source else word('hero_magic'),health=r[0x318] if source else word('hero_health'),owned=r[0xe3] if source else data('hero_items',17)[3],clock=r[0x2f] if source else (int.from_bytes(data('vtimer',4),'big')-int.from_bytes(data('world_clock_shift',4),'big'))&255,palette=list(r[0x1ca0:0x1cc0]) if source else [int.from_bytes(data('sms_palette',64)[i:i+2],'big') for i in range(0,64,2)],audio=r[0x1e05] if source else data('sound_ram',400)[5])
            rows.append(row)
        out=ROOT/f'validation/lantern-{a.tag}-{tag}';assert not out.exists()
        with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),4740,out,{4399,4420,4500,4630,4680,4740},presses+[(4400,4410,8),(4600,4601,8),(4640,4641,0),(4660,4661,7),(4665,4666,7),(4670,4671,7),(4675,4676,8),(4690,4691,0),(4725,4726,8)],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
        (out/'states.json').write_text(json.dumps(rows,indent=2)+'\n');traces[tag]=rows
    cases={tag:dict(activated=rows[0]['dark']==1 and any(x['dark']==0 for x in rows),lit=rows[-1]['dark']==0,selected_reset=next(x for x in rows if x['frame']==4590)['selected']==0,owned=rows[-1]['owned'],repeat_keeps_selection=rows[-1]['selected']==3,magic_preserved=rows[-1]['magic']==rows[0]['magic'],menu_return=rows[-1]['game']==12,lit_through_menu=all(x['dark']==0 for x in rows if x['frame']>=4590)) for tag,rows in traces.items()}
    pairs=list(zip(traces['sms'],traces['md']));activation=[(x,y) for x,y in pairs if 4400<=x['frame']<4458]
    activation_exact=all(x['palette'][:16]==y['palette'][:16] for x,y in activation)
    settled=all(traces['sms'][-1]['palette'][n]==traces['md'][-1]['palette'][n] for n in range(13))
    passed=activation_exact and settled and all(x['activated'] and x['lit'] and x['selected_reset'] and x['owned']==1 and x['magic_preserved'] and x['menu_return'] and x['lit_through_menu'] and x['repeat_keeps_selection'] for x in cases.values())
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),passed=passed,region='pal' if a.pal else 'auto',controlled_room_and_ownership=True,boss_context_flag=a.boss,boss_death_latch=a.boss_death,initial_clock_aligned=True,activation_background_palette_frames_exact=58 if activation_exact else 0,cases=cases,settled_noncycling_background_palette_exact=settled,full_game_verified=False)
    (ROOT/f'analysis/lantern_{a.tag}_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
    if not a.diagnostic:assert passed

if __name__=='__main__':main()
