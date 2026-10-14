"""Live final-particle -> room-script opening, controlled real dungeon rooms."""
import contextlib,hashlib,io,json,re,sys
from validate_key_door_gameplay import ROOT,initial_room,rle_planes,maps,PRESSES

def main():
    cross=False;end_frame=4000
    pal='--pal' in sys.argv;suffix='-pal' if pal else ''
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    original=ROOT/'input/original.sms';cartridge=ROOT/'gaw-megadrive.bin';rom=original.read_bytes()
    _,ext,_,_,arrays,_=initial_room(rom);patterns=bytearray(16384);meta=bytearray(2048)
    end,_=rle_planes(arrays['world_dungeon_background_rle'],0,patterns,0,4);rle_planes(arrays['world_dungeon_background_rle'],end,meta,0,2)
    def cells(room):
        result=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,result,0,1);return bytes(result)
    door=next(d for d in json.loads((ROOT/'analysis/doors_reference.json').read_bytes())['direct_unconditional_dungeon_doors'] if d['room']==16)
    outside=cells(16);osms,omd=maps(outside,ext);results=[]
    from run_core import run
    cases=[(room,keys,False,True) for room in [0x113,0x131,0x1b5] for keys in [2,98,99,255]]
    cases += [(room,2,True,True) for room in [0x113,0x131,0x1b5]]+[(0x113,2,False,False)]
    for room,initial_keys,already,pickup in cases:
        count=1;particle=True;expected=0;x=128;y=96 if room==0x131 and pickup else 128;reward_flag=8 if room==0x131 else 4
        has_key=room in (0x113,0x131) and not already
        expected_keys=min(initial_keys+1,99) if has_key and pickup and initial_keys<99 else initial_keys
        room_cells=cells(room);sms,md=maps(room_cells,meta);flags=bytearray(256);flags[room&255]=16|(reward_flag if already else 0)
        actors=bytearray(768)
        if particle:
            actors[0]=1;actors[1]=2;actors[3]=1;actors[7]=0x66;actors[8:10]=b'\xcc\x90';actors[11]=3;actors[12]=5;actors[13]=4;actors[0x11]=96;actors[0x13]=128
        traces={}
        for tag,path in [('sms',original),('md',cartridge)]:
            if tag=='sms':
                writes=[(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,outside),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),(3400,0xb9,room.to_bytes(2,'little')),(3400,0xa4,rom[0xb762+room*2:0xb764+room*2]),(3400,0x100,bytes(flags)),(3400,0x1c00,room_cells),(3400,0x1600,sms),(3400,0x330,bytes(48)),(3400,0x4b0,bytes(336)),(3400,0x1ce0,b'\xb0\xc0'*3),(3400,0x600,actors),(3400,0xaa,bytes(2)),(3400,0xa2,bytes([count])),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(3400,0x304,b'\0'),(3400,0x314,bytes(4)),(3400,0xde,bytes([initial_keys]))]
            else:
                def w(f,k,v):return f,sy[k],v.to_bytes(2,'big')
                writes=[w(3120,'room_id',16),w(3120,'world_graphics_class',0),(3120,sy['scratch']+0x800,outside),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768)),w(3120,'hero_y',(door['y']+8)<<8),w(3120,'hero_x',door['x']<<8),w(3400,'room_id',room),(3400,sy['game_save_state']+0x50,bytes(flags)),(3400,sy['scratch']+0x800,room_cells),(3400,sy['sms_vram']+0x3800,sms),(3400,sy['world_new_md'],md),(3400,sy['md_map'],md),(3400,sy['world_spell_state'],bytes(48)),(3400,sy['world_loot_state'],bytes(336)),(3400,sy['world_actor_state'],actors),(3400,sy['dungeon_animation_scan'],bytes(1)),(3400,sy['dungeon_animation_phase'],bytes(1)),w(3400,'world_actor_count',count),w(3400,'hero_x',x<<8),w(3400,'hero_y',y<<8),w(3400,'hero_counter',0),w(3400,'hero_dx',0),w(3400,'hero_dy',0),w(3400,'hero_keys',initial_keys)]
            if cross:
                writes.append((3400,0x305,b'\xff') if tag=='sms' else w(3400,'hero_hurt',255))
            samples={}
            def observe(frame,raw):
                if frame<3390:return
                if tag=='sms':
                    state=dict(room=int.from_bytes(raw[0xb9:0xbb],'little'),state=raw[0x1d],x=int.from_bytes(raw[0x312:0x314],'little'),y=int.from_bytes(raw[0x310:0x312],'little'),loot=bytes(raw[0x4b0:0x600]),count=raw[0xa2],actor=raw[0x600],keys=raw[0xde],flags=bytes(raw[0x100:0x200]),cells=bytes(raw[0x1c00:0x1ca0]),map=bytes(raw[0x1600:0x1b00]))
                else:
                    def data(k,n,off=0):
                        a=sy[k]+off;return bytes(raw[(a+i)^1] for i in range(n))
                    val=lambda k:int.from_bytes(data(k,2),'big')
                    state=dict(room=val('room_id'),state=val('game_state'),x=val('hero_x'),y=val('hero_y'),loot=data('world_loot_state',336),count=val('world_actor_count'),actor=data('world_actor_state',1)[0],keys=val('hero_keys'),flags=data('game_save_state',256,0x50),cells=data('scratch',160,0x800),map=data('sms_vram',1280,0x3800))
                samples[frame]=state
            folder=ROOT/f'validation/{tag}-clear-gameplay-{room:03x}-{initial_keys}-{already}-{pickup}-rewards{suffix}'
            with contextlib.redirect_stdout(io.StringIO()):run(path,end_frame,folder,{3390,3400,3420,end_frame}, ([(200,220,0)] if tag=='sms' else [])+PRESSES+[(3125,3129,4)]+([(3440,3460,4)] if pickup else []),ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
            assert samples[3390]['room']==0x1f0,(tag,'entry')
            settled=samples[end_frame]
            assert settled['room']==room and settled['keys']==expected_keys,(tag,'room or key')
            assert settled['flags'][room&255]&reward_flag,(tag,hex(room),settled['flags'][room&255],expected)
            assert settled['count']==0x80,(tag,'counter')
            assert settled['actor']==0,(tag,'particle not ended')
            opening=next((f for f,s in samples.items() if f>=3400 and s['flags'][room&255]&0xe0),None)
            gone=next((f for f,s in samples.items() if f>=3400 and not s['actor']),None)
            if expected:assert opening>=gone,(tag,'opened before death ended')
            traces[tag]=dict(settled=settled,opening=opening,particle_gone=gone)
            if cross:
                reached=next((f for f,s in samples.items() if f>3400 and s['room']==target and s['state']==12),None)
                returned=next((f for f,s in samples.items() if f>=3550 and reached and s['room']==room and s['state']==12),None)
                assert reached and returned,(tag,hex(room),'cross/return',reached,returned)
                traces[tag].update(reached=reached,returned=returned)
                traces[tag]['cross_states']=[samples[reached],samples[returned]]
        for field in (['room','count','actor','keys','flags'] if cross else ['room','count','actor','keys','flags','cells','map','loot']):assert traces['sms']['settled'][field]==traces['md']['settled'][field],(hex(room),field)
        if cross:
            for a,b in zip(traces['sms']['cross_states'],traces['md']['cross_states']):
                for field in ['room','state','x','y','keys','flags','cells','map']:assert a[field]==b[field],(hex(room),'cross/return',field)
        loot_types=[traces['md']['settled']['loot'][n*48] for n in range(7)]
        assert loot_types.count(14)==int(has_key and not pickup),(hex(room),'key lifetime',loot_types)
        results.append(dict(room=room,initial_keys=initial_keys,already_rewarded=already,pickup=pickup,expected_keys=expected_keys,settled_cells_maps_flags_loot_counter_keys_exact=True,key_persists_past_normal_loot_expiry=has_key and not pickup))
        print(hex(room),initial_keys,already,pickup,'reward/key collection matches',flush=True)
    report=dict(md_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),region='pal' if pal else 'auto',cases=results,production_cartridges_unmodified=True,final_particle_runs_in_live_game_loop=True,controlled_particle_type_66_excludes_random_drops=True,limits=['Room, hero, actor animation, counter and animation phase initialized by RAM fixture; complete natural fights/routes are not verified.', 'Controlled final particle type 66 has zero drop probabilities, excluding provisional RNG differences.', 'Room 113 uses controller UP to collect; room 131 starts the hero at the reward centre because a direct path from Y128 is obstructed.', 'One idle case observes the key for 596 frames; key cap and already-rewarded guards are checked.', 'Absolute redraw latency, full transition pixels and audio waveforms remain unverified.'])
    (ROOT/f'validation/clear_rewards_gameplay{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
