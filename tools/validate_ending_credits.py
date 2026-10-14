"""Compare every native credits tick and row to original7027/7061."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
def generate():
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff')
 emit('3e04d3bf3e80d3bfafd3bf3e81d3bf3e0c32ffff214eb31100c9010005edb0')
 emit('21007e22c4dc2100c922c6dccd6170')
 label('snapshot');emit('3e013202c00603');label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('af3202c03ac1dcb7');jp('c2','done')
 emit('2a00c0232200c0cd2770');jp('c3','snapshot')
 label('done');emit('3e013204c0');jp('c3','done')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 assert image[0x7048:0x704b]==bytes.fromhex('cd950b');image[0x7048:0x704b]=bytes.fromhex('c90000')
 # Capture the same64 bytes queued by0384; retain the original DE row address.
 image[0x384:0x387]=bytes.fromhex('c3003a');capture=bytes.fromhex('d51100d2014000edb0d1c9');image[0x3a00:0x3a00+len(capture)]=capture
 folder=ROOT/'validation/ending-credits';folder.mkdir(exist_ok=True);(folder/'source.sms').write_bytes(image)
 return image,folder
def main():
 image,folder=generate()
 if '--generate' in sys.argv:return
 harness=ROOT.parents[1]/'work/ending-credits-harness'
 for name in ['ending_credits.inc','ending_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(harness/'src'/name).read_bytes()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 expected={};finished=[]
 def sms(f,r):
  if r[4]:finished.append(f)
  if r[2]:expected.setdefault(int.from_bytes(r[:2],'little'),bytes(r[0x1cc0:0x1cc8])+bytes([r[0x19]])+bytes(r[0x1200:0x1240]))
 with contextlib.redirect_stdout(io.StringIO()):run(folder/'source.sms',45000,folder/'sms',set(),[],skip_intro=False,ram_observer=sms)
 assert finished and len(expected)>7000,(len(expected),finished[:1]);print(len(expected),'original credit ticks captured',flush=True)
 checked=set();finished=[]
 def md(f,r):
  data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n))
  if int.from_bytes(data('harness_done',2),'big'):finished.append(f)
  if not int.from_bytes(data('harness_ready',2),'big'):return
  case=int.from_bytes(data('harness_case',2),'big')
  if case in checked:return
  actual=data('harness_output',73);assert actual==expected[case],(case,[(i,a,b) for i,(a,b) in enumerate(zip(expected[case],actual)) if a!=b][:24])
  checked.add(case)
 with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',45000,folder/'md',set(),[],skip_intro=False,ram_observer=md)
 assert finished and len(checked)==len(expected),(len(checked),len(expected))
 final=expected[max(expected)];assert final[1]==1
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),harness_sha256=hashlib.sha256((harness/'out/release/rom.bin').read_bytes()).hexdigest(),native_module_sha256=hashlib.sha256((ROOT/'megadrive/src/ending_credits.inc').read_bytes()).hexdigest(),ticks=len(checked),all_8_state_bytes_vscroll_and_64_row_bytes_exact=True,final_state=final[:9].hex(),production_scene_covered_by_this_test=False,module_used_by_production=True,full_game_ported=False,limits=['Original7027 arithmetic and7061 glyph/spacing/row-pointer routines run with original text and glyph map.0384 queue transfer is replaced by copying the same64-byte row into observation RAM;7048 IRQ/outer-loop tail returns after one arithmetic tick. No arithmetic/glyph/random shims.','Native standalone module executes the full natural text stream until its terminator, including blank-row controls, fractional scroll,28-row wrap and final done flag. Framebuffer, IRQ/VRAM presentation, boss-to-ending integration, music and input return are not covered by this module test.'])
 (ROOT/'validation/ending_credits_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'native credits ticks/rows exact')
if __name__=='__main__':main()
