"""Execute actual ACB9/AD55 branches against native conditional dialogue/gold."""
import contextlib,hashlib,io,itertools,json,re,sys
from actor_reference import ROOT
from run_core import run
def row(room=2,coordinate=0x25c,flags=0x14,gold=20,story=0,prerequisite=0,reward=0):
 return (room,0xce if room==2 else 0x22,coordinate&255,coordinate>>8,flags,gold,story,prerequisite,reward)+tuple([0]*23)
ROWS=[row(coordinate=c,story=v) for c,v in itertools.product([0x25c,0x2e0,0x344],range(256))]
ROWS += [row(coordinate=c+d,story=v,flags=f) for c,d,v,f in itertools.product([0x25c,0x2e0,0x344],[0,2],[0,127,128,255],[0,4,0x10,0x14,0x34,0x54,0x94,255])]
ROWS += [row(room=7,coordinate=0x2d4,gold=g,prerequisite=p,reward=r) for g,p,r in itertools.product(range(256),[0,1,127,128,255],[0,1,255])]
ROWS += [row(room=7,coordinate=0x2d4+d,gold=255,prerequisite=p,reward=r,flags=f) for d,p,r,f in itertools.product([0,2],[0,1,127,128,255],[0,1,255],[0,4,0x10,0x14,0x34,0x54,0x94,255])]
def generate():
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source)+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 def field(i,a):emit(f'3a{0x80+i:02x}c032{a&255:02x}{a>>8:02x}')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e0a3208c0')
 label('case');emit('af3202c03290c03291c03294c03295c03208de32e4dc3a08c032ffffdd2a06c0')
 for i in range(32):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 for i,a in [(0,0xc0b9),(1,0xc0bb),(2,0xc060),(3,0xc061),(4,0xc0a6),(5,0xc0dd),(6,0xc0d7),(7,0xc0d2),(8,0xc0f7)]:field(i,a)
 emit('3e013240c03e0232ffff3a80c0fe02');jp('c2','reward');emit('cdb9ac');jp('c3','ready');label('reward');emit('cd55ad')
 label('ready');emit('3e013202c00603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 assert 0x28000+len(ROWS)*32<=len(image) and len(code)<0xa00
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x28000:0x28000+len(ROWS)*32]=bytes(v for r in ROWS for v in r)
 # Observe original frontend; retain all conditions, flags and gold loops.
 image[0x050c:0x0510]=bytes.fromhex('2290c0c9');image[0x627a]=0xc9
 image[0x1e48:0x1e4b]=bytes.fromhex('c3403b');counter=bytes.fromhex('e52a94c0232294c0e1c9');image[0x3b40:0x3b40+len(counter)]=counter
 folder=ROOT/'validation/conditional-house';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 (ROOT/'tools/conditional_house_cases.inc').write_text('static const u8 conditional_house_cases[][32]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in ROWS)+'};\n')
 return folder
def main():
 folder=generate()
 if '--generate' in sys.argv:print(len(ROWS),'conditional dialogue cases generated');return
 harness=ROOT.parents[1]/'work/conditional-house-harness'
 for name in ['main.c','conditional_house.inc','conditional_house_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(harness/'src'/('game_main.inc' if name=='main.c' else name)).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};done=[];frames=len(ROWS)*6+100
 def sms(f,r):
  if r[4]:done.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[a] for a in [0xf7,0xdd,0x90,0x91,0x1ce4,0x94,0x95,0x1e08,0xd2,0xd7]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',frames,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert done and len(expected)==len(ROWS),(len(expected),len(ROWS));print(len(expected),'original conditional effects captured',flush=True)
 checked=set();done=[]
 def md(f,r):
  data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n))
  if int.from_bytes(data('harness_done',2),'big'):done.append(f)
  if not int.from_bytes(data('harness_ready',2),'big'):return
  case=int.from_bytes(data('harness_case',2),'big')
  if case in checked:return
  actual=data('harness_output',10);assert actual==expected[case],(case,ROWS[case],expected[case].hex(),actual.hex());checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',frames,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert done and len(checked)==len(ROWS)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=len(checked),all_256_story_byte_values=True,all_256_gold_values_prerequisite_reward_guard_boundaries=True,text_flags_gold_counts_and_requests_exact=True,full_game_ported=False,limits=['Actual ACB9/AD55 room scripts,6603 and6614/661C/6624/6634 execute.050C captures HL,627A returns;1E48 counts actual units after the original95 request. Conditions, save bytes and gold loops unmodified.', 'Isolated decisions exclude frontend rendering, SRAM persistence and natural progression. Source branch outsideCE/22 is deliberately selected; other outside contexts remain handled by the existing ordinary dialogue selector.'])
 (ROOT/'validation/conditional_house_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native conditional effects exact')
if __name__=='__main__':main()
