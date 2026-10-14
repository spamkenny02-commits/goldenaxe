"""Compare original Z80 1976/1A7C/1BCD/2279 to native room preparation.

Separate fixtures exercise 512 rooms and sixteen persistent flag combinations.
Neither fixture enters the production ROM. Natural puzzle activation is not
implied by directly initializing the persistent flags under test.
"""
import contextlib
import hashlib
import io
import json
import re
from extract_world import ROOT
from extract_title import rle_planes
from run_core import run

FLAGS=[0,1,2,4,0x20,0x40,0x80,0xe0,0x24,0x44,0x84,0xe4,255,16,3,7]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture(rom,key_doors=False,room_clear=False,dungeon_cells=False,shutters=False,contacts=False,puzzles=False,items=False):
    if puzzles or items:contacts=True
    if shutters or contacts:room_clear=True
    event_fixture=key_doors or room_clear or dungeon_cells
    code=bytearray();labels={};fixups=[];base=0x3a00 if contacts else 0x3b00 if shutters else 0x3c00 if room_clear else 0x3d00 if event_fixture else 0x3e00
    def emit(data):code.extend(bytes.fromhex(data))
    def label(name):labels[name]=base+len(code)
    def jump(op,name):
        emit(op);fixups.append((len(code),name));emit('0000')
    def store(value,address):emit(f'3e{value:02x}32{address&255:02x}{address>>8:02x}')
    emit('f331f0df2100c01101c001ff1f3600edb0')  # DI; clear game RAM
    emit('af32fcff32fdff3e0132feff')
    emit('3e04d3bf3e80d3bfafd3bf3e81d3bf')
    emit('21940022bbc0')
    if event_fixture:
        for address in [0xc0d9,0xc0da,0xc0db,0xc0dc]:store(24,address)
        store(1,0xc0f1);store(1,0xc0f2)
    label('case')
    store(0,0xc002)
    emit('2a00c07ce6016722b9c0b7')
    jump('c2','dungeon')
    emit('7dfe10');jump('da','house')
    emit('e60ffe0f');jump('ca','house')
    emit('af');jump('c3','class')
    label('house');emit('3e01');jump('c3','class')
    label('dungeon');emit('3e02')
    label('class');emit('3240c04f')
    # Clear metatiles before changing graphics class, then call original decoders.
    emit('2100c91101c901ff063600edb0')
    emit('3a40c0874f3a40c0815f1600') # E = class * 3
    jump('21','streams');emit('195e2356237e32ffffeb1100c90e02cd000c')
    store(2,0xffff);emit('cdc081cd301a')
    # One independent persistent byte per room; house flags belong to its parent.
    emit('2100c11101c101ff003600edb0')
    emit('3a01c0cb3f5f1600');jump('21','flags');emit('197e3205c0')
    emit('2ab9c026c1773a40c0fe01');jump('c2','prepared_flags')
    emit('36003a05c03294c1')
    label('prepared_flags')
    emit('2ab9c0297cc60832ffff26805e2356eb1100dc0e01cd000c')
    emit('2100dd2234c0cd7619cd7922')
    store(1,0xc002);jump('cd','hold')
    emit('2a00c0232200c07cfe20');jump('c2','case')
    store(0,0xc002);store(1,0xc004)
    label('done');jump('c3','done')
    label('hold');emit('0603')
    label('vblank');emit('dbbfe680');jump('ca','vblank')
    emit('05');jump('c2','vblank');emit('c9')
    label('streams')
    for start in [0x3c010,0x38010,0x34010]:
        end,_=rle_planes(rom,start,bytearray(16384),0,4)
        code.extend((0x8000+(end&0x3fff)).to_bytes(2,'little'));code.append(start//0x4000)
    label('flags');code.extend(([0]*8+[4,0xe0,255]+[0]*5) if contacts else ([0,0,0x0d,0xe0]*4) if room_clear else [0]*16 if event_fixture else FLAGS)
    if event_fixture:
        # Insert a call before each ready handshake; original 5BB4 executes intact.
        marker=bytes.fromhex('3e013202c0')
        pos=code.index(marker)
        hook=bytearray.fromhex('cd0000')
        # Relocate existing absolute fixups after inserting the three-byte call.
        code[pos:pos]=hook
        labels={k:v+(3 if v>=base+pos else 0) for k,v in labels.items()}
        fixups=[(p+(3 if p>=pos else 0),name) for p,name in fixups]
        fixups.append((pos+1,'door'))
        label('door')
        if key_doors:
            emit('3a01c0cb3f5f1600')
            jump('21','directions');emit('197e320ac3')
            jump('21','buttons');emit('197e3220c0')
            jump('21','xs');emit('197e3213c3')
            jump('21','ys');emit('197e3211c3')
            jump('21','keys');emit('197e32dec0')
            jump('21','masters');emit('197e32efc0')
            emit('af3208decd b45b c9')
            for name,values in [('directions',[0,2,3,1]*4),('buttons',[1,4,8,2]*4),
                                ('xs',[128,32,224,128]*4),('ys',[40,80,80,112]*4),
                                ('keys',[0]*4+[1]*4+[2]*4+[5]*4),('masters',[0]*12+[1]*4)]:
                label(name);code.extend(values)
        elif dungeon_cells:
            emit('af3200dd2100dd2234c0')
            emit('3a01c0cb3f32abc0')
            emit('2ab9c02600');jump('11','scans');emit('197e32aac0')
            emit('3a40c0fe02');jump('c2','empty')
            emit('cda56acd7922')
            label('empty');emit('c9')
            label('scans');code.extend((n%36)*4 for n in range(256))
        else:
            # Contact-gated script prefixes return with input flags clear and
            # a nonmatching coordinate. Original room scripts/callees run intact.
            emit('af32a6c032a8c03208de21ffff2260c0')
            if contacts:
                store(0,0xc0a9)
                jump('cd','contact_setup')
            if shutters:
                store(0,0xc0a9)
                emit('3a01c0cb3fe6035f1600');jump('21','contacts');emit('197e32a6c0')
            if items:
                emit('21e0c011e1c00110003600edb0');store(1,0xc0e0)
                emit('3a01c0cb3fe60332e1c0')
            store(2,0xc0de)
            emit('3a01c0cb3fcb3fcb3f5f1600')
            jump('21','counts');emit('197e32a2c0')
            if contacts:
                store(1,0xc0a2);emit('3a01c0fe1e');jump('da','contact_count');store(0,0xc0a2);label('contact_count')
            emit('21b0c411b1c4014f0136a7edb0')
            emit('3a01c0cb3fe6035f1600');jump('21','occupied');emit('194e060721b0c4113000')
            label('loot_slot');emit('79b7');jump('ca','free_slot')
            emit('36080d');jump('c3','next_slot')
            label('free_slot');emit('3600')
            label('next_slot');emit('19');emit('05');jump('c2','loot_slot')
            emit('2ab9c0');jump('11','selected');emit('197eb7');jump('ca','empty')
            emit('2ab9c0291162b7195e2356eb')
            jump('cd','indirect')
            if shutters:
                emit('3a01c0fe18');jump('da','repeat')
                emit('af32a2c032a6c0');label('repeat')
            emit('2ab9c0291162b7195e2356eb')
            jump('cd','indirect');emit('c9')
            label('indirect');emit('e9')
            label('empty');emit('c9')
            label('counts');code.extend([0,1,0x80,255])
            label('occupied');code.extend([7,0,6,3])
            if shutters:label('contacts');code.extend([0x90,0xb0,0xa0,0x30])
            if contacts:
                label('contact_setup')
                emit('3a40c0fe02c0')
                emit('3a01c0cb3f5f1600');jump('21','contact_flags');emit('197e32a6c0')
                jump('21','contact_records');emit('060a' if items else '061f' if puzzles else '060b')
                label('contact_search');emit('3ab9c0be');jump('ca','contact_found')
                emit('1105001905');jump('c2','contact_search');emit('c9')
                label('contact_found');emit('235e235623eb2260c0eb4e')
                emit('3a01c0e6fefe0e');jump('c2','contact_coordinate')
                emit('3a60c0ee023260c0')
                label('contact_coordinate');emit('79feff');jump('ca','contact_cell_done')
                emit('06003a01c0e6fefe16');jump('ca','contact_nonzero')
                emit('af');jump('c3','contact_cell_store')
                label('contact_nonzero');emit('3e4d')
                label('contact_cell_store');emit('2100dc0977')
                label('contact_cell_done');emit('3a01c0e6fefe1a');jump('c2','contact_setup_done')
                store(0,0xdc4e);label('contact_setup_done');emit('c9')
                label('contact_flags');code.extend([0x14,0x94,0x54,0x34,0x10,0x15,0x04,0x14,0x14,0x14,0x14,0x14,0xb4,0x14,0x14,0x14])
                label('contact_records')
                from extract_contact_scripts import extract as extract_contacts
                from extract_room_puzzles import records as puzzle_records
                from extract_item_rewards import records as item_records
                for r in item_records(rom) if items else puzzle_records(rom) if puzzles else extract_contacts(rom):
                    if r['target']==0x5cfb:continue
                    coord=r.get('coordinate',0x168 if r['target']==0x5cc7 else 0)
                    cell=r['explicit_registers']['c'] if r['target']==0x5cec else 0x1b if r['target']==0x5cc7 else 255
                    code.extend([r['room']&255,coord&255,coord>>8,cell,0])
            label('selected')
            from extract_room_clear import extract,extract_rewards,extract_completions
            selected={x['room'] for x in extract(rom)+extract_rewards(rom)+extract_completions(rom)}
            if shutters:
                from extract_room_clear import extract_shutters
                selected={x['room'] for x in extract_shutters(rom)}
            if contacts:
                from extract_contact_scripts import extract as extract_contacts
                from extract_room_puzzles import records as puzzle_records
                from extract_item_rewards import records as item_records
                selected={r['room'] for r in (item_records(rom) if items else puzzle_records(rom) if puzzles else extract_contacts(rom)) if r['target']!=0x5cfb}
            code.extend(int(room in selected) for room in range(512))
    for offset,name in fixups:code[offset:offset+2]=labels[name].to_bytes(2,'little')
    assert base+len(code)<0x3ff0,len(code)
    image=bytearray(rom);image[:3]=b'\xc3'+base.to_bytes(2,'little');image[base:base+len(code)]=code
    assert image[0x2f]==0xfb;image[0x2f]=0
    if event_fixture:
        # The isolated fixture has no game IRQ. Skip its hardware wait only;
        # preserve original key dispatch, cell changes and full redraw routines.
        assert image[0x0b95]==0xf5;image[0x0b95]=0xc9
    if items:
        assert image[0x6317:0x631a]==bytes.fromhex('32a3c0')
        image[0x631a]=0xc9  # Exclude modal frontend; original grant/room logic remains intact.
    return image


def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    harness=ROOT.parents[1]/'work/room-cells-harness'
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in
        (harness/'out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    copies={}
    for path in (ROOT/'megadrive/src').iterdir():
        if not path.is_file():continue
        target=harness/'src'/('game_main.inc' if path.name=='main.c' else path.name)
        assert path.read_bytes()==target.read_bytes(),path.name
        copies[path.name]=sha(path.read_bytes())
    folder=ROOT/'validation/room-cells';folder.mkdir(exist_ok=True)
    image=fixture(rom);source=folder/'source-room-cells.sms';source.write_bytes(image)
    expected={};done=[]
    def observe_source(frame,raw):
        if raw[4]:done.append(frame)
        if not raw[2]:return
        case=int.from_bytes(raw[:2],'little')
        if case in expected:return
        room=case&511
        expected[case]=(bytes(raw[0x1c00:0x1ca0]),bytes(raw[0x1600:0x1b00]),
                        bytes(raw[0x6e:0x71]),raw[0x100+(room&255)])
    with contextlib.redirect_stdout(io.StringIO()):
        run(source,70000,folder/'sms',{69999},[],skip_intro=False,ram_observer=observe_source)
    assert len(expected)==8192 and done,('source',len(expected),done[:1])
    print('Original Z80: 8192 room/flag combinations captured',flush=True)
    checked=set();done=[];operations=set()
    def observe_native(frame,raw):
        def data(name,size,offset=0):
            address=sy[name]+offset
            return bytes(raw[(address+i)^1] for i in range(size))
        def word(name):return int.from_bytes(data(name,2),'big')
        if word('harness_done'):done.append(frame)
        if not word('harness_ready'):return
        case=word('harness_case')
        if case in checked:return
        cells,sms,metadata,flag=expected[case]
        assert data('room_metadata',3)==metadata,(case,'metadata')
        assert data('scratch',160,0x800)==cells,(case,'cells',[(n,a,b) for n,(a,b) in enumerate(zip(cells,data('scratch',160,0x800))) if a!=b][:8])
        assert data('sms_vram',1280,0x3800)==sms,(case,'SMS tile map')
        assert data('game_save_state',1,0x50+(case&255))==bytes([flag]),(case,'persistent flags')
        native=bytearray()
        for i in range(0,len(sms),2):
            word_value=int.from_bytes(sms[i:i+2],'little')
            value=((word_value>>11)&1)<<13|((word_value>>12)&1)<<15|((word_value>>10)&1)<<12|((word_value>>9)&1)<<11|16+(word_value&511)
            native.extend(value.to_bytes(2,'big'))
        assert data('world_new_md',1280)==native,(case,'MD tile map')
        if FLAGS[case>>9]==255:operations.add(metadata[2])
        checked.add(case)
    with contextlib.redirect_stdout(io.StringIO()):
        run(harness/'out/release/rom.bin',70000,folder/'md',{69999},[],skip_intro=False,ram_observer=observe_native)
    assert len(checked)==8192 and done,('native',len(checked),done[:1])
    assert operations==set(range(21)),operations
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),
                fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),
                room_flag_cases=8192,rooms=512,flags=FLAGS,transformation_types_checked=sorted(operations),
                original_z80_routines=['1976','1A7C','1BCD','2279'],native_production_preparation_executed=True,
                cell_bytes_compared=8192*160,sms_and_md_map_bytes_compared=8192*2560,
                metadata_and_persistent_flags_exact=True,source_copies=copies,
                natural_puzzle_activation_verified=False,full_game_ported=False,
                limits=['Flags are initialized by fixtures; natural puzzle triggers and key consumption are not tested.',
                        'Only 160 playable cells and 640 playfield words are compared; out-of-playfield queue/scratch effects are excluded.',
                        'Exterior quest/portal processing after 1976 is not covered.'])
    (ROOT/'validation/room_cells_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('8192 native cases match original Z80 cells, metadata, persistent flags and SMS/MD maps')


if __name__=='__main__':main()
