"""Execute original AF25/6497 and native gold decisions over every gold value."""
import contextlib,hashlib,io,itertools,json,re,sys
from actor_reference import ROOT
from run_core import run
REFERENCE=json.loads((ROOT/'analysis/house_gold_reference.json').read_text())
def row(town,gold,flags=0x14,delta=0,saved=0):
 c=0x2dc+delta
 return (0x3f,town,c&255,c>>8,flags,gold,saved)+tuple([0]*25)
ROWS=[row(t,g) for (t,a),g in itertools.product(REFERENCE['records'],range(256))]
ROWS += [row(t,g,f,d,s) for (t,a),g,f,d,s in itertools.product(REFERENCE['records'],[0,127,255],[0,0x10,0x14,0x34,0x54,0x94,255],[0,2],[0,2,128,130])]
def generate():
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source)+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def field(i,a):emit(f'3a{0x80+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e0a3208c0')
 label('case');emit('af3202c03290c03291c03292c032e4dc3208de3a08c032ffffdd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 for i,a in [(0,0xc0b9),(1,0xc0bb),(2,0xc060),(3,0xc061),(4,0xc0a6),(5,0xc0dd)]:field(i,a)
 emit('3a81c06f26c13a86c0773e013240c03e0232ffffb7cd25af')
 label('ready');emit('3e013202c00603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 assert 0x28000+len(ROWS)*32<=len(image) and len(code)<0xa00
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 # Keep gold arithmetic, original marking, context table and the real95 request.
 image[0x050c:0x0516]=bytes.fromhex('2290c03ae4dc3292c0c9')
 image[0x1e48]=0xc9;image[0x627a]=0xc9
 folder=ROOT/'validation/house-gold';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/house_gold_cases.inc').write_text('static const u8 house_gold_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return folder
def main():
 folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'gold cases generated');return
 harness=ROOT.parents[1]/'work/house-gold-harness'
 for name in ['main.c','house_gold.inc','house_gold_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(harness/'src'/('game_main.inc' if name=='main.c' else name)).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*6+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[a] for a in [0xdd,0x100+r[0xbb],0x90,0x91,0x1e08,0x92,0x1ce4]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original gold effects captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n))
  if int.from_bytes(data('harness_done',2),'big'):done.append(f)
  if not int.from_bytes(data('harness_ready',2),'big'):return
  case=int.from_bytes(data('harness_case',2),'big')
  if case in checked:return
  actual=data('harness_output',7);assert actual==expected[case],(case,ROWS[case],expected[case].hex(),actual.hex());checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=len(checked),towns=len(REFERENCE['records']),all_256_gold_values=True,gold_mark_text_sound_count_exact=True,full_game_ported=False,limits=['ActualAF25/6497 executes original conditions,193D marking,651C table and gold saturation/loops.050C captures text pointer/count;1E48 returns after real95 request;627A returns instead of waiting/redrawing.','Isolated decisions exclude live rendering, update timing, SRAM and natural reachability.'])
 (ROOT/'validation/house_gold_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native gold effects exact')
if __name__=='__main__':main()
