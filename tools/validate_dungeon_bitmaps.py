"""Original 6A66 tile-upload queue versus the compiled native bitmap helper."""
import contextlib,hashlib,io,json,re
from run_core import run,ROOT

def sha(b):return hashlib.sha256(b).hexdigest()

def fixture(rom):
    base=0x3e00;code=bytearray();labels={};fixups=[]
    def emit(s):code.extend(bytes.fromhex(s))
    def label(n):labels[n]=base+len(code)
    def jump(op,n):emit(op);fixups.append((len(code),n));emit('0000')
    emit('f331f0df2100c01101c001ff1f3600edb0')
    emit('af32fcff32fdff3e0132feff3e023240c0')
    emit('3e04d3bf3e80d3bfafd3bf3e81d3bf')
    emit('3e0b32ffff215fb51100d10e04cd000c3e0832fcff2100d1110090010004edb0af32fcff')
    label('case');emit('af3202c02100dd1101dd0106003600edb02100dd2234c0')
    emit('3a00c0322fc03a01c08787873230c93ef03231c9')
    emit('3e2032aac0af32abc0cd666a2100dd1110c0010700edb0cd93023e013202c0')
    jump('cd','hold');emit('2a00c0232200c07cfe20');jump('c2','case')
    emit('af3202c03e013204c0');label('done');jump('c3','done')
    label('hold');emit('0603');label('vblank');emit('dbbfe680');jump('ca','vblank');emit('05');jump('c2','vblank');emit('c9')
    for p,n in fixups:code[p:p+2]=labels[n].to_bytes(2,'little')
    assert base+len(code)<0x3ff0
    image=bytearray(rom);image[:3]=b'\xc3'+base.to_bytes(2,'little');image[base:base+len(code)]=code
    return image

def main():
    original=(ROOT/'input/original.sms').read_bytes();harness=ROOT.parents[1]/'work/dungeon-bitmaps-harness'
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    copies={}
    for path in (ROOT/'megadrive/src').iterdir():
        if not path.is_file():continue
        copied=harness/'src'/('game_main.inc' if path.name=='main.c' else path.name)
        assert copied.read_bytes()==path.read_bytes(),path.name
        copies[path.name]=sha(path.read_bytes())
    folder=ROOT/'validation/dungeon-bitmaps';folder.mkdir(exist_ok=True);source=folder/'source.sms';image=fixture(original);source.write_bytes(image)
    expected={};done=[];current=[None]
    def sms(frame,raw):
        if raw[4]:done.append(frame)
        if not raw[2]:return
        case=int.from_bytes(raw[:2],'little')
        current[0]=case
        if case not in expected:expected[case]=[raw[0x2f],raw[0x930],bytes(raw[0x10:0x17]),None]
    def source_vram(frame,v):
        case=current[0]
        if case is not None and expected[case][3] is None:
            tile=expected[case][1];expected[case][3]=bytes(v[tile*32:tile*32+192])
    with contextlib.redirect_stdout(io.StringIO()):run(source,40000,folder/'sms',set(),[],skip_intro=False,ram_observer=sms,vram_observer=source_vram)
    assert len(expected)==8192 and done,('source',len(expected))
    print('8192 original bitmap-queue cases captured',flush=True)
    checked=set();done=[];uploads=0;frames=set()
    def native(frame,raw):
        nonlocal uploads
        def data(k,n,off=0):
            a=sy[k]+off;return bytes(raw[(a+i)^1] for i in range(n))
        def word(k):return int.from_bytes(data(k,2),'big')
        if word('harness_done'):done.append(frame)
        if not word('harness_ready'):return
        case=word('harness_case')
        if case in checked:return
        clock,tile,queue,actual_patterns=expected[case];assert word('harness_clock')==clock
        if queue[0]:
            assert queue[:2]==b'\x01\xff' and queue[6]==6,(case,queue.hex())
            pointer=int.from_bytes(queue[2:4],'little');destination=int.from_bytes(queue[4:6],'little')&0x3fff
            assert destination==tile*32
            from extract_dungeon_bitmaps import extract
            decoded=extract(original)[2];offset=pointer-0x9000;patterns=decoded[offset:offset+192];uploads+=1;frames.add(pointer)
            assert actual_patterns==patterns,(case,'original IRQ upload')
            assert word('harness_pending')==tile+1
        else:
            patterns=bytes([0xa7])*192;assert word('harness_pending')==0
        assert data('sms_vram',192,tile*32)==patterns,(case,'bitmap bytes')
        checked.add(case)
    with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',40000,folder/'md',set(),[],skip_intro=False,ram_observer=native)
    assert len(checked)==8192 and done and uploads==1024 and frames=={0x9000,0x90c0,0x9180},(len(checked),uploads,frames)
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(original),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),source_copies=copies,cases_checked=8192,clock_values=256,destination_tiles=32,source_upload_commands=1024,source_frame_pointers=sorted(frames),source_pattern_bytes_and_native_pending_upload_exact=True,full_game_ported=False,limits=['Original 1733..1756 SRAM preparation, 6A66 upload queue and 0293/02DE SRAM upload execute in the fixture. Clock and destination metatile are controlled.','Empty source cells suppress floor-cell updates; palette outputs and source CPU workload are outside this test.','Live VRAM presentation and complete natural routes require separate checks.'])
    (ROOT/'validation/dungeon_bitmaps_report.json').write_text(json.dumps(report,indent=2)+'\n');print('8192 native bitmap cases match original queue; 1024 six-tile uploads.')

if __name__=='__main__':main()
