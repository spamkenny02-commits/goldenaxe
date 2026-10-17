"""Exhaustive plane-pair pixel parity and compiled68000 conversion benchmark."""
import contextlib,ctypes as c,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run

def main():
 base=ROOT/'validation/pattern-pairs';src=base/'src';src.mkdir(parents=True,exist_ok=True)
 code=(ROOT/'megadrive/src/main.c').read_text();lut=re.search(r'static const u32 plane_spread\[256\]=\{.*?\n\};',code,re.S).group()
 wrapper='''#include "../../../megadrive/src/pattern_convert.h"
static u32 golden(const u8 *source)
{
 u16 bit,plane;u32 result=0;
 for(bit=0;bit<8;bit++)
 {
  u16 color=0;for(plane=0;plane<4;plane++) color|=((source[plane]>>(7-bit))&1)<<plane;
  result=(result<<4)|color;
 }
 return result;
}
u32 sweep(void)
{
 u32 word,output[2];u8 input[8] __attribute__((aligned(2)));u16 n;
 for(word=0;word<65536UL;word++)
 {
  for(n=0;n<8;n++) input[n]=0;
  input[0]=input[6]=word>>8;input[1]=input[7]=word;
  pattern_convert(input,output,2);
  if(output[0]!=golden(input) || output[1]!=golden(input+4)) return word+1;
 }
 output[0]=0x12345678UL;pattern_convert(input,output,0);
 return output[0]==0x12345678UL?0:65537UL;
}
u32 check(const u8 *source,const u32 *output,u16 rows)
{
 u16 n;for(n=0;n<rows;n++) if(output[n]!=golden(source+n*4)) return n+1;return 0;
}
'''+lut+'''
void old_convert(const u8 *source,u32 *output,u16 first,u16 count)
{
 u16 tile,y;
 for(tile=first;tile<first+count;tile++) for(y=0;y<8;y++)
 {
  const u8 *planes=source+tile*32+y*4;
  output[tile*8+y]=plane_spread[planes[0]]|(plane_spread[planes[1]]<<1)|(plane_spread[planes[2]]<<2)|(plane_spread[planes[3]]<<3);
 }
}
'''
 (src/'wrapper.c').write_text(wrapper);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),str(src/'wrapper.c'),str(ROOT/'megadrive/src/pattern_convert.c'),'-o',str(base/'check.dll')],env=env,capture_output=True,text=True);assert built.returncode==0,built.stderr
 dll=c.CDLL(str(base/'check.dll'));dll.sweep.restype=c.c_uint32;assert dll.sweep()==0
 (src/'pattern_convert.c').write_text('#include "../../../megadrive/src/pattern_convert.c"\n')
 (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/pattern_convert.h"
u32 sweep(void);u32 check(const u8*,const u32*,u16);void old_convert(const u8*,u32*,u16,u16);
static u8 pixels[16384] __attribute__((aligned(2)));static u32 output[4096];
volatile u32 gaw_pair_failures,gaw_pair_old,gaw_pair_new;volatile u16 gaw_pair_done;
int main(bool hard_reset)
{
 u16 n,repeat;u32 start;VDP_setEnable(FALSE);VDP_setVInterrupt(TRUE);SYS_enableInts();
 gaw_pair_failures=sweep();
 for(n=0;n<16384;n++) pixels[n]=(n*73+(n>>7))&255;
 SYS_doVBlankProcess();start=vtimer;
 for(repeat=0;repeat<32;repeat++) {old_convert(pixels,output,0,512);__asm__ volatile("":::"memory");}
 gaw_pair_old=vtimer-start;gaw_pair_failures+=check(pixels,output,4096);
 SYS_doVBlankProcess();start=vtimer;
 for(repeat=0;repeat<32;repeat++) {pattern_convert(pixels,output,4096);__asm__ volatile("":::"memory");}
 gaw_pair_new=vtimer-start;gaw_pair_failures+=check(pixels,output,4096);
 gaw_pair_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
 env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True);(base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2000:]
 symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};rom=base/'out/release/rom.bin';results=[]
 for region in ['auto','pal']:
  observed={}
  def observe(frame,ram):
   def get(name,size):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(size)),'big')
   observed.update(frame=frame,done=get('gaw_pair_done',2),failures=get('gaw_pair_failures',4),old_frames=get('gaw_pair_old',4),new_frames=get('gaw_pair_new',4))
  with contextlib.redirect_stdout(io.StringIO()):run(rom,20000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
  assert observed.get('done') and not observed['failures'] and observed['new_frames']<observed['old_frames'],observed
  results.append(dict(region=region,**observed));print(results[-1],flush=True)
 report=dict(exhaustive_pairs=65536,each_half_independently=True,host_pixel_parity=True,compiled=results,benchmark_repetitions=32,benchmark_rows=4096,module_sha256=hashlib.sha256((ROOT/'megadrive/src/pattern_convert.c').read_bytes()).hexdigest(),lut_sha256=hashlib.sha256((ROOT/'megadrive/src/pattern_pair_lut.inc').read_bytes()).hexdigest(),kernel_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),limits=['Pixel oracle expands individual bits; all16-bit pairs tested independently in low/high positions onhost and68000. Zero count and mixed full512-tile buffer verified.','CPU-only benchmark32 repetitions,display off; not an end-to-end loading time or gameplay FPS claim. Natural menu/door/background regressions are separate.'])
 (ROOT/'validation/pattern_pairs_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
