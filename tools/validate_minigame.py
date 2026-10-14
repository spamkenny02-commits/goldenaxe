"""Execute original AF25/6497 and native gold decisions over every gold value."""
import contextlib,hashlib,io,itertools,json,re,sys
from actor_reference import ROOT
from run_core import run
def row(mode=0,coordinate=0x248,flags=0x14,roll=0,gold=20,special=0,top=(0x3a,0x3a,0x3a),value=0,stage=1):
 return (mode,coordinate&255,coordinate>>8,flags,roll,gold,special,*top,0,value,stage)+tuple([0]*19)
ROWS=[row(coordinate=0x248+4*slot,roll=roll,special=special,top=tuple(0x34 if n<count else 0x3a for n in range(3))) for slot,roll,special,count in itertools.product(range(10),range(32),[0,0x38,0x39],range(3))]
ROWS += [row(coordinate=c,flags=f) for c,f in itertools.product([0x148,0x246,0x248,0x26c,0x270],[0,0x10,0x14,0x34,0x54,0x94,255])]
ROWS += [row(mode=1,special=s,value=v) for s,v in itertools.product([0,0x38,0x39],range(64))]
ROWS += [row(mode=2,gold=g,top=top,stage=3) for g,top in itertools.product(range(256),itertools.product(range(0x34,0x38),repeat=3))]
def generate():
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source)+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def field(i,a):emit(f'3a{0x80+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e0a3208c0')
 label('case');emit('af3202c03290c03291c03294c03295c0329bc03208de32e4dc3a08c032ffffdd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 emit('2100dc1101dc019f003600edb02133dc063a36003e3a060a')
 label('cards');emit('772310fc')
 for i,a in [(1,0xc060),(2,0xc061),(3,0xc0a6),(4,0xc09a),(5,0xc0dd),(6,0xdc0c),(7,0xdc03),(8,0xdc06),(9,0xdc09),(12,0xc073)]:field(i,a)
 emit('3e0232ffff3a80c0b7');jp('c2','not_draw');emit('cd1967');jp('c3','ready')
 label('not_draw');emit('fe01');jp('c2','reward');field(11,0xdc33);emit('2133dccdca67');jp('c3','ready')
 label('reward');emit('cd0a68')
 label('ready');emit('3e013202c00603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 assert 0x28000+len(ROWS)*32<=len(image) and len(code)<0xa00
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 # Frontends only; no condition, table, flip or reward arithmetic replaced.
 image[0x050c:0x0510]=bytes.fromhex('2290c0c9');image[0x627a]=0xc9;image[0x6876]=0xc9;image[0x1de2]=0xc9;image[0x0b95]=0xc9
 image[0x04e1:0x04e4]=bytes.fromhex('c3003b')
 # explicit retry stream: supplied byte once, then ordinary card0.
 rng=bytes.fromhex('3a9bc0b720053a9ac01801af219bc034c9')
 image[0x3b00:0x3b00+len(rng)]=rng
 image[0x1e48:0x1e4b]=bytes.fromhex('c3403b');counter=bytes.fromhex('e52a94c0232294c0e1c9');image[0x3b40:0x3b40+len(counter)]=counter
 folder=ROOT/'validation/minigame';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/minigame_cases.inc').write_text('static const u8 minigame_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return folder
def main():
 folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'minigame cases generated');return
 harness=ROOT.parents[1]/'work/minigame-harness'
 for name in ['main.c','minigame.inc','minigame_core.inc','minigame_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(harness/'src'/('game_main.inc' if name=='main.c' else name)).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*6+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x1c00:0x1c40])+bytes(r[a] for a in [0x73,0xdd,0x90,0x91,0x1ce4,0x94,0x95,0x1e08,0x9b]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original minigame effects captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n))
  if int.from_bytes(data('harness_done',2),'big'):done.append(f)
  if not int.from_bytes(data('harness_ready',2),'big'):return
  case=int.from_bytes(data('harness_case',2),'big')
  if case in checked:return
  actual=data('harness_output',73);assert actual==expected[case],(case,ROWS[case],expected[case].hex(),actual.hex());checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=len(checked),all_256_gold_values_all_64_card_triples=True,all_32_rolls_ten_slots_three_special_states_three_selection_counts=True,cells_stage_gold_text_count_requests_exact=True,full_game_ported=False,limits=['Original6719,67CA and680A execute.050C captures text pointer;627A,1DE2 and0B95 return;6876 stops before replay;1E48 counts units after real95 request. RNG04E1 supplied first roll then0 retry: RNG algorithm/timing is not verified.', 'Unit tests compare64 cells, stage, gold, text pointer, display count, executed unit count,95 request and RNG call count. Live presentation, natural randomness and full game progression excluded.'])
 (ROOT/'validation/minigame_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native minigame effects exact')
if __name__=='__main__':main()
