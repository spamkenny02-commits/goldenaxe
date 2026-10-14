"""Actual ADA1/ADF2/AF88 quest dispatch versus compiled native decisions."""
import contextlib,hashlib,io,itertools,json,re,sys
from actor_reference import ROOT
from run_core import run
REFERENCE=json.loads((ROOT/'analysis/plain_house_dialogue_reference.json').read_text())
RECORDS=REFERENCE['contexts']
ROWS=[(r['room'],r['outside'],(r['coordinate']+delta)&255,(r['coordinate']+delta)>>8,flags,r['table']&255,r['table']>>8,r['text_pc']&255,r['text_pc']>>8,r['coordinate']&255,r['coordinate']>>8)+tuple([0]*21) for r,flags,delta in itertools.product(RECORDS,[0,4,0x10,0x14,0x34,0x54,0x94,255],[0,2,64])]
def generate():
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def field(i,a):emit(f'3a{0x80+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e0a3208c0')
 label('case');emit('af3202c032a3c03290c03291c03a08c032ffffdd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 for i,a in [(1,0xc0bb),(2,0xc060),(3,0xc061),(4,0xc0a6)]:field(i,a)
 emit('af3290c03291c03e0232ffff3a89c04f3a8ac0473a85c05f3a86c057cd003a')
 label('ready');emit('3e013202c00603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 assert len(ROWS)*32<=0x18000 and len(code)<0xa00
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 image[0x3a00:0x3a04]=bytes.fromhex('cd7e66c9');image[0x6277:0x627b]=bytes.fromhex('2290c0c9')
 folder=ROOT/'validation/plain-house';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/plain_house_source_pcs.inc').write_text('static const u16 plain_house_source_pcs[]={'+','.join(str(r['text_pc']) for r in RECORDS)+'};\n')
 (ROOT/'tools/plain_house_cases.inc').write_text('static const u8 plain_house_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'quest cases generated');return
 harness=ROOT.parents[1]/'work/plain-house-harness'
 for name in ['main.c','plain_house_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(harness/'src'/('game_main.inc' if name=='main.c' else name)).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*6+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x90:0x92]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original quest decisions captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n))
  if int.from_bytes(data('harness_done',2),'big'):done.append(f)
  if not int.from_bytes(data('harness_ready',2),'big'):return
  case=int.from_bytes(data('harness_case',2),'big')
  if case in checked:return
  actual=data('harness_output',2);assert actual==expected[case],(case,ROWS[case],expected[case].hex(),actual.hex());checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=len(checked),contexts=len(RECORDS),source_text_pointer_exact=True,full_game_ported=False,limits=['Original667E conditions and context-table search execute; only6277 text frontend stores original HL then returns. No condition or table shim.','Valid original context rows across all extracted21 nodes; flag and coordinate mismatches return without text. Runtime presentation, reachability and complete natural quests remain unproved.'])
 (ROOT/'validation/plain_house_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native quest decisions/effects exact')
if __name__=='__main__':main()
