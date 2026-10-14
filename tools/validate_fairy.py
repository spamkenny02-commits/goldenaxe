"""ActualB205 capacity/refill/visitation behavior versus compiled native fairy."""
import contextlib,hashlib,io,itertools,json,re,sys
from actor_reference import ROOT
from run_core import run
REFERENCE=json.loads((ROOT/'analysis/fairy_reference.json').read_text())
def row(town=0x18,coordinate=0x25c,flags=0xb0,capacity=24,health=1,magic_capacity=16,magic=2,saved=0):
 return (0xaf,town,coordinate&255,coordinate>>8,flags,capacity,health,magic_capacity,magic,saved)+tuple([0]*22)
ROWS=[row(town=t,capacity=c,health=h,magic_capacity=c) for (t,k),c,h in itertools.product(REFERENCE['records'],range(256),[0,1,24,128,255])]
ROWS += [row(town=t,coordinate=0x25c+d,flags=f,saved=s) for (t,k),d,f,s in itertools.product(REFERENCE['records'],[0,1,2],[0,0x14,0x94,0x34,0x54,255,0x90,0xb0],[0,1,2,128,130])]
def generate():
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source)+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def field(i,a):emit(f'3a{0x80+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e0a3208c0')
 label('case');emit('af3202c03290c03291c03294c03295c03208de32a3c03a08c032ffffdd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 for i,a in [(0,0xc0b9),(1,0xc0bb),(2,0xc060),(3,0xc061),(4,0xc0a6),(5,0xc0da),(6,0xc318),(7,0xc0dc),(8,0xc0db)]:field(i,a)
 emit('3a81c06f26c13a89c0773e013240c03e0232ffffc d05b2'.replace(' ',''))
 label('ready');emit('3e013202c00603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 assert 0x28000+len(ROWS)*32<=len(image) and len(code)<0xa00
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 # Modal reward frontend returns after original6317 stores its item.
 image[0x6277:0x627b]=bytes.fromhex('2290c0c9');image[0x631a]=0xc9
 image[0x1e48:0x1e4b]=bytes.fromhex('c3403b');counter=bytes.fromhex('e52a94c0232294c0e1c9');image[0x3b40:0x3b40+len(counter)]=counter
 folder=ROOT/'validation/fairy';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/fairy_cases.inc').write_text('static const u8 fairy_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return folder
def main():
 folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'fairy cases generated');return
 harness=ROOT.parents[1]/'work/fairy-harness'
 for name in ['main.c','fairy.inc','fairy_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(harness/'src'/('game_main.inc' if name=='main.c' else name)).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*6+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[a] for a in [0x100+r[0xbb],0x318,0xda,0xdb,0xdc,0xa3,0x90,0x91,0x1e08,0x94,0x95]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original fairy effects captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n))
  if int.from_bytes(data('harness_done',2),'big'):done.append(f)
  if not int.from_bytes(data('harness_ready',2),'big'):return
  case=int.from_bytes(data('harness_case',2),'big')
  if case in checked:return
  actual=data('harness_output',11);assert actual==expected[case],(case,ROWS[case],expected[case].hex(),actual.hex());checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=len(checked),all_eight_contexts_and_256_capacity_values=True,visited_guard_flags_coordinate_extreme_health_values=True,save_HP_MP_capacities_item_text_refill_count_request_exact=True,full_game_ported=False,limits=['ActualB205/5FC7/193D/602A and capacity/refill arithmetic execute.6277 captures text HL;631A returns after6317 stores item;1E48 counts units after real95 request. No condition, table, flag or capacity arithmetic shim.', 'Isolated fixtures include byte-wrap/extreme health values not claimed naturally reachable. Modal frontend, room transformation, SRAM and natural progression are outside this unit check.'])
 (ROOT/'validation/fairy_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native fairy effects exact')
if __name__=='__main__':main()
