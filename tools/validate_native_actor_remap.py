"""Original1D0D remap: both actual palette tables, page edges and D100 scratch."""
import ctypes as c,itertools,json,os,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_history_timed import fixture
from validate_native_actor_graphics import MODULES
WRAPPER=r'''#include "source_actor_graphics.h"
u8 remap_case(const u8 *rom,u16 address,u16 bytes,u8 remap,u8 *patterns,u8 *terrain)
{
 SourceClock k;SourceIrqContext ctx={0};u8 ram[336]={0},audio[400]={0};
 audio[10]=1;ctx.ram=ram;ctx.audio=audio;ctx.low=rom;ctx.bank6=rom+0x18000;ctx.low_bytes=32768;ctx.input.lines=262;ctx.input.reset_mask=16;
 if(!source_clock_init(&k,262,0,0,1,0,0))return 0;
 return source_actor_remap(&k,&ctx,patterns,terrain,address,bytes,remap);
}
'''
def main():
 folder=ROOT/'validation/native-actor-remap';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'remap.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 original=(ROOT/'input/original.sms').read_bytes();rom=fixture(original,False)
 # The test caller uploads supplied pattern bytes, then invokes unchanged1D0D.
 code=bytes.fromhex('f3dbbf2a82c07dd3bf7cd3bf2100c93a81c0470ebeed a310fc2a82c0ed5b84c03a80c0cd0d1dc9')
 rom[0x16d0:0x16d0+len(code)]=code;assert 0x16d0+len(code)<=0x1706 and rom[0x1d0d:0x1db2]==original[0x1d0d:0x1db2]
 delay=rom.index(bytes.fromhex('2a82c0'),0x3000,0x3060);rom[delay:delay+3]=bytes.fromhex('2a88c0')
 cart=folder/'fixture.sms';cart.write_bytes(rom);host=c.CDLL(str(folder/'remap.dll'));u8=c.POINTER(c.c_uint8);host.remap_case.argtypes=[u8,c.c_uint16,c.c_uint16,c.c_uint8,u8,u8];host.remap_case.restype=c.c_uint8;source_rom=(c.c_uint8*len(original)).from_buffer_copy(original)
 types={t for t in original[0x3234e:0x3334e] if t>=32};remaps=sorted({original[0x825f+(t-32)*3]&240 for t in types}-{0});assert remaps==[16,32]
 cases=list(itertools.product(remaps,[0x6000,0x60e0,0x6100,0x7f80],[32,64,128],range(4)));pending=[];current={};checked=[0];digest=bytearray()
 def prepare(i,f):
  remap,address,size,style=cases[i]
  # Explicit parentheses keep byte generation within8 bits for both styles.
  data=bytes((0 if style==0 else 255 if style==1 else ((n*37+i*17)^((n>>2)*style))&255) for n in range(size))
  pending[:]=[(f,0x900,data),(f,0x1100,bytes([0xa7])*1024),(f,0x80,bytes([remap,(size*2)&255])+address.to_bytes(2,'little')+(address+size).to_bytes(2,'little')),(f,0x1d00,b'\1')];current.update(index=i,data=data)
 def observe(f,r):
  if f<12 or (f-12)%3:return
  i=(f-12)//3
  if i>=len(cases):return
  remap,address,size,style=cases[i];assert not r[0x1d00],('source unfinished',i)
  patterns=(c.c_uint8*size).from_buffer_copy(current['data']);terrain=(c.c_uint8*1024)(*([0xa7]*1024));assert host.remap_case(source_rom,address,size,remap,patterns,terrain)
  assert bytes(terrain)==r[0x1100:0x1500],('D100 scratch',i,cases[i],[(j,a,b) for j,(a,b) in enumerate(zip(terrain,r[0x1100:0x1500])) if a!=b][:8])
  current.update(frame=f,expected=bytes(patterns),address=address&0x3fff);digest.extend(bytes(terrain));digest.extend(bytes(patterns))
 def video(f,v):
  if current.get('frame')!=f:return
  address=current['address'];assert v[address:address+len(current['expected'])]==current['expected'],('VRAM',current['index'],cases[current['index']]);checked[0]+=1
  if current['index']+1<len(cases):prepare(current['index']+1,f+1)
 prepare(0,10);run(cart,len(cases)*3+9,folder/'source',set(),[],skip_intro=False,ram_writes=pending,ram_observer=observe,vram_observer=video)
 assert checked[0]==len(cases)
 report=dict(passed=True,cases=checked[0],remap_tables=remaps,destination_addresses=[0x6000,0x60e0,0x6100,0x7f80],pattern_sizes=[32,64,128],scratch_bytes_checked_per_case=1024,source_sha256=sha(original),fixture_sha256=sha(rom),output_sha256=sha(digest),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},limits=['Unchanged1D0D..1DB1 plus original palette tables. Controlled bitplanes and paused source audio; complete D100..D4FF scratch and written VRAM bytes compare.','Functional scratch/pixel oracle only: source entry R/phase and instruction timings are checked separately by the live graphics chain; no native68000 remap10-specific or waveform claim.'])
 (ROOT/'analysis/native_actor_remap_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report)

if __name__=='__main__':main()
