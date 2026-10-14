"""Compare production dungeon edge scrolling after controller-driven entry.

Exterior room/map/position fixtures avoid the untested route to each entrance.
The dungeon is loaded by the production door routine on both consoles. Edge
positions are then controlled; map changes and scrolling execute normally.
"""
import contextlib
import hashlib
import io
import json
import re
import sys
from extract_world import ROOT, initial_room
from extract_title import rle_planes
from validate_actor_tick import PRESSES
from run_core import run


def main():
    pal = '--pal' in sys.argv
    suffix = '-pal' if pal else ''
    sy = {m[2].split('.lto_priv.')[0]: int(m[1], 16)&65535 for line in
          (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
          if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    original = ROOT/'input/original.sms'
    cartridge = ROOT/'gaw-megadrive.bin'
    rom = original.read_bytes()
    _, meta, _, _, arrays, _ = initial_room(rom)
    doors = json.loads((ROOT/'analysis/doors_reference.json').read_bytes())['direct_unconditional_dungeon_doors']
    template = bytearray((ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630])
    actors = bytearray(768)
    for slot, actor_x, actor_y in [(0,80,64),(8,160,112)]:
        actor = bytearray(template)
        actor[3]=1;actor[4]=120;actor[5]=0;actor[6]=255
        actor[0x10:0x18]=bytes(8);actor[0x11]=actor_y;actor[0x13]=actor_x
        actors[slot*48:(slot+1)*48]=actor
    results = []
    for door in [d for d in doors if d['room'] in [0x10, 0x62]]:
        outside, x, y, origin = (door[k] for k in ['room', 'x', 'y', 'target'])
        offset = int.from_bytes(arrays['world_room_index'][outside*2:outside*2+2], 'little')
        cells = bytearray(160)
        rle_planes(arrays['world_room_streams'], offset, cells, 0, 1)
        sms = bytearray()
        md = bytearray()
        for row in range(20):
            for col in range(32):
                cell = cells[(row//2)*16+col//2]
                address = cell*8+(row&1)*4+(col&1)*2
                entry = meta[address:address+2]
                sms.extend(entry)
                word = int.from_bytes(entry, 'little')
                native = ((word>>11)&1)<<13|((word>>12)&1)<<15|((word>>10)&1)<<12|((word>>9)&1)<<11|16+(word&511)
                md.extend(native.to_bytes(2, 'big'))
        for direction, edge_x, edge_y in [('left',14,80),('right',242,80),('up',128,14),('down',80,162)]:
            if '--first' in sys.argv and results:
                break
            target = (origin&0x1f0)|((origin+(-1 if direction=='left' else 1))&15) if direction in ['left','right'] else (origin&256)|((origin+(-16 if direction=='up' else 16))&255)
            traces = {}
            for tag, path in [('sms',original), ('md',cartridge)]:
                samples = {}
                if tag == 'sms':
                    writes = [(3120,0xb9,outside.to_bytes(2,'little')),
                              (3120,0xa4,door['script_entry'].to_bytes(2,'little')),
                              (3120,0x1c00,bytes(cells)),(3120,0x1600,bytes(sms)),
                              (3120,0x600,bytes(768)),
                              (3120,0x310,((y+8)<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),
                              (3510,0x600,bytes(actors)),
                              (3520,0x310,(edge_y<<8).to_bytes(2,'little')+(edge_x<<8).to_bytes(2,'little'))]
                else:
                    def w(frame,name,value):
                        return frame,sy[name],value.to_bytes(2,'big')
                    writes = [w(3120,'room_id',outside),w(3120,'world_graphics_class',0),
                              (3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,bytes(sms)),
                              (3120,sy['world_new_md'],bytes(md)),(3120,sy['world_actor_state'],bytes(768)),
                              w(3120,'hero_y',(y+8)<<8),w(3120,'hero_x',x<<8),
                              (3510,sy['world_actor_state'],bytes(actors)),
                              w(3520,'hero_y',edge_y<<8),w(3520,'hero_x',edge_x<<8)]
                def observe(frame,raw):
                    if frame<3510:
                        return
                    if tag == 'sms':
                        val = lambda a:int.from_bytes(raw[a:a+2],'little')
                        state = dict(room=val(0xb9),state=raw[0x1d],x=val(0x312),y=val(0x310),
                                     cells=bytes(raw[0x1c00:0x1ca0]),map=bytes(raw[0x1600:0x1b00]),
                                     palette=bytes(raw[0x1ca0:0x1cad]),flags=raw[0x100+(target&255)],
                                     masks=bytes(raw[0x200:0x300]))
                    else:
                        raw = bytes(raw[i^1] for i in range(len(raw)))
                        val = lambda k:int.from_bytes(raw[sy[k]:sy[k]+2],'big')
                        a = sy['game_save_state']
                        state = dict(room=val('room_id'),state=val('game_state'),x=val('hero_x'),y=val('hero_y'),
                                     cells=raw[sy['scratch']+0x800:sy['scratch']+0x8a0],
                                     map=raw[sy['sms_vram']+0x3800:sy['sms_vram']+0x3d00],
                                     palette=bytes(raw[sy['sms_palette']+i*2+1] for i in range(13)),
                                     flags=raw[a+0x50+(target&255)],masks=raw[a+0x150:a+0x250])
                    samples[frame] = state
                def video(frame,vram):
                    if frame not in samples:
                        return
                    sprites = []
                    if tag=='sms':
                        for i in range(64):
                            if vram[0x3f00+i]==208:
                                break
                            tile=vram[0x3f81+i*2]
                            if tile<240:
                                sprites.append(tile)
                    else:
                        i=0;seen=set()
                        while i not in seen and len(seen)<80:
                            seen.add(i);p=0xf400+i*8
                            sprite_y=int.from_bytes(vram[p:p+2],'little')&511
                            sprite_x=int.from_bytes(vram[p+6:p+8],'little')&511
                            tile=int.from_bytes(vram[p+4:p+6],'little')&2047
                            if sprite_x and sprite_y and 272<=tile<512:
                                sprites.append(tile)
                            i=int.from_bytes(vram[p+2:p+4],'little')&127
                            if not i:
                                break
                    samples[frame]['nonhero_sprites']=sprites
                folder = ROOT/f'validation/{tag}-dungeon-scroll-{origin:03x}-{direction}{suffix}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(path,3700,folder,{3510,3540,3600,3700},
                        ([(200,220,0)] if tag=='sms' else [])+PRESSES+[(3125,3129,4)],
                        ram_writes=writes,ram_observer=observe,vram_observer=video,
                        core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
                assert samples[3510]['room']==origin,(tag,'door entry failed')
                assert samples[3515]['nonhero_sprites'],(tag,'old actor fixture not visible')
                transitions = [f for f,s in samples.items() if s['state']==10 and f>=3520]
                assert transitions,(tag,direction,'no transition')
                resumed = next((f for f,s in samples.items() if f>transitions[-1] and s['state']==12),None)
                assert resumed is not None,(tag,direction,'never resumed',samples[3700]['room'])
                clean=next(f for f in transitions if not samples[f]['nonhero_sprites'])
                stable=[f for f in transitions if f>=clean] if tag=='sms' else transitions[1:]
                assert all(not samples[f]['nonhero_sprites'] for f in stable),(tag,direction,'objects visible during scroll')
                traces[tag] = dict(first=transitions[0],last=transitions[-1],resumed=resumed,
                                   first_clean_sat_frame=clean,nonhero_sprite_errors=0,
                                   state=samples[resumed])
            source,native = (traces[t]['state'] for t in ['sms','md'])
            assert source['room']==native['room']==target,(origin,direction,'target',source['room'],native['room'],target)
            for field in ['x','y','cells','map','palette','flags','masks']:
                assert source[field]==native[field],(origin,direction,field, source[field] if isinstance(source[field],int) else 'bytes differ', native[field] if isinstance(native[field],int) else '')
            assert source['flags']&16
            results.append(dict(origin=origin,target=target,direction=direction,
                                destination_state_source_exact=True,cell_bytes_exact=160,map_bytes_exact=1280,
                                fixed_palette_bytes_exact=13,persistence_bytes_exact=256,old_objects_hidden=True,
                                dark_destination=(target&255) in arrays['world_dungeon_dark_rooms'],
                                timing={tag:{k:v for k,v in record.items() if k!='state'} for tag,record in traces.items()}))
            print(f'Dungeon scroll {origin:03X}->{target:03X} {direction}: destination matches',flush=True)
    if '--first' not in sys.argv:
        assert len(results)==8
        report = dict(md_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                      source_sha256=hashlib.sha256(rom).hexdigest(),region='pal' if pal else 'auto',cases=results,
                      production_door_entry=True,controlled_exterior_and_edge_positions=True,
                      source_exact_scroll_timing=False,full_natural_dungeon_progression_verified=False)
        (ROOT/f'validation/dungeon_scroll{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
