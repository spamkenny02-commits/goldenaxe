"""Controlled starting rooms, then actual controller-driven dungeon entry/exit.

Both consoles boot normally. Test-only RAM fixtures supply an exterior room
and its base map; all subsequent door dispatch and destination loading are
executed by the production cartridges. Absolute fade timing is not asserted.
"""
import contextlib,hashlib,io,json,re,sys
from extract_world import ROOT,initial_room
from extract_title import rle_planes
from validate_actor_tick import PRESSES
from run_core import run


def main():
    pal='--pal' in sys.argv;death='--death' in sys.argv;suffix='-pal' if pal else ''
    end_frame=4100 if death else 3700
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in
        (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    rom=(ROOT/'input/original.sms').read_bytes();_,meta,_,_,arrays,_=initial_room(rom)
    doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_dungeon_doors']
    if '--first' in sys.argv:doors=doors[:1]
    results=[]
    for door in doors:
        room,x,y,target=(door[k] for k in ['room','x','y','target'])
        index=arrays['world_room_index'];offset=int.from_bytes(index[room*2:room*2+2],'little')
        cells=bytearray(160);rle_planes(arrays['world_room_streams'],offset,cells,0,1)
        sms=bytearray();md=bytearray()
        for row in range(20):
            for col in range(32):
                cell=cells[(row//2)*16+col//2];address=cell*8+(row&1)*4+(col&1)*2
                entry=meta[address:address+2];sms.extend(entry);word=int.from_bytes(entry,'little')
                native=((word>>11)&1)<<13|((word>>12)&1)<<15|((word>>10)&1)<<12|((word>>9)&1)<<11|16+(word&511)
                md.extend(native.to_bytes(2,'big'))
        traces={};captures={}
        for tag,cartridge in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
            samples={}
            if tag=='sms':
                writes=[(3120,0xb9,room.to_bytes(2,'little')),
                    (3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),
                    (3120,0x1600,bytes(sms)),(3120,0x600,bytes(768)),
                    (3120,0x310,((y+8)<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),
                    (3520,0x310,(152<<8).to_bytes(2,'little')+(128<<8).to_bytes(2,'little'))]
            else:
                def w(frame,name,value):return (frame,sy[name],value.to_bytes(2,'big'))
                writes=[w(3120,'room_id',room),w(3120,'world_graphics_class',0),
                    (3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,bytes(sms)),
                    (3120,sy['world_new_md'],bytes(md)),(3120,sy['world_actor_state'],bytes(768)),
                    w(3120,'hero_y',(y+8)<<8),w(3120,'hero_x',x<<8),
                    w(3520,'hero_y',152<<8),w(3520,'hero_x',128<<8)]
            def observe(frame,raw):
                if frame<3120:return
                if tag=='sms':
                    val=lambda a,n=1:int.from_bytes(raw[a:a+n],'little')
                    state=dict(room=val(0xb9,2),state=val(0x1d),x=val(0x312,2),y=val(0x310,2),
                        direction=val(0x30a),return_room=val(0xbb,2),return_x=val(0xbe),return_y=val(0xbd),
                        checkpoint=val(0xc4,2),flags=val(0x100+(target&255)),music=val(0x65))
                    if frame in [3400,3700]:captures[(tag,frame)]=bytes(raw)
                else:
                    raw=bytes(raw[i^1] for i in range(len(raw)))
                    val=lambda name:int.from_bytes(raw[sy[name]:sy[name]+2],'big')
                    a=sy['game_save_state']
                    state=dict(room=val('room_id'),state=val('game_state'),x=val('hero_x'),y=val('hero_y'),
                        direction=val('hero_direction'),return_room=val('house_return_room'),
                        return_x=val('house_return_x')>>8,return_y=val('house_return_y')>>8,
                        checkpoint=int.from_bytes(raw[a+0x14:a+0x16],'little'),
                        flags=raw[a+0x50+(target&255)],music=val('sound_current_track'))
                    if frame in [3400,3700]:captures[(tag,frame)]=raw
                samples[frame]=state
                if frame==end_frame:captures[(tag,frame)]=bytes(raw)
            folder=ROOT/f'validation/{tag}-dungeon-{"continue" if death else "door"}-{room:02x}{suffix}'
            presses=PRESSES+[(3125,3129,4),(3525,3529,5)]
            if death:
                writes=[item for item in writes if item[0]!=3520]
                if tag=='sms':writes.extend([(3520,0x318,b'\0'),(3520,0x600,bytes(768)),(3760,0xdd,b'\x64')])
                else:writes.extend([w(3520,'hero_health',0),(3520,sy['world_actor_state'],bytes(768)),w(3760,'hero_gold',100)])
                presses=PRESSES+[(3125,3129,4),(3700,3704,5),(3730,3734,4),(3760,3764,8)]
            with contextlib.redirect_stdout(io.StringIO()):
                run(cartridge,end_frame,folder,{3400,end_frame},([(200,220,0)] if tag=='sms' else [])+presses,
                    ram_writes=writes,ram_observer=observe,
                    core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
            traces[tag]=samples
        for frame in [3400,end_frame]:
            source,native=(traces[tag][frame] for tag in ['sms','md'])
            for field in ['room','state','x','y','direction','return_room','return_x','return_y','checkpoint']:
                assert source[field]==native[field],(door,frame,field,source,native)
            source_ram=captures[('sms',frame)];native_ram=captures[('md',frame)]
            start=sy['game_save_state']+0x150
            assert source_ram[0x200:0x300]==native_ram[start:start+256],(door,frame,'actor persistence masks')
        assert traces['sms'][3400]['room']==target and traces['sms'][end_frame]['room']==(target if death else room),(door,'did not enter/exit',traces['sms'][3400],traces['sms'][end_frame])
        source=captures[('sms',3400)];native=captures[('md',3400)]
        assert source[0x1c00:0x1ca0]==native[sy['scratch']+0x800:sy['scratch']+0x8a0],(door,'dungeon cells')
        assert source[0x1600:0x1b00]==native[sy['sms_vram']+0x3800:sy['sms_vram']+0x3d00],(door,'dungeon map words')
        palette=bytes(int.from_bytes(native[sy['sms_palette']+i*2:sy['sms_palette']+i*2+2],'big') for i in range(16))
        assert source[0x1ca0:0x1cad]==palette[:13],(door,'dungeon fixed palette')
        cycle={bytes((0,0,0))}|{arrays['world_dungeon_color_cycle'][i:i+3] for i in range(0,12,3)}
        assert source[0x1cad:0x1cb0] in cycle and palette[13:16] in cycle,(door,'dungeon palette cycle')
        assert traces['md'][3400]['flags']&0x10 and traces['sms'][3400]['flags']&0x10,(door,'visited')
        assert traces['md'][3400]['music']==traces['sms'][3400]['music'],(door,'music')
        if death:
            source=captures[('sms',end_frame)];native=captures[('md',end_frame)]
            for name,offset,expected in [('hero_health',0x318,24),('hero_magic',0xdb,24),('hero_gold',0xdd,75)]:
                assert int.from_bytes(native[sy[name]:sy[name]+2],'big')==source[offset]==expected,(door,'continued stats',name)
        results.append(dict(room=room,target=target,entry_index=door['index'],
            settled_entry_exit_fields_source_exact=True,base_cell_bytes_exact=160,map_word_bytes_exact=1280,
            visited_flag_source_exact=True,music_source_exact=True,fixed_palette_bytes_source_exact=13,
            animated_palette_colors_valid=True,palette_cycle_phase_exact=False,
            actor_mask_bytes_source_exact=512,
            first_entry_frame={tag:next(f for f,s in t.items() if s['room']==target) for tag,t in traces.items()},
            first_return_frame={} if death else {tag:next(f for f,s in t.items() if f>3520 and s['room']==room) for tag,t in traces.items()},
            death_continue_checked=death))
        print(f'Dungeon {room:02X}->{target:03X} {"Continue" if death else "entry/exit"} matches settled source state',flush=True)
    if '--first' not in sys.argv:
        report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
            source_sha256=hashlib.sha256(rom).hexdigest(),region='pal' if pal else 'auto',cases=results,
            controlled_initial_room_map_and_position=True,entry_exit_by_normal_controller=True,
            absolute_transition_timing_exact=False,full_natural_dungeon_progression_verified=False)
        (ROOT/f'validation/dungeon_{"continue" if death else "doors"}{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
