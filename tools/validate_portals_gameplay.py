"""Live controller portal crossings in unmodified SMS and native MD ROMs."""
import contextlib,hashlib,io,json,re,sys
from validate_key_door_gameplay import ROOT,initial_room,rle_planes,maps,PRESSES,run

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    pal='--pal' in sys.argv;suffix='-pal' if pal else '';rom=(ROOT/'input/original.sms').read_bytes()
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    profile=json.loads((ROOT/f'analysis/portal-source-v0051/portal_profile{suffix}.json').read_bytes())
    prepared=json.loads((ROOT/'analysis/portal-source-v0051/portal_prepared_rooms.json').read_bytes());assert prepared['source_sha256']==sha(rom)
    _,ext,_,_,arrays,_=initial_room(rom)
    def cells(room):
        out=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,out,0,1);return out
    door=next(d for d in json.loads((ROOT/'analysis/doors_reference.json').read_bytes())['direct_unconditional_dungeon_doors'] if d['room']==16)
    outside=cells(16);osms,omd=maps(outside,ext);results=[]
    chosen=next((int(a.split('=',1)[1],16) for a in sys.argv if a.startswith('--room=')),None)
    for reference in profile['cases']:
        room=reference['room'];destination=reference['destination']
        if chosen is not None and room!=chosen:continue
        x,y=reference['initial_hero'];direction=reference['approach_direction'];coordinate=(((y-12)&248)*8+(((x-12)>>2)&62)+126)
        room_cells=bytes.fromhex(prepared['rooms'][str(room)]['cells']);sms=bytes.fromhex(prepared['rooms'][str(room)]['map']);md=bytearray()
        for n in range(0,1280,2):
            w=int.from_bytes(sms[n:n+2],'little');v=((w>>11)&1)<<13|((w>>12)&1)<<15|((w>>10)&1)<<12|((w>>9)&1)<<11|16+(w&511);md.extend(v.to_bytes(2,'big'))
        flags=bytearray(256);flags[room&255]=prepared['rooms'][str(room)]['flag'];actors=bytearray(768);actors[0]=1;actors[6]=255
        traces={}
        for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
            if tag=='sms':
                writes=[(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,outside),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),
                (3400,0xb9,room.to_bytes(2,'little')),(3400,0xa4,rom[0xb762+room*2:0xb764+room*2]),(3400,0x100,bytes(flags)),(3400,0x1c00,room_cells),(3400,0x1600,sms),(3400,0x330,bytes(48)),(3400,0x4b0,bytes(336)),(3400,0x600,actors),(3400,0xa2,b'\x01'),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(3400,0x304,b'\0'),(3400,0x314,bytes(4)),(3400,0x30a,bytes([direction])),(3400,0x64,bytes([direction])),(3400,0x62,coordinate.to_bytes(2,'little')),(3400,0xa8,b'\0'),(3400,0xa9,b'\0')]
            else:
                def w(f,k,v):return f,sy[k],v.to_bytes(2,'big')
                writes=[w(3120,'room_id',16),w(3120,'world_graphics_class',0),(3120,sy['scratch']+0x800,outside),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768)),w(3120,'hero_y',(door['y']+8)<<8),w(3120,'hero_x',door['x']<<8),
                w(3400,'room_id',room),(3400,sy['game_save_state']+0x50,bytes(flags)),(3400,sy['scratch']+0x800,room_cells),(3400,sy['sms_vram']+0x3800,sms),(3400,sy['world_new_md'],md),(3400,sy['md_map'],md),(3400,sy['world_spell_state'],bytes(48)),(3400,sy['world_loot_state'],bytes(336)),(3400,sy['world_actor_state'],actors),w(3400,'world_actor_count',1),w(3400,'hero_x',x<<8),w(3400,'hero_y',y<<8),w(3400,'hero_direction',direction),w(3400,'hero_counter',0),w(3400,'hero_dx',0),w(3400,'hero_dy',0),w(3400,'room_shutter_state',0),w(3400,'room_shutter_direction',0),w(3400,'room_script_coordinate_pending',1)]
            samples={};wipe_frames={}
            def observe(frame,raw):
                if frame<3400:return
                if tag=='sms':
                    word=lambda a:int.from_bytes(raw[a:a+2],'little')
                    state=dict(room=word(0xb9),state=raw[0x1d],x=word(0x312),y=word(0x310),direction=raw[0x30a],count=raw[0xa2],flags=bytes(raw[0x100:0x200]),masks=bytes(raw[0x200:0x300]),cells=bytes(raw[0x1c00:0x1ca0]),map=bytes(raw[0x1600:0x1b00]),loot=bytes(raw[0x4b0:0x600]))
                else:
                    def data(k,n,off=0):return bytes(raw[(sy[k]+off+i)^1] for i in range(n))
                    val=lambda k:int.from_bytes(data(k,2),'big')
                    state=dict(room=val('room_id'),state=val('game_state'),x=val('hero_x'),y=val('hero_y'),direction=val('hero_direction'),count=val('world_actor_count'),flags=data('game_save_state',256,0x50),masks=data('game_save_state',256,0x150),cells=data('scratch',160,0x800),map=data('sms_vram',1280,0x3800),loot=data('world_loot_state',336))
                samples[frame]=state
            def observe_vram(frame,data):
                if 3410<=frame<=3450:
                    if tag=='sms':words=[int.from_bytes(data[i:i+2],'little') for i in range(0x3800,0x3e00,2)];blank=0x18ff
                    else:words=[int.from_bytes(data[0xe000+(y+2)*128+x*2:0xe002+(y+2)*128+x*2],'little') for y in range(24) for x in range(32)];blank=0xa10f
                    wipe_frames[frame]=[n for n,w in enumerate(words) if w==blank]
            folder=ROOT/f'validation/portal-{tag}-{room:03x}{suffix}'
            with contextlib.redirect_stdout(io.StringIO()):run(path,3550,folder,{3390,3410,3420,3430,3440,3480,3550},([(200,220,0)] if tag=='sms' else [])+PRESSES+[(3125,3129,4),(3410,3415,[4,5,6,7][direction])],ram_writes=writes,ram_observer=observe,vram_observer=observe_vram,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
            changed=next((f for f,v in samples.items() if v['room']==destination),None);assert changed,(tag,hex(room),'portal not triggered')
            loading=next((f for f,v in samples.items() if f>=changed and v['room']==destination and v['state']==8),None);assert loading,(tag,hex(room),'loading state not observed')
            resume=next((f for f,v in samples.items() if f>loading and v['room']==destination and v['state']==12),None);assert resume,(tag,hex(room),'not resumed')
            traces[tag]=dict(changed=changed,loading=loading,resume=resume,loaded=samples[resume],wipe_frames=wipe_frames)
        for field in ['room','x','y','direction','count','flags','masks','cells','map','loot']:
            assert traces['sms']['loaded'][field]==traces['md']['loaded'][field],(hex(room),field,traces['sms']['loaded'][field] if field not in ['cells','map','loot','flags','masks'] else 'bytes differ',traces['md']['loaded'][field] if field not in ['cells','map','loot','flags','masks'] else 'bytes differ')
        wipe_differences=[f for f in traces['sms']['wipe_frames'] if traces['sms']['wipe_frames'][f]!=traces['md']['wipe_frames'][f]]
        first_wipe=next(f for f,v in traces['sms']['wipe_frames'].items() if 0<len(v)<768)
        active=list(range(first_wipe,first_wipe+19))
        assert all(0<len(traces['sms']['wipe_frames'][f])<768 for f in active),(hex(room),'wipe steps',active)
        assert all(traces['sms']['wipe_frames'][f]==traces['md']['wipe_frames'][f] for f in active),(hex(room),'visible wipe differs')
        full=active[-1]+1;assert len(traces['sms']['wipe_frames'][full])==len(traces['md']['wipe_frames'][full])==768
        assert all(v['room']==room for f,v in samples.items() if 3400<=f<3410),(hex(room),'stationary portal fired')
        results.append(dict(visible_wipe_frames_exact=20,stationary_negative_guard_verified=True,wipe_differing_frames=wipe_differences,wipe_blank_word_counts={tag:{f:len(v) for f,v in t['wipe_frames'].items()} for tag,t in traces.items()},room=room,destination=destination,loaded_state_cells_maps_flags_masks_loot_exact=True,timing={tag:dict(changed=t['changed'],loading=t['loading'],resume=t['resume']) for tag,t in traces.items()},resume_delta=traces['md']['resume']-traces['sms']['resume']))
        print(hex(room),'->',hex(destination),'loaded state matches; resume delta',results[-1]['resume_delta'],flush=True)
    assert results
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),region='pal' if pal else 'auto',cases=results,full_game_ported=False,limits=['Solved-origin flag and frozen actor seeded after a real dungeon entrance; controller movement then triggers the original/native portal.','Loaded state is compared at each system first gameplay-ready frame; timing differences are reported separately.','Full natural progression, all enemy AI, complete pixels and audio waveforms remain unverified.'])
    name=f'portals_gameplay-{chosen:03x}{suffix}_report.json' if chosen is not None else f'portals_gameplay{suffix}_report.json'
    (ROOT/'validation'/name).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
