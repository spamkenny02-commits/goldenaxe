"""Input-driven screen spell probe; compare map states and final game state."""
import argparse,contextlib,ctypes as c,io,json
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha
from extract_world import initial_room
from extract_title import rle_planes
def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--post-menu',action='store_true');p.add_argument('--timing',action='store_true');p.add_argument('--level',type=int,choices=[1,2],default=1);p.add_argument('--pal',action='store_true');p.add_argument('--diagnostic',action='store_true');p.add_argument('--graphics',type=int,choices=[0,1,2],default=0);p.add_argument('--actors',action='store_true');p.add_argument('--magic',type=int,default=64);a=p.parse_args()
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');rom=(ROOT/'input/original.sms').read_bytes();room=0 if a.graphics==1 else 0x1e4 if a.graphics==2 else 0x95
    cells=None
    if a.graphics:
        bank=8+((room*2)>>8);ptr=bank*0x4000+((room*2)&255);offset=bank*0x4000+(int.from_bytes(rom[ptr:ptr+2],'little')&0x3fff);cells=bytearray(160);rle_planes(rom,offset,cells,0,1)
    rows={};maps={};final={};latches={};clock=0;aligned_frame=None
    actors=bytearray(768)
    if a.actors:
        for slot,defense,flags in [(0,0,3),(1,20,3),(2,1,1),(8,0,3)]:
            e=memoryview(actors)[slot*48:(slot+1)*48];e[0]=0x26;e[3]=flags;e[6]=255;e[8:10]=b'\xcc\x90';e[12]=5;e[13]=4;e[0x11]=120;e[0x13]=200;e[0x18]=100;e[0x1a]=defense;e[0x1b]=10
    for tag in ['sms','md']:
        source=tag=='sms';out=ROOT/f'validation/screen-spell-{a.tag}-{tag}';assert not out.exists();states=[];changes=[];display=[];last=None;last_display=None;seen_active=False;damage_latch=None
        if source:
            writes=[(2810,0x40,bytes([a.graphics])),(2810,0x66,bytes([15-a.graphics])),(2810,0xdf,b'\6'),(2810,0xe6,bytes([a.level])),(2810,0xdb,bytes([a.magic,72])),(2810,0x318,b'\x11'),(2810,0x600,bytes(768)),(2810,0x330,bytes(384)),(2990,0x600,bytes(actors))]
        else:
            w=lambda n,v:(2810,sy[n],v.to_bytes(2,'big'))
            writes=[w('world_graphics_class',a.graphics),w('hero_selected_item',6),w('hero_magic',a.magic),w('hero_max_magic',72),w('hero_health',17),(2810,sy['hero_items']+6,bytes([a.level])),(2810,sy['world_actor_state'],bytes(768)),(2810,sy['world_spell_state'],bytes(48)),(2810,sy['world_loot_state'],bytes(336)),(2990,sy['world_actor_state'],bytes(actors)),(2980,sy['vtimer'],clock.to_bytes(4,'big')),(2980,sy['world_clock_shift'],bytes(4))]
        if cells is not None:
            if source:writes += [(2810,0xb9,room.to_bytes(2,'little')),(2810,0x1c00,bytes(cells)),(2810,0xa4,rom[0xb762+room*2:0xb764+room*2])]
            else:writes += [w('room_id',room),(2810,sy['scratch']+0x800,bytes(cells))]
        timing=None;events=[];previous=0
        if a.timing and source:
            core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_screen_spell_libretro.dll';timing=c.CDLL(str(core));timing.gaw_timing_events.restype=c.POINTER(c.c_uint64);timing.gaw_timing_count.restype=c.c_uint
        def observe(f,r):
            nonlocal clock,last,seen_active,damage_latch,previous,aligned_frame
            if timing is not None:
                if f==2998:timing.gaw_timing_reset();previous=0
                if f>=2999:
                    count=timing.gaw_timing_count();ptr=timing.gaw_timing_events();assert previous<=count<32768
                    for n in range(previous,count):events.append([f]+[int(ptr[n*8+j]) for j in range(8)])
                    previous=count
            if source and f==2979:clock=r[0x2f]
            if f<2999:return
            data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k));word=lambda n:int.from_bytes(data(n,2),'big')
            level=r[0x90] if source else word('screen_spell_level');active=bool(level) if source else word('screen_spell_active')
            row=dict(frame=f,level=level,active=active,health=r[0x318] if source else word('hero_health'),magic=r[0xdb] if source else word('hero_magic'),selected=r[0xdf] if source else word('hero_selected_item'),owned=r[0xe6] if source else data('hero_items',17)[6],clock=r[0x2f] if source else word('screen_spell_clock') if active else (int.from_bytes(data('vtimer',4),'big')-int.from_bytes(data('world_clock_shift',4),'big'))&255,iteration=0 if source else word('screen_spell_iteration'),pacing_error=0 if source else word('screen_spell_pacing_error'),gap=0 if source else word('screen_spell_model_gap'),late=0 if source else word('screen_spell_late_publications'),hero=r[0x301] if source else word('hero_state'))
            states.append(row)
            if not a.post_menu and not source and 3300<=f<3450 and aligned_frame is None and ((row['clock']+1)&255)==final['sms']['clock']:
                aligned_frame=f+1;captures.add(f+1)
            if level:seen_active=True
            if seen_active and not level and damage_latch is None:damage_latch=(bytes(r[0x600:0x900]) if source else data('world_actor_state',768)).hex()
            buf=bytes(r[0x1600:0x1b00]) if source else data('sms_vram',0x3d00)[0x3800:]
            if buf!=last:
                changes.append(dict(frame=f,active=active,map=buf.hex(),work=(bytes(r[0x1200:0x14c0]) if source else data('house_dialogue_storage',704)).hex()));last=buf
            if f==(3700 if a.post_menu else 3400):final[tag]=row
        def vram(f,v):
            nonlocal last_display
            if f<2999:return
            if source:buf=bytes(v[0x3800:0x3d00])
            else:
                buf=bytearray()
                for row in range(20):
                    for col in range(32):
                        addr=0xe000+(row+2)*128+col*2;w=int.from_bytes(v[addr:addr+2],'little')
                        word=((w&2047)-16)&511;word|=((w>>13)&1)<<11|((w>>15)&1)<<12|((w>>12)&1)<<10|((w>>11)&1)<<9
                        buf.extend(word.to_bytes(2,'little'))
                buf=bytes(buf)
            if buf!=last_display:
                sat=[]
                if source:
                    for i in range(64):
                        if v[0x3f00+i]==208:break
                        sat.append([v[0x3f80+i*2],v[0x3f00+i],v[0x3f81+i*2]])
                else:
                    index=0;seen=set()
                    while index not in seen:
                        seen.add(index);base=0xf400+index*8;word=lambda off:int.from_bytes(v[base+off:base+off+2],'little');tile=word(4)&2047
                        sat.append([((word(6)&511)-128)&255,((word(0)&511)-145)&255,(tile-272)&255 if tile<1024 else None]);index=word(2)&127
                        if not index:break
                display.append(dict(frame=f,active=states[-1]['active'],clock=states[-1]['clock'],map=buf.hex(),sprites=sat));last_display=buf
        captures={2999,3005,3020,3040,3060,3080,3100,3150,3400}
        presses=([(200,220,0)] if source else [])+PRESSES[:8]+[(3000,3001,8)]
        if a.post_menu:presses += [(3460,3463,0),(3560,3563,0)];captures.update([3490,3650,3700])
        with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),3700 if a.post_menu else 3450,out,captures,presses,core=core if timing is not None else None,ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
        for name,value in [('states',states),('maps',changes),('display',display)]:(out/(name+'.json')).write_bytes((json.dumps(value,indent=2)+'\n').encode())
        if timing is not None:
            (out/'cycle-events.json').write_bytes((json.dumps(events,indent=2)+'\n').encode());timing.gaw_screen_scene_size.restype=c.c_uint;timing.gaw_screen_scene_data.restype=c.POINTER(c.c_ubyte);size=timing.gaw_screen_scene_size();assert size<256;(out/'scenes.bin').write_bytes(c.string_at(timing.gaw_screen_scene_data(),size*8192))
        rows[tag]=states;maps[tag]=display;latches[tag]=damage_latch
    native={x['map'] for x in maps['md'] if x['active']==2};original={x['map'] for x in maps['sms'] if x['active']};common=native&original
    sequence={tag:[x['map'] for x in maps[tag] if x['active']==(True if tag=='sms' else 2)] for tag in ['sms','md']}
    sequence_equal=sequence['sms']==sequence['md']
    sprite_rows={tag:[x['sprites'] for x in maps[tag] if x['active']==(True if tag=='sms' else 2)] for tag in ['sms','md']}
    sprite_positions_equal=[[row[:2] for row in frame] for frame in sprite_rows['sms']]==[[row[:2] for row in frame] for frame in sprite_rows['md']]
    sprite_tiles_equal=sprite_rows['sms']==sprite_rows['md']
    fields=all(final['sms'][k]==final['md'][k] for k in ['health','magic','selected','owned','hero','level'])
    assert final['sms']['magic']==(a.magic-32 if a.magic>=32 else a.magic) and final['sms']['selected']==(0 if a.magic>=32 else 6)
    actor_equal=not a.actors or latches['sms']==latches['md']
    loop_rows=[r for r in rows['md'] if r['active']==2]
    loop_clock_equal=all(r['clock']==((rows['sms'][0]['clock']+2+r['iteration'])&255) for r in loop_rows)
    result=dict(display_sprite_positions_equal=sprite_positions_equal,display_sprite_tiles_equal=sprite_tiles_equal,post_menu=a.post_menu,loop_clock_matches_source_iteration=loop_clock_equal,loop_clock_rows=len(loop_rows),aligned_native_return_frame=aligned_frame,md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=fields and native<=original and actor_equal and sequence_equal and loop_clock_equal and not final['md']['pacing_error'],ordered_display_sequence_equal=sequence_equal,display_sequence_lengths={k:len(v) for k,v in sequence.items()},graphics=a.graphics,actors=a.actors,magic=a.magic,damage_latch_actor_bytes_equal=actor_equal,level=a.level,region='pal' if a.pal else 'auto',source_map_states=len(original),native_map_states=len(native),common_map_states=len(common),native_unmatched_map_states=len(native-original),final_fields_equal=fields,active_frames={tag:[r['frame'] for r in rows[tag] if r['active']] for tag in ['sms','md']},final=final,full_game_verified=False)
    (ROOT/f'analysis/screen_spell_{a.tag}_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print({k:v for k,v in result.items() if k not in ['active_frames','final']});assert result['passed'] or a.diagnostic
if __name__=='__main__':main()
