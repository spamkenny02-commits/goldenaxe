"""Run production room loading on 68000 for all 512 base room maps.

This checks resource selection, collision metatiles, decoded cells, native
tile words and background upload. Event-dependent map edits are not implied.
"""
import contextlib,hashlib,io,json,re
from extract_world import ROOT,initial_room
from extract_title import rle_planes
from run_core import run


def sha(data):return hashlib.sha256(data).hexdigest()


def packed(planar):
    output=bytearray()
    for offset in range(0,len(planar),4):
        value=0
        for bit in range(8):
            color=sum(((planar[offset+p]>>bit)&1)<<p for p in range(4))
            value|=color<<(bit*4)
        output.extend(value.to_bytes(4,'big'))
    return output


def main():
    harness=ROOT.parents[1]/'work/world-loader-harness'
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in
        (harness/'out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    copies={}
    for path in (ROOT/'megadrive/src').iterdir():
        if not path.is_file():continue
        target=harness/'src'/('game_main.inc' if path.name=='main.c' else path.name)
        assert path.read_bytes()==target.read_bytes(),path.name
        copies[path.name]=sha(path.read_bytes())
    rom=(ROOT/'input/original.sms').read_bytes();*_,arrays,_=initial_room(rom)
    classes={}
    for cls,prefix in [(0,'world_'),(1,'world_house_'),(2,'world_dungeon_')]:
        patterns=bytearray(16384);meta=bytearray(2048)
        stream=arrays[prefix+'background_rle']
        end,size=rle_planes(stream,0,patterns,0,4);rle_planes(stream,end,meta,0,2)
        if cls==0:
            for target in (0x1c0,0x1f0):meta[target:target+8]=meta[0x98:0xa0]
        extras=arrays[prefix+'extra_meta'];i=0;destination=0x400
        while extras[i]<128:
            index=extras[i];i+=1;meta[destination:destination+8]=meta[index*8:index*8+8];destination+=8
        i+=1
        for offset in range(0x401,destination,2):meta[offset]=(meta[offset]&31)|extras[i];i+=1
        classes[cls]=(bytes(meta),bytes(patterns[:size]),packed(patterns[:size]),
            arrays['world_dungeon_palettes'][:16] if cls==2 else arrays[prefix+'palette'])
    checked=set();uploaded=set();done=[];current=None
    def observe(frame,raw):
        nonlocal current
        current=None
        def data(name,size,offset=0):
            base=sy[name]+offset;return bytes(raw[(base+i)^1] for i in range(size))
        def word(name):return int.from_bytes(data(name,2),'big')
        if word('harness_done'):done.append(frame)
        if not word('harness_ready'):return
        room=word('harness_room');current=room
        if room in checked:return
        cls=2 if room>=256 else 1 if room<16 or room&15==15 else 0
        meta,patterns,_,palette=classes[cls]
        if cls==2:
            dungeon_index=0 if (room&255) in arrays['world_dungeon_dark_rooms'] else 1+(room%10)
            palette=arrays['world_dungeon_palettes'][dungeon_index*16:(dungeon_index+1)*16]
        assert word('room_id')==room,(room,'room ID')
        assert data('scratch',2048)==meta,(room,'metatiles')
        assert data('sms_vram',len(patterns))==patterns,(room,'planar background')
        assert data('sms_palette',32)==b''.join(c.to_bytes(2,'big') for c in palette),(room,'palette')
        index=arrays['world_room_index'];offset=int.from_bytes(index[room*2:room*2+2],'little')
        cells=bytearray(160);rle_planes(arrays['world_room_streams'],offset,cells,0,1)
        assert data('scratch',160,0x800)==cells,(room,'map cells')
        sms=bytearray();native=bytearray()
        for y in range(20):
            for x in range(32):
                cell=cells[(y//2)*16+x//2];address=cell*8+(y&1)*4+(x&1)*2
                entry=meta[address:address+2];sms.extend(entry)
                word=int.from_bytes(entry,'little')
                md=((word>>11)&1)<<13|((word>>12)&1)<<15|((word>>10)&1)<<12|((word>>9)&1)<<11|16+(word&511)
                native.extend(md.to_bytes(2,'big'))
        assert data('sms_vram',1280,0x3800)==sms,(room,'SMS map words')
        assert data('world_new_md',1280)==native,(room,'MD map words')
        checked.add(room)
    def video(frame,raw):
        if current is None or current in uploaded:return
        cls=2 if current>=256 else 1 if current<16 or current&15==15 else 0
        expected=classes[cls][2]
        actual=bytes(raw[(512+i)^1] for i in range(len(expected)))
        assert actual==expected,(current,'hardware background upload')
        uploaded.add(current)
    with contextlib.redirect_stdout(io.StringIO()):
        run(harness/'out/release/rom.bin',12000,ROOT/'validation/world-loader-harness',{11999},[],
            skip_intro=False,ram_observer=observe,vram_observer=video)
    assert checked==set(range(512)) and uploaded==checked and done,(len(checked),len(uploaded),done[:1])
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),
        harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),
        native_68000_loader_executed=True,rooms_checked=len(checked),dungeon_rooms_checked=256,
        map_words_bytes_compared=2560*len(checked),collision_metatiles_checked=True,
        hardware_background_uploads_checked=len(uploaded),first_done_frame=done[0],
        dungeon_palettes_exercised=10,dark_room_loads_checked=38,
        source_copies=copies,test_only_harness=True,natural_dungeon_entry_verified=False,
        quest_cell_transformations_verified=False)
    (ROOT/'validation/world_loader_harness_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('512 native room loads: cells, metatiles, SMS/MD words, palette and hardware background match')


if __name__=='__main__':main()
