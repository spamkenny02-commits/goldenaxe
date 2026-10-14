"""Execute the production 68000 actor loader on every room and three masks."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT,load_room_actors
from run_core import run


def sha(data):return hashlib.sha256(data).hexdigest()


def packed(planar):
    result=bytearray()
    for n in range(0,len(planar),4):
        word=0
        for bit in range(8):
            color=sum(((planar[n+p]>>bit)&1)<<p for p in range(4))
            word|=color<<(bit*4)
        result.extend(word.to_bytes(4,'big'))
    return bytes(result)


def main():
    harness=ROOT.parents[1]/'work/actor-loader-harness'
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    for name in ['actors.c','actors.h','actor_data.c']:
        assert (harness/f'src/{name}').read_bytes()==(ROOT/f'megadrive/src/{name}').read_bytes()
    rom=(ROOT/'input/original.sms').read_bytes();checked=set();converted={};done=[]
    def observe(frame,raw):
        def word(name):
            a=sy[name];return raw[a^1]*256+raw[(a+1)^1]
        if word('harness_done'):done.append(frame)
        if not word('harness_ready'):return
        room,mask=word('harness_room'),word('harness_mask')
        if (room,mask) in checked:return
        def data(name,size):
            base=sy[name];return bytes(raw[(base+i)^1] for i in range(size))
        entities,patterns,tiles,count,resources=load_room_actors(rom,room,mask)
        assert data('world_actor_state',768)==entities,(room,mask,'records')
        assert data('harness_vram',16384)==patterns,(room,mask,'planar graphics')
        expected=bytearray(16384)
        for entry in resources:
            start=0x2000+entry['tile_base']*32;end=start+entry['tile_count']*32
            fragment=bytes(patterns[start:end])
            if fragment not in converted:converted[fragment]=packed(fragment)
            expected[start:end]=converted[fragment]
        assert data('harness_patterns',16384)==expected,(room,mask,'packed graphics')
        assert word('world_actor_tiles')==tiles and word('world_actor_count')==count,(room,mask,'allocation')
        checked.add((room,mask))
    with contextlib.redirect_stdout(io.StringIO()):
        run(harness/'out/release/rom.bin',8000,ROOT/'validation/actor-loader-harness',{7999},[],skip_intro=False,ram_observer=observe)
    assert checked=={(room,mask) for room in range(512) for mask in [255,165,0]},(len(checked), sorted(checked)[-12:], done[:1])
    assert done,'Harness did not finish'
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),
                harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),
                native_68000_loader_executed=True,room_mask_cases=len(checked),rooms=512,
                persistence_masks=[255,165,0],actor_record_bytes_compared=768*len(checked),
                pattern_bytes_compared=32768*len(checked),first_done_frame=done[0],
                source_copies_exact=True,test_only_harness=True,natural_dungeon_entry_verified=False,
                source_files={name:sha((harness/f'src/{name}').read_bytes()) for name in ['actors.c','actors.h','actor_data.c','main.c']})
    (ROOT/'validation/actor_loader_harness_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(checked)} native loader cases; records, planar/packed graphics and allocation exact')


if __name__=='__main__':main()
