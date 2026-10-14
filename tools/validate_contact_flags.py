"""Compare original 5B5A contact flags and cached coordinates/direction."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
X=[0,8,31,32,39,40,41,48,128,208,215,216,217,224,248,255]
Y=[0,8,31,32,39,40,41,48,80,112,160,167,168,176,248,255]
def sha(b):return hashlib.sha256(b).hexdigest()
def coordinate(x,y):return (((y-12)&255)&248)*8+((((x-12)&255)>>2)&62)+126
def cases():
    rows=[]
    for n in range(8192):
        x=X[n&15];y=Y[(n>>4)&15];d=(n>>8)&3;up=(n>>10)&1;mode=n>>11
        ox=(x-8)&255;oy=y;current=coordinate(ox,oy)
        cached=current if mode in (0,2) else current^2;cd=d if mode in (0,1) else d^1
        rows.append(bytes([x,y,d,up,ox,oy,current&255,current>>8,cached&255,cached>>8,cd,int(mode==3),d^1,0,0,0]))
    return rows

def fixture(original,rows):
    image=bytearray(original);code=bytearray();base=0x3d00;labels={};fixups=[]
    def emit(h):code.extend(bytes.fromhex(h))
    def label(n):labels[n]=base+len(code)
    def jump(op,n):emit(op);fixups.append((len(code),n));emit('0000')
    emit('f331f0df2100c01101c001ff1f3600edb0')
    emit('af32fcff32fdff3e0132feff3e0232ffff3212c02100802210c0')
    emit('3e04d3bf3e80d3bfafd3bf3e81d3bf')
    label('case');emit('af3202c02a10c0')
    for addr in [0xc313,0xc311,0xc30a,0xc020,0xc006,0xc007,0xc060,0xc061,0xc062,0xc063,0xc064,0xc008,0xc009]:
        emit('7e23');emit('32'+addr.to_bytes(2,'little').hex())
    emit('3a08c0b7');jump('ca','ready')
    emit('2a60c02262c03a09c03264c0')
    label('ready');emit('cd5a5b3aa6c03230c02a62c02231c03a64c03233c0')
    emit('3a13c3ee013213c33a0ac3ee01320ac33a20c0ee013220c0cd5a5b')
    emit('3aa6c03234c02a62c02235c03a64c03237c0')
    emit('2a10c0111000197c fec0');jump('c2','pointer')
    emit('26803a12c03c3212c032ffff')
    label('pointer');emit('2210c03e013202c0');jump('cd','hold')
    emit('2a00c0232200c07cfe20');jump('c2','case')
    emit('af3202c03e013204c0');label('done');jump('c3','done')
    label('hold');emit('0603');label('vblank');emit('dbbfe680');jump('ca','vblank');emit('05');jump('c2','vblank');emit('c9')
    for p,n in fixups:code[p:p+2]=labels[n].to_bytes(2,'little')
    assert base+len(code)<0x3ff0
    image[:3]=b'\xc3'+base.to_bytes(2,'little');image[base:base+len(code)]=code
    assert image[0x5ba8:0x5bab]==bytes.fromhex('cdb45b');image[0x5ba8]=0xc9
    assert image[0x2f]==0xfb;image[0x2f]=0
    data=b''.join(rows);image[0x8000:0x8000+len(data)]=data
    return image

def main():
    original=(ROOT/'input/original.sms').read_bytes();rows=cases()
    harness=ROOT.parents[1]/'work/contact-flags-harness'
    folder=ROOT/'validation/contact-flags';folder.mkdir(exist_ok=True)
    if '--prepare' in __import__('sys').argv:
        (ROOT/'tools/contact_flags_cases.inc').write_text('static const u8 cases[8192][16] = {\n'+''.join('{'+','.join(str(x) for x in r)+'},\n' for r in rows)+'};\n')
        print('Prepared 8192 boundary/input/cache cases');return
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    copies={}
    for path in (ROOT/'megadrive/src').iterdir():
        if path.is_file():
            target=harness/'src'/('game_main.inc' if path.name=='main.c' else path.name)
            assert path.read_bytes()==target.read_bytes(),path.name;copies[path.name]=sha(path.read_bytes())
    image=fixture(original,rows);source=folder/'flags.sms';source.write_bytes(image);expected={};done=[]
    def sms(frame,raw):
        if raw[4]:done.append(frame)
        if raw[2]:expected.setdefault(int.from_bytes(raw[:2],'little'),bytes(raw[0x30:0x38]))
    with contextlib.redirect_stdout(io.StringIO()):run(source,40000,folder/'sms',{39999},[],skip_intro=False,ram_observer=sms)
    assert len(expected)==8192 and done,(len(expected),done[:1]);print('8192 original flag/cache cases captured',flush=True)
    checked=set();done=[]
    def md(frame,raw):
        def data(name,size):return bytes(raw[(sy[name]+i)^1] for i in range(size))
        def word(name):return int.from_bytes(data(name,2),'big')
        if word('harness_done'):done.append(frame)
        if not word('harness_ready'):return
        case=word('harness_case')
        assert data('harness_result',8)==expected[case],(case,rows[case].hex(),data('harness_result',8).hex(),expected[case].hex())
        checked.add(case)
    with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',40000,folder/'md',{39999},[],skip_intro=False,ram_observer=md)
    assert len(checked)==8192 and done,(len(checked),done[:1])
    values=sorted({v[i] for v in expected.values() for i in (0,4)})
    assert any((v&0x77)==0x14 for v in values) and any((v&0xb0)==0xb0 for v in values)
    report=dict(flag_values_checked=values,stationary_up_gate_covered=True,moving_inside_gate_covered=True,md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(original),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases_checked=8192,two_consecutive_dispatches=True,all_flags_and_cached_coordinate_direction_exact=True,x_boundaries=X,y_boundaries=Y,source_copies=copies,original_routine='5B5A..5BA8 (return inserted before key-door dispatch)',full_game_ported=False,limits=['Isolated flag computation; room effects and natural progression are not tested here.'])
    (ROOT/'validation/contact_flags_report.json').write_text(json.dumps(report,indent=2)+'\n');print('8192 native flag/cache cases match original Z80')
if __name__=='__main__':main()
