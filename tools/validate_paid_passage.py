"""ActualB205 capacity/refill/visitation behavior versus compiled native paid_passage."""
import contextlib,hashlib,io,itertools,json,re,sys
from actor_reference import ROOT
from run_core import run
REFERENCE=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text());ROUTES=REFERENCE['routes']
def row(mode=0,town=0x1a,coordinate=0x25c,flags=0x14,gold=20,accepted=255,barrier=17,saved=255):
 target=next(r[1] for r in ROUTES if r[0]==town)
 return (mode,town,coordinate&255,coordinate>>8,flags,gold,accepted,barrier,saved,target)+tuple([0]*22)
ROWS=[row(town=t,gold=g,accepted=a,barrier=b) for t,g,a,b in itertools.product(REFERENCE['towns'],range(256),[0,255],[1,17])]
ROWS += [row(town=t,coordinate=0x25c+d,flags=f) for t,d,f in itertools.product(REFERENCE['towns'],[0,2],[0,4,0x10,0x14,0x34,0x54,0x94,255])]
ROWS += [row(mode=1,town=t,coordinate=0x19c+d,flags=f,saved=s) for t,d,f,s in itertools.product(REFERENCE['towns'],[0,2],range(256),[0,1,128,255])]
def generate():
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source)+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def field(i,a):emit(f'3a{0x80+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e0a3208c0')
 label('case');emit('af3202c03290c03291c03294c03295c03208de32e4dc3a08c032ffffdd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 for i,a in [(1,0xc0bb),(2,0xc060),(3,0xc061),(4,0xc0a6),(5,0xc0dd),(7,0xdc38)]:field(i,a)
 emit('3a89c06f26c13a88c0773e9f32b9c03e013240c03eaa32bdc03ebb32bec03e103237dc3e013239dc3249dc3e123247dc3e133248dc3e0232ffffcd9eb1')
 label('ready');emit('3e013202c00603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 assert 0x28000+len(ROWS)*32<=len(image) and len(code)<0xa00
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 # Frontends only: confirmation input, text pointer, load state and wait.
 image[0x050c:0x0510]=bytes.fromhex('2290c0c9');image[0x60bc:0x60c0]=bytes.fromhex('3a86c0c9');image[0x627a]=0xc9;image[0x1de2]=0xc9
 load=bytes.fromhex('2abbc022b9c0af3240c0c9');image[0x65e1:0x65e1+len(load)]=load
 image[0x1e48:0x1e4b]=bytes.fromhex('c3403b');counter=bytes.fromhex('e52a94c0232294c0e1c9');image[0x3b40:0x3b40+len(counter)]=counter
 folder=ROOT/'validation/paid-passage';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/paid_passage_cases.inc').write_text('static const u8 paid_passage_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return folder
def main():
 folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'paid_passage cases generated');return
 harness=ROOT.parents[1]/'work/paid-passage-harness'
 for name in ['main.c','paid_passage.inc','paid_passage_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(harness/'src'/('game_main.inc' if name=='main.c' else name)).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*6+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[a] for a in [0xdd,0x1ce4,0x90,0x91,0x1e08,0x94,0x95,0x1c37,0x1c38,0x1c39,0x1c47,0x1c48,0x1c49,0xb9,0xbb,0xbd,0xbe,0x100+r[0x89]]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original paid_passage effects captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n))
  if int.from_bytes(data('harness_done',2),'big'):done.append(f)
  if not int.from_bytes(data('harness_ready',2),'big'):return
  case=int.from_bytes(data('harness_case',2),'big')
  if case in checked:return
  actual=data('harness_output',18);assert actual==expected[case],(case,ROWS[case],expected[case].hex(),actual.hex());checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=len(checked),all_256_gold_values_six_contexts_confirmation_open_guard=True,all_256_exit_flags_six_routes_destination_flag_boundaries=True,fields_cells_price_text_gold_count_request_and_exit_exact=True,full_game_ported=False,limits=['Actual B19E ->616F/6036/61C3/61D5 executes.050C captures HL,60BC returns supplied answer,627A/1DE2 return,1E48 counts actual units after95.65E1 room-load frontend copies C0BB to C0B9/class0 then returns;616F routing and1947 flag marking execute unmodified.', 'Isolated gold/cell/route decisions exclude frontend pixels, actual resource loading, SRAM and natural full progression.'])
 (ROOT/'validation/paid_passage_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native paid_passage effects exact')
if __name__=='__main__':main()
