"""Execute original Z80 maze exits and compare the compiled native implementation."""
import contextlib,hashlib,io,itertools,json,re
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
CASES=[(room&255,room>>8,cl,progress,d,y,0) for room,cl,progress,d,y in itertools.product([0x77,0x76,0x67,0x177],range(3),range(5),range(4),[95,96])]
# Final six cases retain state: full correct path, then ordinary return south.
CASES += [(0x77,0,0,0,d,y,int(i>0)) for i,(d,y) in enumerate([(3,96),(0,16),(3,95),(1,160),(0,16),(1,160)])]
def sha(b):return hashlib.sha256(b).hexdigest()
def generate():
    original=(ROOT/'input/original.sms').read_bytes();code=bytearray();labels={};fix=[];base=0x3000
    def emit(h):code.extend(bytes.fromhex(h))
    def label(n):labels[n]=base+len(code)
    def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
    def store(v,a):emit(f'3e{v:02x}32{a&255:02x}{a>>8:02x}')
    emit('f331f0df2100c01101c001ff1f3600edb0')
    emit('af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf')
    jp('dd21','table')
    label('case');store(0,0xc002)
    emit('dd7e06b7');jp('c2','retain')
    emit('dd7e0032b9c0dd7e0132bac0dd7e03326cc0')
    label('retain');emit('dd7e023240c0dd7e053211c3dd7e04fe02');jp('d2','horizontal')
    emit('b73e10');jp('c2','vertical');emit('3ef0')
    label('vertical');emit('cdc521');jp('c3','ready')
    label('horizontal');emit('fe023e01');jp('c2','horizontal_call');emit('3eff')
    label('horizontal_call');emit('cdcb21')
    label('ready');store(1,0xc002);emit('0603')
    label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
    emit('110700dd192a00c0232200c001'+len(CASES).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case')
    store(0,0xc002);store(1,0xc004);label('done');jp('c3','done')
    label('table');code.extend(bytes(v for row in CASES for v in row))
    for pos,name in fix:code[pos:pos+2]=labels[name].to_bytes(2,'little')
    assert base+len(code)<0x4000
    image=bytearray(original);image[:3]=bytes([0xc3,base&255,base>>8]);image[base:base+len(code)]=code
    assert image[0x21c5:0x2237]==original[0x21c5:0x2237]
    assert image[0x18e2:0x190b]==original[0x18e2:0x190b]
    folder=ROOT/'validation/forest-maze';folder.mkdir(exist_ok=True)
    (folder/'source-maze.sms').write_bytes(image)
    header='static const u8 maze_cases[][7]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in CASES)+'};\n'
    (ROOT/'tools/forest_maze_cases.inc').write_text(header)
    return original,bytes(image),folder

def main():
    original,image,folder=generate()
    if '--generate' in __import__('sys').argv:return
    harness=ROOT.parents[1]/'work/forest-maze-harness'
    assert (harness/'src/game_main.inc').read_bytes()==(ROOT/'megadrive/src/main.c').read_bytes()
    assert (harness/'src/forest_maze_cases.inc').read_bytes()==(ROOT/'tools/forest_maze_cases.inc').read_bytes()
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    expected={};done=[]
    def sms(f,r):
        if r[4]:done.append(f)
        if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),(int.from_bytes(r[0xb9:0xbb],'little'),r[0x6c]))
    with contextlib.redirect_stdout(io.StringIO()):run(folder/'source-maze.sms',2500,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
    assert done and len(expected)==len(CASES),(len(expected),len(CASES))
    print(f'{len(expected)} original Z80 exits captured',flush=True)
    checked=set();done=[]
    def md(f,r):
        def w(n):return int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(2)),'big')
        if w('harness_done'):done.append(f)
        if not w('harness_ready'):return
        case=w('harness_case')
        if case in checked:return
        actual=(w('harness_room'),w('harness_progress'))
        assert actual==expected[case],(case,CASES[case],expected[case],actual)
        if case>=480:assert w('harness_stage')==1,(case,'production transition not entered')
        checked.add(case)
    with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',2500,folder/'md',set(),[],skip_intro=False,ram_observer=md)
    assert done and len(checked)==len(CASES),(len(checked),len(CASES))
    sequence=[expected[i] for i in range(480,len(CASES))]
    assert sequence==[(0x77,1),(0x77,2),(0x77,3),(0x77,4),(0x67,5),(0x77,0)],sequence
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(original),fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),cases=len(checked),original_routines_executed=['21C5..2236','18E2..190A on successful final exit'],all_room_and_progress_results_exact=True,ordered_production_begin_and_stage_zero_sequence=sequence,production_source_copy_sha256=sha((ROOT/'megadrive/src/main.c').read_bytes()),full_game_ported=False,limits=['480 controlled exits cover four room words, three graphics classes, five valid maze stages, all four directions and Y=95/96 boundary.','Six ordered exits use native production begin_room_transition and step_room_transition stage zero, with normal room assets. Original fixture directly calls unchanged exit routines.','Complete natural route, rendered scrolling, actors, audio, global timing and invalid progress values are outside this check.'])
    (ROOT/'validation/forest_maze_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(checked)} native exits exact; full ordered maze path succeeds',flush=True)
if __name__=='__main__':main()
