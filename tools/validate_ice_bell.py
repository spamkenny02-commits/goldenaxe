"""Real bell input after a controlled room is rendered through inventory close."""
import argparse,contextlib,io,json
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from extract_world import initial_room
from extract_title import rle_planes
from validate_key_door_gameplay import maps
from audit_item_reward_visuals import md_pixels
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--pal',action='store_true');p.add_argument('--room',type=lambda x:int(x,0),default=0x3c);p.add_argument('--graphics',type=int,default=0);p.add_argument('--actors',action='store_true');p.add_argument('--inventory',action='store_true');p.add_argument('--overview',action='store_true');p.add_argument('--diagnostic',action='store_true');a=p.parse_args()
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');rom=(ROOT/'input/original.sms').read_bytes();_,meta,_,_,arrays,_=initial_room(rom);cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][a.room*2:a.room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);tilemap,_=maps(cells,meta)
    pc=0xbb62
    while rom[pc] and rom[pc]!=a.room:pc+=4
    metadata=rom[pc+1:pc+4] if rom[pc] else b'\xff\xff\0'
    x,y=(40,40) if a.room==0x3c else (136,112);clock=0;results={};records={};patterns={};latches={};finals={}
    actors=bytearray(768)
    if a.actors:
        for slot,kind,flags in [(0,0x26,1),(1,0x26,0),(8,0x30,1),(15,0x68,0x41)]:
            off=slot*48;actors[off]=kind;actors[off+3]=flags;actors[off+6]=255;actors[off+8:off+10]=b'\xcc\x90';actors[off+12]=5;actors[off+13]=4;actors[off+0x11]=120;actors[off+0x13]=200;actors[off+0x18]=10
    for tag in ['sms','md']:
        source=tag=='sms';out=ROOT/f'validation/ice-bell-{a.tag}-{tag}';assert not out.exists();rows=[];samples=[];latched=None;last=None
        if source:
            writes=[(2810,0xb9,a.room.to_bytes(2,'little')),(2810,0xa4,rom[0xb762+a.room*2:0xb764+a.room*2]),(2810,0x6e,metadata),(2810,0x40,bytes([a.graphics])),(2810,0x1600,tilemap),(2810,0x1c00,bytes(cells)),(2810,0xac,b'\0'),(2810,0xdf,b'\12'),(2810,0xea,b'\1'),(2810,0x318,b'\x11'),(2810,0xdb,bytes([11,24,37,2])),(2810,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(2810,0x304,b'\0'),(2810,0x314,bytes(4)),(2810,0x600,bytes(768)),(2990,0x600,bytes(actors))]
            if a.overview:writes.append((2810,0xeb,b'\1'))
        else:
            w=lambda n,v:(2810,sy[n],v.to_bytes(2,'big'))
            writes=[w('room_id',a.room),w('world_graphics_class',a.graphics),w('hero_selected_item',10),w('ice_bell_state',0),w('hero_health',17),w('hero_magic',11),w('hero_gold',37),w('hero_keys',2),w('hero_x',x<<8),w('hero_y',y<<8),w('hero_counter',0),w('hero_dx',0),w('hero_dy',0),(2810,sy['room_metadata'],metadata),(2810,sy['hero_items']+10,b'\1'),(2810,sy['sms_vram']+0x3800,tilemap),(2810,sy['scratch']+0x800,bytes(cells)),(2810,sy['world_actor_state'],bytes(768)),(2990,sy['world_actor_state'],bytes(actors)),(2980,sy['vtimer'],clock.to_bytes(4,'big')),(2980,sy['world_clock_shift'],bytes(4))]
            if a.overview:writes.append((2810,sy['hero_items']+11,b'\1'))
        def observe(f,r):
            nonlocal clock,latched
            if source and f==2979:clock=r[0x2f]
            if f<2999:return
            data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k));word=lambda n:int.from_bytes(data(n,2),'big')
            row=dict(frame=f,state=r[0xac] if source else word('ice_bell_state'),selected=r[0xdf] if source else word('hero_selected_item'),owned=r[0xea] if source else data('hero_items',17)[10],health=r[0x318] if source else word('hero_health'),magic=r[0xdb] if source else word('hero_magic'),gold=r[0xdd] if source else word('hero_gold'),keys=r[0xde] if source else word('hero_keys'),hero=r[0x301] if source else word('hero_state'),game=r[0x1d] if source else word('game_state'),terrain=r[0x41] if source else word('hero_terrain_context'),water_cells=(r[0x1c00:0x1ca0] if source else data('scratch',0x8a0)[0x800:]).count(0x3f))
            rows.append(row)
            if row['state'] and latched is None:latched=dict(frame=f,actors=(bytes(r[0x600:0x900]) if source else data('world_actor_state',768)).hex())
            if f==end:
                finals[tag]=dict(fields=row,cells=bytes(r[0x1c00:0x1ca0]).hex() if source else data('scratch',0x8a0)[0x800:].hex(),metatiles=(bytes(r[0xac0:0xac8])+bytes(r[0xaf0:0xaf8])).hex() if source else (data('scratch',0x1c8)[0x1c0:]+data('scratch',0x1f8)[0x1f0:]).hex(),flags=bytes(r[0x100:0x200]).hex() if source else data('game_save_state',0x150)[0x50:].hex(),audio_error=0 if source else word('sound_unhandled_command'))
        def vram(f,v):
            nonlocal last
            if f!=2999 and not 3000<=f<=3080:return
            if source:water=bytes(v[127*32:131*32]);ice=bytes(v[101*32:102*32])
            else:
                def planar(tile,count):
                    out=bytearray(count*32)
                    for t in range(count):
                        pix=md_pixels(v,tile+t)
                        for yy in range(8):
                            for xx in range(8):
                                for plane in range(4):out[t*32+yy*4+plane]|=((pix[yy*8+xx]>>plane)&1)<<(7-xx)
                    return bytes(out)
                water=planar(143,4);ice=planar(117,1)
            if f==2999 or water!=last:samples.append(dict(frame=f,water=water.hex(),ice=ice.hex()));last=water
        end=4500 if a.overview else 3700 if a.inventory else 3300
        presses=([(200,220,0)] if source else [])+PRESSES[:8]+([] if a.graphics else [(2810,2813,0),(2910,2913,0)])+[(3000,3001,8),(3200,3201,8)]
        if a.inventory:presses += [(3330,3333,0),(3400,3403,0),(3550,3551,8)]
        if a.overview:presses += [(3300,3303,0),(3330,3331,7),(3345,3346,8),(3370,3373,0),(3440,3441,8),(4300,4301,8)]
        with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),end,out,{2999,3003,3007,3011,3015,3025,3100,end},presses,ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
        for name,value in [('states',rows),('patterns',samples),('latch',latched)]: (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
        records[tag]=rows;patterns[tag]=samples;latches[tag]=latched
    stage_frames={};stage_pass=True
    if cells.count(0x3f) and not a.graphics:
        current=bytearray.fromhex(patterns['sms'][0]['water']);ice=bytes.fromhex(patterns['sms'][0]['ice']);expected=[bytes(current).hex()];mask=0x7f
        for step in range(8):
            for row in range(32):
                m=mask if not row&1 else ((mask>>4)|(mask<<4))&255
                for plane in range(4):
                    i=row*4+plane;current[i]=(current[i]&m)|(ice[i%32]&(~m&255))
            expected.append(bytes(current).hex());mask=((mask>>1)|(mask<<7))&255
        for tag in ['sms','md']:
            seen={x['water']:x['frame'] for x in reversed(patterns[tag])};stage_frames[tag]=[seen.get(value) for value in expected];stage_pass &= all(x is not None for x in stage_frames[tag])
    fields_equal=all(finals['sms']['fields'][k]==finals['md']['fields'][k] for k in ['state','selected','owned','health','magic','gold','keys','game','water_cells'])
    data_equal=all(finals['sms'][k]==finals['md'][k] for k in ['cells','metatiles','flags'])
    latch_equal=not a.actors or latches['sms']['actors']==latches['md']['actors']
    passed=stage_pass and fields_equal and data_equal and latch_equal and all(not x['audio_error'] for x in finals.values())
    result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),passed=passed,region='pal' if a.pal else 'auto',room=a.room,graphics=a.graphics,actors=a.actors,inventory=a.inventory,overview=a.overview,controlled_room_rendered_via_inventory=not bool(a.graphics),source_native_final_fields_equal=fields_equal,source_native_cells_metatiles_flags_equal=data_equal,source_native_latched_actors_equal=latch_equal,eight_mask_steps_seen=stage_pass,stage_first_frames=stage_frames,final=finals,full_game_verified=False)
    (ROOT/f'analysis/ice_bell_{a.tag}_report.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='final'});assert passed or a.diagnostic

if __name__=='__main__':main()
