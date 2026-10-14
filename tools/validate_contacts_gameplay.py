"""Live final-particle -> room-script opening, controlled real dungeon rooms."""
import contextlib,hashlib,io,json,re,sys
from validate_key_door_gameplay import ROOT,initial_room,rle_planes,maps,PRESSES

def main():
    cross=False;end_frame=3600
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
    contact_records={r['room']:r for r in json.loads((ROOT/'analysis/contact_script_reference.json').read_bytes())['records'] if r['target']!=0x5cfb}
    cases=[(room,already) for room in contact_records for already in [False,True]]
    for room,already in cases:
        record=contact_records[room];kind=record['kind'];empty=kind=='empty_cell_passages';marker=kind=='stationary_up_cell'
        target=record.get('coordinate',0x168 if marker else 0)
        if empty:x,y=128,112
        else:
            positions=[(x,y) for y in range(32,161,8) for x in range(32,225,8) if (((y-12)&248)*8+(((x-12)>>2)&62)+126)==target]
            assert len(positions)==1,(room,positions);x,y=positions[0]
        coordinate=(((y-12)&248)*8+(((x-12)>>2)&62)+126)
        direction=0;button=4;occupied=True;count=1;initial_keys=expected_keys=2
        cell=record['explicit_registers']['c'] if empty else 0x1b if marker else None
        room_cells=bytearray(cells(room));flags=bytearray(256);flags[room&255]=16|(4 if already and not marker else 0)
        if empty:room_cells[cell]=0x4d
        if marker:room_cells[cell]=0x4d if already else 0x10
        room_cells=bytes(room_cells);sms,md=maps(room_cells,meta)
        actors=bytearray(768)
        if occupied:actors[0]=1;actors[6]=255
        dying=bytearray(768);dying[0]=1;dying[1]=2;dying[3]=1;dying[7]=0x66;dying[8:10]=b'\xcc\x90';dying[11]=3;dying[12]=5;dying[13]=4;dying[0x11]=96;dying[0x13]=128
        traces={}
        for tag,path in [('sms',original),('md',cartridge)]:
            if tag=='sms':
                writes=[(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,outside),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),(3400,0xb9,room.to_bytes(2,'little')),(3400,0xa4,rom[0xb762+room*2:0xb764+room*2]),(3400,0x100,bytes(flags)),(3400,0x1c00,room_cells),(3400,0x1600,sms),(3400,0x330,bytes(48)),(3400,0x4b0,bytes(336)),(3400,0x1ce0,b'\xb0\xc0'*3),(3400,0x600,actors),(3400,0xaa,bytes(2)),(3400,0xa2,bytes([count])),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(3400,0x304,b'\0'),(3400,0x314,bytes(4)),(3400,0xde,bytes([initial_keys]))]
            else:
                def w(f,k,v):return f,sy[k],v.to_bytes(2,'big')
                writes=[w(3120,'room_id',16),w(3120,'world_graphics_class',0),(3120,sy['scratch']+0x800,outside),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768)),w(3120,'hero_y',(door['y']+8)<<8),w(3120,'hero_x',door['x']<<8),w(3400,'room_id',room),(3400,sy['game_save_state']+0x50,bytes(flags)),(3400,sy['scratch']+0x800,room_cells),(3400,sy['sms_vram']+0x3800,sms),(3400,sy['world_new_md'],md),(3400,sy['md_map'],md),(3400,sy['world_spell_state'],bytes(48)),(3400,sy['world_loot_state'],bytes(336)),(3400,sy['world_actor_state'],actors),(3400,sy['dungeon_animation_scan'],bytes(1)),(3400,sy['dungeon_animation_phase'],bytes(1)),w(3400,'world_actor_count',count),w(3400,'hero_x',x<<8),w(3400,'hero_y',y<<8),w(3400,'hero_counter',0),w(3400,'hero_dx',0),w(3400,'hero_dy',0),w(3400,'hero_keys',initial_keys)]
            writes.extend([(3400,0xa8,b'\0'),(3400,0xa9,b'\0'),(3400,0x30a,b'\0'),(3400,0x64,b'\0'),(3400,0x62,coordinate.to_bytes(2,'little'))] if tag=='sms' else [w(3400,'room_shutter_state',0),w(3400,'room_shutter_direction',0),w(3400,'hero_direction',0),w(3400,'room_script_coordinate_pending',1)])
            if empty:
                changed=bytearray(room_cells);changed[cell]=0;csms,cmd=maps(changed,meta)
                writes.extend([(3410,0x1c00,bytes(changed)),(3410,0x1600,csms)] if tag=='sms' else [(3410,sy['scratch']+0x800,bytes(changed)),(3410,sy['sms_vram']+0x3800,csms),(3410,sy['world_new_md'],cmd),(3410,sy['md_map'],cmd)])
            samples={}
            def observe(frame,raw):
                if frame<3390:return
                if tag=='sms':
                    state=dict(room=int.from_bytes(raw[0xb9:0xbb],'little'),state=raw[0x1d],x=int.from_bytes(raw[0x312:0x314],'little'),y=int.from_bytes(raw[0x310:0x312],'little'),shutter=raw[0xa8],direction=raw[0xa9],loot=bytes(raw[0x4b0:0x600]),count=raw[0xa2],actor=raw[0x600],keys=raw[0xde],flags=bytes(raw[0x100:0x200]),cells=bytes(raw[0x1c00:0x1ca0]),map=bytes(raw[0x1600:0x1b00]))
                else:
                    def data(k,n,off=0):
                        a=sy[k]+off;return bytes(raw[(a+i)^1] for i in range(n))
                    val=lambda k:int.from_bytes(data(k,2),'big')
                    state=dict(room=val('room_id'),state=val('game_state'),x=val('hero_x'),y=val('hero_y'),shutter=val('room_shutter_state'),direction=val('room_shutter_direction'),loot=data('world_loot_state',336),count=val('world_actor_count'),actor=data('world_actor_state',1)[0],keys=val('hero_keys'),flags=data('game_save_state',256,0x50),cells=data('scratch',160,0x800),map=data('sms_vram',1280,0x3800))
                samples[frame]=state
            folder=ROOT/f'validation/{tag}-clear-gameplay-{room:03x}-{already}-contacts{suffix}'
            with contextlib.redirect_stdout(io.StringIO()):run(path,end_frame,folder,{3390,3400,3410,3490,end_frame}, ([(200,220,0)] if tag=='sms' else [])+PRESSES+[(3125,3129,4)]+([] if empty else [(3410,3440,button)]),ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
            assert samples[3390]['room']==0x1f0,(tag,'entry')
            settled=samples[end_frame]
            assert settled['room']==room and settled['keys']==expected_keys,(tag,'room or key')
            assert settled['count']==1 and settled['keys']==2,(tag,'counter/keys')
            assert settled['cells'][0x1b]==0x4d if marker else settled['flags'][room&255]&4,(tag,'contact did not trigger',hex(room),kind,settled['x'],settled['y'])
            effect=lambda v:v['cells'][0x1b]==0x4d if marker else bool(v['flags'][room&255]&4)
            fired=next((f for f,v in samples.items() if f>=3400 and effect(v)),None)
            traces[tag]=dict(settled=settled,fired=fired)
        for field in ['room','count','actor','keys','flags','cells','map','loot','shutter','direction']:
            assert traces['sms']['settled'][field]==traces['md']['settled'][field],(hex(room),already,field)
        assert traces['sms']['fired']==traces['md']['fired'],(hex(room),already,'trigger timing',traces['sms']['fired'],traces['md']['fired'])
        fired=traces['sms']['fired']
        if marker and not already:assert 3410<=fired<=3420,(hex(room),'marker redraw did not complete',fired)
        else:assert fired==(3400 if already else 3410),(hex(room),already,'unexpected trigger',fired)
        results.append(dict(room=room,kind=kind,already_triggered=already,settled_cells_maps_flags_loot_counter_keys_exact=True,trigger_frame=traces['sms']['fired'],trigger_timing_exact=True))
        print(hex(room),already,'live contact matches',flush=True)
    report=dict(md_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),region='pal' if pal else 'auto',cases=results,production_cartridges_unmodified=True,full_game_ported=False,limits=['Controlled room/hero/frozen actor setup after a real dungeon entry. Stationary triggers use controller UP; empty-cell triggers inject the cleared cell/map at frame 3410.','No natural full fight, block destruction or dungeon route is established.','Full pixels, audio waveform and redraw latency remain unverified.'])
    (ROOT/f'validation/contacts_gameplay{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
