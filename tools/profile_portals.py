"""Read-only source portal transition profiling after controlled real entry."""
import contextlib,ctypes as c,hashlib,io,json,sys
from validate_key_door_gameplay import ROOT,initial_room,rle_planes,maps,PRESSES,run

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    pal='--pal' in sys.argv;suffix='-pal' if pal else '';original=ROOT/'input/original.sms';rom=original.read_bytes()
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_portal_timing_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
    records=[r for r in json.loads((ROOT/'analysis/contact_script_reference.json').read_bytes())['records'] if r['target']==0x5cfb]
    chosen=next((int(a.split('=',1)[1],16) for a in sys.argv if a.startswith('--room=')),None)
    if chosen is not None:records=[r for r in records if r['room']==chosen]
    assert records
    prepared=json.loads((ROOT/'analysis/portal_prepared_rooms.json').read_bytes());assert prepared['source_sha256']==sha(rom)
    _,ext,_,_,arrays,_=initial_room(rom);patterns=bytearray(16384);meta=bytearray(2048)
    end,_=rle_planes(arrays['world_dungeon_background_rle'],0,patterns,0,4);rle_planes(arrays['world_dungeon_background_rle'],end,meta,0,2)
    def cells(room):
        result=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,result,0,1);return bytes(result)
    door=next(d for d in json.loads((ROOT/'analysis/doors_reference.json').read_bytes())['direct_unconditional_dungeon_doors'] if d['room']==16)
    outside=cells(16);osms,_=maps(outside,ext);results=[]
    for record in records:
        result=None
        for approach in [3,2,0,1]:
            room=record['room'];target=record['coordinate'];destination=record['destination_room']
            positions=[(x,y) for y in range(16,169,8) for x in range(16,241,8) if (((y-12)&248)*8+(((x-12)>>2)&62)+126)==target]
            assert len(positions)==1;(x,y),=positions
            direction=approach
            if direction==3:x-=8
            elif direction==2:x+=8
            elif direction==0:y+=8
            else:y-=8
            initial_coordinate=(((y-12)&248)*8+(((x-12)>>2)&62)+126)
            source_cells=bytes.fromhex(prepared['rooms'][str(room)]['cells']);sms=bytes.fromhex(prepared['rooms'][str(room)]['map']);flags=bytearray(256);flags[room&255]=prepared['rooms'][str(room)]['flag'];actors=bytearray(768);actors[0]=1;actors[6]=255
            writes=[(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,outside),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),
            (3400,0xb9,room.to_bytes(2,'little')),(3400,0xa4,rom[0xb762+room*2:0xb764+room*2]),(3400,0x100,bytes(flags)),(3400,0x1c00,source_cells),(3400,0x1600,sms),(3400,0x330,bytes(48)),(3400,0x4b0,bytes(336)),(3400,0x600,actors),(3400,0xa2,b'\x01'),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(3400,0x304,b'\0'),(3400,0x314,bytes(4)),(3400,0x30a,bytes([direction])),(3400,0x64,bytes([direction])),(3400,0x62,initial_coordinate.to_bytes(2,'little')),(3400,0xa8,b'\0'),(3400,0xa9,b'\0')]
            states=[];events=[];vrams=[];previous=0;wipe_initial=[]
            def observe(frame,raw):
                nonlocal previous
                if frame==3390:dll.gaw_timing_reset();previous=0
                if frame<3390:return
                count=dll.gaw_timing_count();p=dll.gaw_timing_events()
                for n in range(previous,count):
                    pc,cycles,irq,r,clock,hl,de,bc=[int(p[n*8+j]) for j in range(8)]
                    events.append(dict(frame=frame,pc=pc,master_cycles=cycles,irq_master_cycles=irq,room=r,clock=clock,hl=hl,de=de,bc=bc))
                previous=count
                if frame<3400:return
                word=lambda a:int.from_bytes(raw[a:a+2],'little')
                states.append(dict(frame=frame,room=word(0xb9),state=raw[0x1d],x=word(0x312),y=word(0x310),direction=raw[0x30a],counter=raw[0x304],shutter=raw[0xa8],count=raw[0xa2],coordinate=word(0x60),flags=raw[0xa6],mask=raw[0x200+(room&255)],destination_flag=raw[0x100+(destination&255)],cells_sha256=sha(raw[0x1c00:0x1ca0]),map_sha256=sha(raw[0x1600:0x1b00])))
            def vram(frame,data):
                if any(e['pc']==0x1f83 and e['frame']==frame for e in events) and not wipe_initial:
                    wipe_initial.append(data[0x3800:0x3e00].hex())
                if 3408<=frame<=3480:
                    words=[int.from_bytes(data[i:i+2],'little') for i in range(0x3800,0x3e00,2)]
                    vrams.append(dict(frame=frame,blank_words=sum(w==0x18ff for w in words),map_sha256=sha(data[0x3800:0x3e00])))
            folder=ROOT/f'validation/source-portal-{room:03x}-{direction}{suffix}'
            with contextlib.redirect_stdout(io.StringIO()):run(original,3550,folder,{3390,3400,3410,3420,3430,3440,3480,3550},[(200,220,0)]+PRESSES+[(3125,3129,4),(3410,3435,[4,5,6,7][direction])],core=core,ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
            success=[e for e in events if e['pc']==0x5d09]
            if not success:continue
            trigger=success[0];finish=next(e for e in events if e['pc']==0x5d4b and e['master_cycles']>trigger['master_cycles'])
            phases=[e for e in events if trigger['master_cycles']<=e['master_cycles']<=finish['master_cycles'] and e['pc'] in [0x5d09,0x1f78,0x1f83,0x1fa4,0x2260,0x2279,0x5d17,0x5d41,0x5d4b]]
            settled=states[-1];assert settled['room']==destination and settled['state']==12,(room,settled)
            resume=next(v['frame'] for v in states if v['frame']>finish['frame'] and v['state']==12)
            loader=[e for e in events if finish['master_cycles']<e['master_cycles'] and e['frame']<=resume and e['pc'] in [0x0b56,0x0c98,0x032a,0x0bfe,0x24c5,0x1780,0x24ed,0x24f2]]
            assert len(wipe_initial)==1
            result=dict(wipe_initial_map=wipe_initial[0],loader_phases=loader,room=room,destination=destination,coordinate=target,initial_hero=[x,y],approach_direction=direction,trigger_frame=trigger['frame'],script_return_frame=finish['frame'],phases=phases,states=states,nametable_frames=vrams,settled=settled)
            break
        assert result,(hex(record['room']),'no traversable approach found')
        results.append(result);print(hex(room),'->',hex(destination),'trigger',trigger['frame'],'return',finish['frame'],'settled',settled['x']//256,settled['y']//256,flush=True)
    report=dict(source_sha256=sha(rom),core_sha256=sha(core.read_bytes()),region='pal' if pal else 'auto',cases=results,source_rom_unmodified=True,read_only_instruction_cycle_hook=True,native_portals_implemented=False,origin_persistent_class_flag_seeded=4,source_room_preparation_sha256=sha((ROOT/'analysis/portal_prepared_rooms.json').read_bytes()),limits=['Controlled solved-room flag, source-prepared map and frozen actor after real dungeon entry; controller input from a traversable adjacent position triggers the portal. Full natural routes and fights are not established.','Reported final hero position may include movement while input remains held after transition. Phase 5D41 is the source arrival-position marker.'])
    name=f'portal_profile-{chosen:03x}{suffix}.json' if chosen is not None else f'portal_profile{suffix}.json'
    (ROOT/'analysis'/name).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
