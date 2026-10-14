"""Execute the original Z80 decoders on all 512 maps and class-2 resources.

The separate SMS fixture replaces boot only, calls original 032A/0C00/81C0,
and holds each result for three video frames. No fixture enters production.
Quest-dependent cell transformations after 192A are deliberately not covered.
"""
import contextlib, hashlib, io, json
from extract_world import ROOT, initial_room
from extract_title import rle_planes
from run_core import run


def sha(data): return hashlib.sha256(data).hexdigest()


def fixture(rom):
    code=bytearray();labels={};fixups=[];base=0x3e00
    def emit(data):code.extend(bytes.fromhex(data))
    def label(name):labels[name]=base+len(code)
    def branch(op,name):
        emit(op);fixups.append((len(code),name));emit('0000')
    def store(value,address):emit(f'3e{value:02x}32{address&255:02x}{address>>8:02x}')
    emit('f331f0df')                         # DI; SP=DFF0
    emit('af3202c03204c03206c0')             # zero handshake fields
    # Mapper defaults are made explicit (no SRAM, slots 0/1/13).
    emit('af32fcff32fdff3e0132feff')
    # Mode 4, IRQs/display disabled. Status still supplies video boundaries.
    emit('3e04d3bf3e80d3bfafd3bf3e81d3bf')
    store(13,0xffff)
    emit('21008011a0dc011000edb0')          # palette
    emit('110040cd2a03')                   # original VRAM decoder, HL=8010
    emit('1100c90e02cd000c')               # original metatile decoder
    store(2,0xc040);store(2,0xffff)
    emit('cdc081')                         # original extra/collision metatiles
    store(11,0xffff)
    emit('2a5d171100d10e04cd000c')          # original animation decoder
    store(1,0xc006);store(1,0xc002)
    branch('cd','hold')
    emit('2100002200c0')
    label('room')
    store(0,0xc002);store(2,0xc006)
    emit('2a00c0297cc60832ffff26805e2356eb1100dc0e01cd000c')
    store(1,0xc002);branch('cd','hold')
    emit('2a00c0232200c07cfe02');branch('c2','room')
    store(0,0xc002);store(1,0xc004)
    label('done');branch('c3','done')
    label('hold');emit('0603')
    label('vblank');emit('dbbfe680');branch('ca','vblank')
    emit('05');branch('c2','vblank');emit('c9')
    for offset,name in fixups:code[offset:offset+2]=labels[name].to_bytes(2,'little')
    assert base+len(code)<0x3ff0
    image=bytearray(rom);image[:3]=bytes.fromhex('c3003e')
    image[base:base+len(code)]=code
    # RST 28 is otherwise original. Suppress its EI, keeping the decoder
    # isolated from the normal game's IRQ handler and uninitialized state.
    assert image[0x2f]==0xfb;image[0x2f]=0
    return image


def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    *_,arrays,metadata=initial_room(rom)
    folder=ROOT/'validation/dungeon-world-assets';folder.mkdir(exist_ok=True)
    image=fixture(rom);path=folder/'source-decoder-fixture.sms';path.write_bytes(image)
    patterns=bytearray(16384);meta=bytearray(2048)
    end,_=rle_planes(rom,0x34010,patterns,0,4)
    rle_planes(rom,end,meta,0,2)
    extras=arrays['world_dungeon_extra_meta'];count=extras.index(255)
    extended=bytearray()
    for tile in extras[:count]:extended.extend(meta[tile*8:tile*8+8])
    for i in range(count*4):extended[i*2+1]=(extended[i*2+1]&31)|extras[count+1+i]
    checked=set();graphics_checked=False;done=[];current=None
    def observe(frame,ram):
        nonlocal graphics_checked,current
        current=None
        if ram[4]:done.append(frame)
        if not ram[2]:return
        if ram[6]==1:
            assert ram[0x900:0x900+648]==meta[:648],'Z80 metatiles'
            assert ram[0xd00:0xd00+len(extended)]==extended,'Z80 collision flags'
            assert ram[0x1100:0x1340]==arrays['world_dungeon_animation_bitmaps'],'Z80 animation'
            assert ram[0x1ca0:0x1cb0]==arrays['world_dungeon_palette'],'Z80 palette'
            current='graphics'
        elif ram[6]==2:
            room=int.from_bytes(ram[:2],'little')
            if room in checked:return
            index=arrays['world_room_index'];offset=int.from_bytes(index[room*2:room*2+2],'little')
            expected=bytearray(160)
            rle_planes(arrays['world_room_streams'],offset,expected,0,1)
            assert ram[0x1c00:0x1ca0]==expected,(room,'Z80 room cells')
            checked.add(room)
    def video(frame,vram):
        nonlocal graphics_checked
        if current=='graphics':
            assert vram[:4096]==patterns[:4096],'Z80 VRAM background'
            graphics_checked=True
    with contextlib.redirect_stdout(io.StringIO()):
        run(path,1700,folder,{1699},[],skip_intro=False,ram_observer=observe,vram_observer=video)
    assert checked==set(range(512)),(len(checked),max(checked,default=-1),done[:1])
    assert graphics_checked and done
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),
        fixture_sha256=sha(image),source_z80_decoders_executed=['032A','0C00','81C0'],
        maps_checked=len(checked),map_cell_bytes_compared=160*len(checked),
        dungeon_background_bytes=4096,dungeon_metatile_bytes=648,
        dungeon_extra_metatile_bytes=len(extended),dungeon_animation_bytes=576,
        dungeon_palette_bytes=16,first_done_frame=done[0],
        compressed_stream_bytes=metadata['all_rooms_compressed_bytes'],
        test_only_fixture=True,natural_dungeon_entry_verified=False,
        quest_cell_transformations_verified=False,
        files={name:sha((ROOT/name).read_bytes()) for name in
            ['tools/extract_world.py','megadrive/src/world_data.c','tools/validate_dungeon_world_assets.py']})
    (ROOT/'validation/dungeon_world_assets_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('512 maps and dungeon graphics match original Z80 decoder execution')


if __name__=='__main__':main()
