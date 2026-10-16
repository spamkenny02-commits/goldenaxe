"""Controller-driven key opening, crossing and return in production cartridges.

Boot and dungeon entry execute normally after an exterior fixture. One further
fixture supplies a real locked dungeon room, hero position and inventory.
All opening/crossing/return behavior then runs through the live gameplay loop.
"""
import contextlib,hashlib,io,json,re,sys
from extract_world import ROOT,initial_room
from extract_title import rle_planes
from validate_actor_tick import PRESSES
from run_core import run


def maps(cells,meta):
    sms=bytearray();md=bytearray()
    for y in range(20):
        for x in range(32):
            cell=cells[(y//2)*16+x//2];a=cell*8+(y&1)*4+(x&1)*2
            entry=meta[a:a+2];sms.extend(entry);w=int.from_bytes(entry,'little')
            v=((w>>11)&1)<<13|((w>>12)&1)<<15|((w>>10)&1)<<12|((w>>9)&1)<<11|16+(w&511)
            md.extend(v.to_bytes(2,'big'))
    return bytes(sms),bytes(md)


def main():
    pal='--pal' in sys.argv;death='--death' in sys.argv;suffix='-pal' if pal else ''
    end_frame=4400 if death else 3750
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in
        (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    original=ROOT/'input/original.sms';cartridge=ROOT/'gaw-megadrive.bin';rom=original.read_bytes()
    _,exterior,_,_,arrays,_=initial_room(rom)
    meta=bytearray(2048);patterns=bytearray(16384)
    end,_=rle_planes(arrays['world_dungeon_background_rle'],0,patterns,0,4)
    rle_planes(arrays['world_dungeon_background_rle'],end,meta,0,2)
    door=next(d for d in json.loads((ROOT/'analysis/doors_reference.json').read_bytes())['direct_unconditional_dungeon_doors'] if d['room']==16)
    def cells(room):
        result=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little')
        rle_planes(arrays['world_room_streams'],offset,result,0,1);return bytes(result)
    outside=cells(16);outside_sms,outside_md=maps(outside,exterior)
    results=[]
    for direction,room,x,y,button,reverse,target,flag in [
        ('up',0x120,128,48,4,5,0x110,0x20),
        ('left',0x121,40,80,6,7,0x120,0x40),
        ('right',0x120,216,80,7,6,0x121,0x80)]:
        if any(a.startswith('--direction=') and a.split('=',1)[1]!=direction for a in sys.argv):continue
        for inventory,keys,master in [('ordinary',2,0),('master',5,1),('empty',0,0)]:
            if '--first' in sys.argv and results:break
            room_cells=cells(room);sms,md=maps(room_cells,meta)
            flags=bytearray(256);flags[room&255]=16
            traces={}
            for tag,path in [('sms',original),('md',cartridge)]:
                if tag=='sms':
                    writes=[(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),
                            (3120,0x1c00,outside),(3120,0x1600,outside_sms),(3120,0x600,bytes(768)),
                            (3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),
                            (3400,0xb9,room.to_bytes(2,'little')),(3400,0xa4,b'\x61\xb7'),
                            (3400,0x100,bytes(flags)),(3400,0x1c00,room_cells),(3400,0x1600,sms),
                            (3400,0x600,bytes(768)),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),
                            (3400,0x304,b'\0'),(3400,0x314,bytes(4)),(3400,0xde,bytes([keys])),(3400,0xef,bytes([master]))]
                else:
                    def w(f,k,v):return f,sy[k],v.to_bytes(2,'big')
                    writes=[w(3120,'room_id',16),w(3120,'world_graphics_class',0),
                            (3120,sy['scratch']+0x800,outside),(3120,sy['sms_vram']+0x3800,outside_sms),
                            (3120,sy['world_new_md'],outside_md),(3120,sy['world_actor_state'],bytes(768)),
                            w(3120,'hero_y',(door['y']+8)<<8),w(3120,'hero_x',door['x']<<8),
                            w(3400,'room_id',room),(3400,sy['game_save_state']+0x50,bytes(flags)),
                            (3400,sy['scratch']+0x800,room_cells),(3400,sy['sms_vram']+0x3800,sms),
                            (3400,sy['world_new_md'],md),(3400,sy['md_map'],md),
                            (3400,sy['world_actor_state'],bytes(768)),w(3400,'hero_x',x<<8),w(3400,'hero_y',y<<8),
                            w(3400,'hero_counter',0),w(3400,'hero_dx',0),w(3400,'hero_dy',0),
                            w(3400,'hero_keys',keys),(3400,sy['hero_items']+15,bytes([master]))]
                samples={}
                if death:
                    if tag=='sms':writes.extend([(3800,0x318,b'\0'),(3800,0x600,bytes(768))])
                    else:writes.extend([w(3800,'hero_health',0),(3800,sy['world_actor_state'],bytes(768))])
                def observe(frame,raw):
                    if frame<3390:return
                    if tag=='sms':
                        val=lambda a:int.from_bytes(raw[a:a+2],'little')
                        state=dict(room=val(0xb9),state=raw[0x1d],x=val(0x312),y=val(0x310),keys=raw[0xde],
                                   flags=bytes(raw[0x100:0x200]),cells=bytes(raw[0x1c00:0x1ca0]),map=bytes(raw[0x1600:0x1b00]))
                    else:
                        def data(k,n,off=0):
                            a=sy[k]+off;return bytes(raw[(a+i)^1] for i in range(n))
                        val=lambda k:int.from_bytes(data(k,2),'big')
                        state=dict(room=val('room_id'),state=val('game_state'),x=val('hero_x'),y=val('hero_y'),keys=val('hero_keys'),
                                   flags=data('game_save_state',256,0x50),cells=data('scratch',160,0x800),map=data('sms_vram',1280,0x3800))
                    samples[frame]=state
                with contextlib.redirect_stdout(io.StringIO()):
                    run(path,end_frame,ROOT/f'validation/{tag}-key-gameplay-{direction}-{inventory}{"-continue" if death else ""}{suffix}',{3390,3450,3510,3750,end_frame},
                        ([(200,220,0)] if tag=='sms' else [])+PRESSES+[(3125,3129,4),(3410,3500,button),(3550,3700,reverse)]+([(3970,3974,5),(4000,4004,4),(4030,4034,8)] if death else []),
                        ram_writes=writes,ram_observer=observe,
                        core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
                assert samples[3390]['room']==0x1f0,(tag,'initial dungeon entry')
                opening=next((f for f,s in samples.items() if f>=3400 and s['flags'][room&255]&flag),None)
                reached=next((f for f,s in samples.items() if f>3400 and s['room']==target and s['state']==12),None)
                returned=next((f for f,s in samples.items() if f>=3550 and reached and s['room']==room and s['state']==12),None)
                if inventory=='empty':
                    assert opening is None and reached is None,(tag,direction,'opened without key')
                else:
                    assert opening is not None and reached is not None and returned is not None,(tag,direction,opening,reached,returned,samples[3750]['room'])
                traces[tag]=dict(samples=samples,opening=opening,reached=reached,returned=returned)
            if inventory!='empty':
                for phase in ['reached','returned']:
                    a,b=(t['samples'][t[phase]] for t in traces.values())
                    for field in ['room','x','y','keys','flags','cells','map']:
                        assert a[field]==b[field],(direction,inventory,phase,field)
            expected=keys-(1 if inventory=='ordinary' else 0)
            assert all(t['samples'][3750]['keys']==expected for t in traces.values()),(direction,inventory,'repeated consumption')
            if death:
                a,b=(t['samples'][end_frame] for t in traces.values())
                assert a['room']==b['room']==0x1f0,(direction,inventory,'checkpoint')
                for field in ['room','state','x','y','keys','flags','cells','map']:
                    assert a[field]==b[field],(direction,inventory,'Continue',field)
            results.append(dict(direction=direction,inventory=inventory,room=room,target=target,
                                opened_crossed_returned=inventory!='empty',empty_inventory_refused=inventory=='empty',
                                settled_crossing_return_fields_source_exact=True,keys_after_repeated_contacts=expected,
                                death_continue_persistence_verified=death,
                                timing={tag:{k:v for k,v in t.items() if k!='samples'} for tag,t in traces.items()}))
            print(direction,inventory,'controller opening/crossing/return matches',flush=True)
    if '--first' not in sys.argv:
        assert len(results)==9
        report=dict(md_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),
                    region='pal' if pal else 'auto',cases=results,production_cartridges_unmodified=True,
                    controller_opening_crossing_and_return=True,initial_room_map_position_inventory_controlled=True,
                    save_reload_verified=False,absolute_transition_timing_exact=False,full_natural_dungeon_progression_verified=False)
        (ROOT/f'validation/key_door_{"continue" if death else "gameplay"}{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
