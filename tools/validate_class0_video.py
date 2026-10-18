"""Exhaustive attribute/color and independent planar-pixel checks."""
import contextlib,ctypes as c,hashlib,io,json,os,re,subprocess,sys
from pathlib import Path
from generate_class0_video import generate
from validate_native_patterns import decode
ROOT=Path(__file__).resolve().parents[1]

def main():
 assets=generate();folder=ROOT/'validation/class0-video';folder.mkdir(exist_ok=True);env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-O3','-shared','-Wall','-Wextra','-Werror','-I',str(ROOT.parents[1]/'work/sgdk/inc'),str(ROOT/'megadrive/src/source_class0_video.c'),'-o',str(folder/'video.dll')],env=env,check=True)
 dll=c.CDLL(str(folder/'video.dll'));dll.source_class0_video_word.argtypes=[c.c_uint16];dll.source_class0_video_word.restype=c.c_uint16
 dll.source_class0_video_map.argtypes=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.c_uint16]
 dll.source_class0_video_palette.argtypes=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint16)]
 dll.source_class0_video_patterns.restype=c.POINTER(c.c_uint32)
 dll.source_class0_video_background.restype=c.c_uint16
 for word in range(65536):
  expected=16+(word&511)|((word&0x200)<<2)|((word&0x400)<<2)|((word&0x800)<<2)|((word&0x1000)<<3)
  assert dll.source_class0_video_word(word)==expected,word
  if word%32768==0:
   source=b''.join(w.to_bytes(2,'little') for w in range(word,word+32768));native=(c.c_uint16*32768)();dll.source_class0_video_map((c.c_uint8*65536).from_buffer_copy(source),native,32768)
   assert all(v==dll.source_class0_video_word(word+n) for n,v in enumerate(native))
 levels=[0,3,5,7]
 for value in range(256):
  palette=(c.c_uint16*32)();dll.source_class0_video_palette((c.c_uint8*16)(*([value]*16)),palette)
  expected=levels[value&3]<<1|levels[(value>>2)&3]<<5|levels[(value>>4)&3]<<9
  assert list(palette)[16:]==[expected]*16 and palette[0]==0
 rom=(ROOT/'input/original.sms').read_bytes();sms,_=decode(rom[0x3c010:]);packed=dll.source_class0_video_patterns()
 def color(value):return levels[value&3]<<1|levels[(value>>2)&3]<<5|levels[(value>>4)&3]<<9
 assert dll.source_class0_video_background()==color(rom[0x3c000])
 assert list(palette)[1:16]==[color(v) for v in rom[0x3c001:0x3c010]]
 for tile in range(193):
  for y in range(8):
   for x in range(8):
    expected=sum(((sms[tile*32+y*4+p]>>(7-x))&1)<<p for p in range(4));actual=(packed[tile*8+y]>>(28-x*4))&15
    assert actual==expected,(tile,x,y)
 report=dict(attribute_words=65536,map_words=65536,upper_palette_values=256,base_pattern_pixels=193*64,assets=assets,module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_class0_video.c').read_bytes()).hexdigest(),limits=['Host conversion and ROM atlas only; physical SGDK transfers and complete-loader timing are checked separately.'])
 (ROOT/'analysis/class0_video_conversion_report.json').write_text(json.dumps(report,indent=2)+'\n');print('65536 attributes,65536 map words,256 palette values and12352 pixels pass.')
 if '--68k' in sys.argv:compiled_check()

def compiled_check():
 from run_core import run
 base=ROOT/'validation/class0-video/kernel';src=base/'src';src.mkdir(parents=True,exist_ok=True)
 (src/'video.c').write_text('#include "../../../../megadrive/src/source_class0_video.c"\n')
 (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_class0_video.h"
volatile u32 gaw_video_words,gaw_video_failures;
volatile u16 gaw_video_done,gaw_video_tails;
static u8 source[512] __attribute__((aligned(2)));
static u16 output[258],map[768],palette[32];
static u16 expected(u16 w) {return (16+(w&511))|((w&0x200)<<2)|((w&0x400)<<2)|((w&0x800)<<2)|((w&0x1000)<<3);}
int main(bool hard_reset)
{
 u32 start;u16 n,count,w;VDP_setEnable(FALSE);
 for(start=0;start<65536UL;start+=256)
 {
  output[0]=0x7777;output[257]=0x7777;
  for(n=0;n<256;n++) {w=start+n;source[n*2]=w;source[n*2+1]=w>>8;}
  source_class0_video_map(source,output+1,256);
  for(n=0;n<256;n++) if(output[n+1]!=expected(start+n)) gaw_video_failures++;
  if(output[0]!=0x7777 || output[257]!=0x7777) gaw_video_failures++;
  gaw_video_words+=256;
 }
 for(count=0;count<8;count++)
 {
  for(n=0;n<258;n++) output[n]=0x7777;
  for(n=0;n<count;n++) {w=0xf000+count*63+n*33;source[n*2]=w;source[n*2+1]=w>>8;}
  source_class0_video_map(source,output+1,count);
  for(n=0;n<count;n++) if(output[n+1]!=expected(0xf000+count*63+n*33)) gaw_video_failures++;
  if(output[0]!=0x7777) gaw_video_failures++;
  for(n=count+1;n<258;n++) if(output[n]!=0x7777) gaw_video_failures++;
  gaw_video_tails++;
 }
 if(source_class0_video_upload(0,palette) || source_class0_video_upload(map,0)) gaw_video_failures++;
 VDP_setEnable(TRUE);
 if(source_class0_video_upload(map,palette)) gaw_video_failures++;
 VDP_setEnable(FALSE);gaw_video_done=1;
 while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
 sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True)
 (base/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
 sy={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=base/'out/release/rom.bin';rows=[]
 for region in ['auto','pal']:
  result={}
  def observe(f,ram):
   def value(name,n):return int.from_bytes(bytes(ram[(sy[name]+i)^1] for i in range(n)),'big')
   result.update(frame=f,done=value('gaw_video_done',2),words=value('gaw_video_words',4),tails=value('gaw_video_tails',2),failures=value('gaw_video_failures',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cartridge,10000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(result.get('done')))
  assert result.get('done') and result['words']==65536 and result['tails']==8 and not result['failures'],(region,result)
  rows.append(dict(region=region,**result));print(rows[-1],flush=True)
 report=dict(cases=65536,tail_lengths=list(range(8)),regions=rows,upload_rejects_null_and_enabled=True,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_class0_video.c').read_bytes()).hexdigest(),assets_sha256=hashlib.sha256((ROOT/'megadrive/src/source_class0_video_assets_generated.h').read_bytes()).hexdigest(),limits=['Compiled68000 assembly conversion, guarded output and upload preconditions. Complete physical uploads and source-clock loading are checked by the separate physical-video profile.'])
 (ROOT/'analysis/class0_video_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
