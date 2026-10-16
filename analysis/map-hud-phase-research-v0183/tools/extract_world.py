"""ROM references for room 0095: Z80 16D0, 190B, 2279 and 1E4E.

No captured RAM/VRAM is used as input to resource extraction.
"""
import json
from pathlib import Path
from extract_title import rle_planes
ROOT=Path(__file__).resolve().parents[1]

def initial_room(rom,room=0x95):
    patterns=bytearray(0x4000)
    rle_planes(rom,0x13701,patterns,0x3040,4)
    rle_planes(rom,0x1274c,patterns,0x1e00,4)
    meta=bytearray(0x400)
    end,pattern_end=rle_planes(rom,0x3c010,patterns,0,4)
    meta_end,meta_length=rle_planes(rom,end,meta,0,2)
    # 1A30: unopened portal descriptors use metatile 13h.
    for target in (0x1c0,0x1f0): meta[target:target+8]=meta[0x98:0xa0]
    # 81C0: extra metatiles at CD00 carry collision flags.
    pos=0x81fc; extra=0x400
    extended=meta+bytearray(0x400)
    while rom[pos]<128:
        index=rom[pos];pos+=1
        extended[extra:extra+8]=meta[index*8:index*8+8];extra+=8
    pos+=1
    for offset in range(0x401,extra,2):
        extended[offset]=(extended[offset]&31)|rom[pos];pos+=1
    room_bank=8+((room*2)>>8)
    room_pointer=room_bank*0x4000+((room*2)&255)
    address=int.from_bytes(rom[room_pointer:room_pointer+2],'little')
    room_start=room_bank*0x4000+(address&0x3fff)
    cells=bytearray(160)
    room_end,length=rle_planes(rom,room_start,cells,0,1)
    assert length==160
    tilemap=bytearray(0x600)
    for y in range(20):
        for x in range(32):
            tile=cells[(y//2)*16+x//2]
            offset=tile*8+(y&1)*4+(x&1)*2
            tilemap[(y*32+x)*2:(y*32+x)*2+2]=extended[offset:offset+2]
    # 1E4E: direct two-plane HUD RLE, then add tile D0 and palette/priority.
    hud=bytearray(0x100)
    hud_end,_=rle_planes(rom,0x126ab,hud,0,2)
    for offset in range(0,256,2):
        hud[offset]=(hud[offset]+0xd0)&255;hud[offset+1]|=0x58
    # 7357: B counts bytes, C rows: two words on each of two rows.
    hud[0x58:0x5c]=rom[0x1e91:0x1e95]
    hud[0x98:0x9c]=rom[0x1e95:0x1e99]
    for offset in range(1,256,2): hud[offset]|=0x40
    # 1EEE, 1F25, 1F4B: initial 24/24 HP and magic, no money.
    for n in range(3): hud[0x5e+n*2:0x60+n*2]=bytes((0x8b,0x19))
    for n in range(3): hud[0xde+n*2:0xe0+n*2]=bytes((0x90,0x19))
    # 085B prints all three decimal digits. Destination is DBD0.
    for n in range(3): hud[0xd0+n*2:0xd2+n*2]=bytes((0xf0,0x18))
    tilemap[0x500:]=hud
    arrays={'world_background_rle':rom[0x3c010:meta_end],
            'world_room_rle':rom[room_start:room_end],
            'world_palette':rom[0x3c000:0x3c010],
            'world_hud_rle':rom[0x126ab:hud_end],
            'world_extra_meta':rom[0x81fc:pos]}
    for name,source,destination in [('world_hud_font_rle',0x13db0,0x1a00),
                                  ('world_hud_patterns_rle',0x122d2,0x3600)]:
        resource_end,_=rle_planes(rom,source,patterns,destination,4)
        arrays[name]=rom[source:resource_end]
    # 2B07 loads one four-tile item icon without compression.
    icon=rom[0x12881:0x12901]
    patterns[0x1d80:0x1e00]=icon
    # 1D0D: A=30h indexes a 16-color remapping table relative to 1DA2.
    remap=rom[0x1dd2:0x1de2]
    for offset in range(0x1d80,0x1e00,4):
        values=patterns[offset:offset+4];converted=[0]*4
        for bit in range(8):
            color=sum(((value>>bit)&1)<<plane for plane,value in enumerate(values))
            for plane in range(4):converted[plane]|=((remap[color]>>plane)&1)<<bit
        patterns[offset:offset+4]=bytes(converted)
    arrays['world_item_icon']=icon;arrays['world_icon_remap']=remap
    arrays['world_hud_icon_words']=rom[0x1e91:0x1e99]
    # 369F -> 3B07: frame selected from 3B67+direction*16, three planes.
    hero_address=int.from_bytes(rom[0x3b77:0x3b79],'little')
    hero_source=0x10000+(hero_address&0x3fff)
    count=rom[hero_source];hero=rom[hero_source+1:hero_source+1+count*24]
    for row in range(count*8):patterns[0x3e00+row*4:0x3e00+row*4+4]=hero[row*3:row*3+3]+b'\0'
    arrays['world_hero_bitmap']=bytes((count,))+hero
    frame_address=int.from_bytes(rom[0x300f0:0x300f2],'little')
    frame_source=0x30000+(frame_address&0x3fff)
    frame_count=rom[frame_source]&127
    arrays['world_hero_frame']=bytes((frame_count,))+rom[frame_source+3:frame_source+3+frame_count*3]
    bitmaps=bytearray();frames=bytearray();collisions=bytearray()
    for direction in range(4):
        descriptor_table=int.from_bytes(rom[0x300a0+direction*2:0x300a2+direction*2],'little')
        for animation in range(4):
            pointer=0x3b67+direction*16+animation*2
            address=int.from_bytes(rom[pointer:pointer+2],'little')
            source=0x10000+(address&0x3fff)
            assert rom[source]==4
            bitmaps.extend(rom[source:source+97])
            pointer=0x30000+(descriptor_table&0x3fff)+animation*2
            address=int.from_bytes(rom[pointer:pointer+2],'little')
            source=0x30000+(address&0x3fff)
            assert rom[source]==0x84
            collisions.extend(rom[source+1:source+3])
            frames.extend(bytes((4,))+rom[source+3:source+15])
    arrays['world_hero_bitmaps']=bitmaps;arrays['world_hero_frames']=frames
    arrays['world_hero_collisions']=collisions
    combat_bitmaps=bytearray();combat_frames=bytearray();bitmap_index=bytearray();frame_index=bytearray();combat_collisions=bytearray()
    for variant in range(4):
        for direction in range(4):
            descriptor_table=int.from_bytes(rom[0x300a0+variant*8+direction*2:0x300a2+variant*8+direction*2],'little')
            for animation in range(8):
                pointer=0x3b67+variant*64+direction*16+animation*2
                address=int.from_bytes(rom[pointer:pointer+2],'little');source=0x10000+(address&0x3fff)
                count=rom[source];assert 4<=count<=8
                bitmap_index.extend(len(combat_bitmaps).to_bytes(2,'little'));combat_bitmaps.extend(rom[source:source+1+count*24])
                pointer=0x30000+(descriptor_table&0x3fff)+animation*2
                address=int.from_bytes(rom[pointer:pointer+2],'little');source=0x30000+(address&0x3fff)
                count=rom[source]&127;assert 4<=count<=8
                combat_collisions.extend(rom[source+1:source+3]);frame_index.extend(len(combat_frames).to_bytes(2,'little'))
                combat_frames.extend(bytes((count,))+rom[source+3:source+3+count*3])
    arrays['world_combat_bitmap_index']=bitmap_index;arrays['world_combat_bitmaps']=combat_bitmaps
    arrays['world_combat_frame_index']=frame_index;arrays['world_combat_frames']=combat_frames
    arrays['world_combat_collisions']=combat_collisions;arrays['world_attack_sequences']=rom[0x3635:0x3661]
    arrays['world_attack_strength']=rom[0x2d9e:0x2dda]
    arrays['world_walk_table']=rom[0x33db:0x33ec]
    # 376C/3D7B: exterior casting graphics and 83E3 direction descriptors.
    cast_bitmaps=bytearray();cast_frames=bytearray();cast_collisions=bytearray()
    for direction in range(4):
        address=int.from_bytes(rom[0x3d7b+direction*4:0x3d7d+direction*4],'little')
        source=0x10000+(address&0x3fff);assert rom[source]==6
        cast_bitmaps.extend(rom[source:source+145])
        table=int.from_bytes(rom[0x303e3+direction*2:0x303e5+direction*2],'little')
        address=int.from_bytes(rom[0x30000+(table&0x3fff):0x30002+(table&0x3fff)],'little')
        source=0x30000+(address&0x3fff);count=rom[source]&127;assert count==4
        cast_collisions.extend(rom[source+1:source+3])
        cast_frames.extend(bytes((count,))+rom[source+3:source+3+count*3])
    arrays['world_cast_bitmaps']=cast_bitmaps;arrays['world_cast_frames']=cast_frames
    arrays['world_cast_collisions']=cast_collisions
    arrays['world_fire_velocity']=rom[0x39bc:0x39c4];arrays['world_fire_origin']=rom[0x39c4:0x39cc]

    # 371D/3736: bank-5 death graphics, alternating by C02F bit 1.
    arrays['world_death_bitmaps']=rom[0x16140:0x161a1]+rom[0x161a1:0x16202]
    assert arrays['world_death_bitmaps'][0]==arrays['world_death_bitmaps'][97]==4
    chars=rom[0x267c:rom.index(0,0x267c)]
    arrays['world_gameover_font']=b''.join(rom[0xc7c6+(c-65)*8:0xc7ce+(c-65)*8] for c in chars)
    arrays['world_gameover_words']=rom[0x268a:0x26b6]
    arrays['world_gray_tones']=rom[0x2670:0x267a]
    arrays['world_water_cycle']=rom[0x17db7:0x17dbe]
    arrays['world_armor_colors']=rom[0x1e2e:0x1e38]
    arrays['world_reveal_contours']=rom[0x2011:0x2051]
    # Normal exterior class (175F): room>=10h and low nibble!=F.
    # Preserve original compressed streams; class-1/2 entries follow below.
    room_index=bytearray(b'\xff'*512);room_streams=bytearray();room_ranges=[]
    for number in range(0x10,0x100):
        if number&15==15:continue
        bank=8+((number*2)>>8);pointer=bank*0x4000+((number*2)&255)
        address=int.from_bytes(rom[pointer:pointer+2],'little');start=bank*0x4000+(address&0x3fff)
        decoded=bytearray(160);stop,length=rle_planes(rom,start,decoded,0,1)
        assert length==160
        offset=len(room_streams);room_index[number*2:number*2+2]=offset.to_bytes(2,'little')
        room_streams.extend(rom[start:stop]);room_ranges.append({'room':number,'start':start,'end':stop})
    # Class 1: houses/other low-nibble-F rooms share bank 14 graphics.
    house_patterns=bytearray(0x4000);house_meta=bytearray(0x800)
    house_end,house_length=rle_planes(rom,0x38010,house_patterns,0,4)
    house_meta_end,_=rle_planes(rom,house_end,house_meta,0,2)
    arrays['world_house_background_rle']=rom[0x38010:house_meta_end]
    arrays['world_house_palette']=rom[0x38000:0x38010]
    extra_start=int.from_bytes(rom[0x825b:0x825d],'little');end=extra_start
    while rom[end]<128:end+=1
    count=end-extra_start;end+=1+count*4
    arrays['world_house_extra_meta']=rom[extra_start:end]
    animation_address=int.from_bytes(rom[0x175b:0x175d],'little')
    animation=bytearray(1024);rle_planes(rom,0x2c000+(animation_address&0x3fff),animation,0,4)
    arrays['world_house_animation_bitmaps']=animation[:256]

    # 175F selects class 2 for room IDs 0100..01FF; 16D0 selects bank 13.
    dungeon_patterns=bytearray(0x4000);dungeon_meta=bytearray(0x800)
    dungeon_end,dungeon_length=rle_planes(rom,0x34010,dungeon_patterns,0,4)
    dungeon_meta_end,dungeon_meta_length=rle_planes(rom,dungeon_end,dungeon_meta,0,2)
    arrays['world_dungeon_background_rle']=rom[0x34010:dungeon_meta_end]
    arrays['world_dungeon_palette']=rom[0x34000:0x34010]
    # Bank 5 BE78 overrides the class-2 palette by dungeon number, or zero
    # for unlit rooms. BDBE animates its last three entries independently.
    arrays['world_dungeon_palettes']=rom[0x17eb8:0x17f68]
    arrays['world_dungeon_dark_rooms']=rom[0x17f68:0x17f8e]
    arrays['world_dungeon_color_cycle']=rom[0x17df3:0x17dff]
    # 1976: four-byte records (room, metadata[3]), terminated by room zero.
    for name,start in [('world_room_metadata',0xbb62),('world_dungeon_metadata',0xbd1f)]:
        end=start
        while rom[end]:end+=4
        arrays[name]=rom[start:end+1]
    extra_start=int.from_bytes(rom[0x825d:0x825f],'little');extra_end=extra_start
    while rom[extra_end]<128:extra_end+=1
    extra_count=extra_end-extra_start;extra_end+=1+extra_count*4
    arrays['world_dungeon_extra_meta']=rom[extra_start:extra_end]
    animation_address=int.from_bytes(rom[0x175d:0x175f],'little')
    dungeon_animation=bytearray(1024)
    animation_end,animation_length=rle_planes(rom,0x2c000+(animation_address&0x3fff),dungeon_animation,0,4)
    # The stream initializes only 576 bytes; 174E copies a larger scratch
    # region. Preserve only initialized data, without inventing its tail.
    assert animation_length==576
    arrays['world_dungeon_animation_bitmaps']=dungeon_animation[:animation_length]

    for number in range(256):
        if number>=16 and number&15!=15:continue
        bank=8+((number*2)>>8);pointer=bank*0x4000+((number*2)&255)
        address=int.from_bytes(rom[pointer:pointer+2],'little');start=bank*0x4000+(address&0x3fff)
        decoded=bytearray(160);stop,length=rle_planes(rom,start,decoded,0,1);assert length==160
        offset=len(room_streams);room_index[number*2:number*2+2]=offset.to_bytes(2,'little')
        room_streams.extend(rom[start:stop])
    dungeon_ranges=[]
    for number in range(256,512):
        bank=8+((number*2)>>8);pointer=bank*0x4000+((number*2)&255)
        address=int.from_bytes(rom[pointer:pointer+2],'little');start=bank*0x4000+(address&0x3fff)
        decoded=bytearray(160);stop,length=rle_planes(rom,start,decoded,0,1);assert length==160
        offset=len(room_streams);room_index[number*2:number*2+2]=offset.to_bytes(2,'little')
        room_streams.extend(rom[start:stop]);dungeon_ranges.append({'room':number,'start':start,'end':stop})
    assert len(room_index)==1024 and len(room_streams)<65536
    arrays['world_room_index']=room_index;arrays['world_room_streams']=room_streams
    report={'room':room,'patterns_end':end,'decoded_pattern_bytes':pattern_end,
            'metatiles_end':meta_end,'decoded_metatile_bytes':meta_length,
            'room_pointer_offset':room_pointer,'room_stream_start':room_start,
            'room_stream_end':room_end,'hud_stream_end':hud_end}
    report['normal_exterior_room_count']=len(room_ranges)
    report['normal_exterior_compressed_bytes']=sum(r['end']-r['start'] for r in room_ranges)
    report['normal_exterior_rooms']=room_ranges
    report['room_count']=512
    report['all_rooms_compressed_bytes']=len(room_streams)
    report['dungeon_rooms']=dungeon_ranges
    report['dungeon_graphics']={'bank':13,'patterns_bytes':dungeon_length,
        'metatiles_bytes':dungeon_meta_length,'background_end':dungeon_meta_end,
        'extra_metatile_count':extra_count,'animation_bytes':animation_length,
        'animation_stream_end':animation_end}
    return patterns,extended,cells,tilemap,arrays,report

def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    patterns,meta,cells,tilemap,arrays,report=initial_room(rom)
    ram=(ROOT/'validation/sms-world/ram_02800.bin').read_bytes()
    comparisons={'room_cells':(cells,ram[0x1c00:0x1ca0]),
                 'metatiles':(meta[:0x390],ram[0x900:0xc90]),
                 'extra_metatiles':(meta[0x400:0x438],ram[0xd00:0xd38]),
                 'playfield_map':(tilemap[:0x500],ram[0x1600:0x1b00]),
                 'hud_map':(tilemap[0x500:],ram[0x1b00:0x1c00])}
    report['differences']={name:sum(a!=b for a,b in zip(actual,expected))
                           for name,(actual,expected) in comparisons.items()}
    for name,(actual,expected) in comparisons.items():
        if actual!=expected:
            print(name,[(hex(n),hex(a),hex(b)) for n,(a,b) in enumerate(zip(actual,expected)) if a!=b][:20])
    vram=(ROOT/'validation/sms-world/vram_02800.bin').read_bytes()
    used={int.from_bytes(tilemap[n:n+2],'little')&511 for n in range(0,len(tilemap),2)}|set(range(496,500))
    report['visible_pattern_byte_differences']=sum(sum(a!=b for a,b in zip(patterns[tile*32:(tile+1)*32],vram[tile*32:(tile+1)*32])) for tile in used)
    lines=['#include <genesis.h>']
    for name,data in arrays.items():
        lines+=['const u8 %s[] = {'%name]+['    '+','.join('0x%02x'%b for b in data[p:p+16])+',' for p in range(0,len(data),16)]+['};']
    (ROOT/'megadrive/src/world_data.c').write_text('\n'.join(lines)+'\n')
    (ROOT/'analysis/world_assets.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'analysis/world_reference.map.bin').write_bytes(tilemap)
    print(json.dumps(report,indent=2))
    assert all(value==0 for value in report['differences'].values())
    assert report['visible_pattern_byte_differences']==0

if __name__=='__main__':main()
