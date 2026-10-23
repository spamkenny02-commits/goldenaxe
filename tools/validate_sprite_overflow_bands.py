"""Compile production sprite-overflow decision against the v0267 implementation."""
import ctypes as c,json,os,random,subprocess
from pathlib import Path
from run_core import ROOT
from archive_lossless_evidence import sha

def body(raw):
 start=raw.index('static void prepare_world_sms_sprite_overflow(');start=raw.index('{',start);depth=1;end=start+1
 while depth:
  depth+=(raw[end]=='{')-(raw[end]=='}');end+=1
 return raw[start:end]

def main():
 folder=ROOT/'validation/sprite-overflow-bands-host';folder.mkdir(exist_ok=True);libs=[];bodies={}
 for tag in ['baseline','current']:
  raw=(subprocess.check_output(['git','show','25b70e0:megadrive/src/main.c'],cwd=ROOT).decode() if tag=='baseline' else (ROOT/'megadrive/src/main.c').read_text());bodies[tag]=body(raw)
  text='''#include <stdint.h>
#include <string.h>
typedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef int16_t s16;typedef int bool;
#define FALSE 0
#define TRUE 1
typedef struct {u16 y;} Sprite;
Sprite vdpSpriteCache[80];u16 world_video_next_overflow,world_sms_sprite_prepared_overflow,world_video_preparing,masked,terminated;
static void terminate_world_sprite_list(u16 count) {terminated=count+1;}
static void mask_world_sms_sprite_rows(u16 count) {masked=count+1;}
static void prepare_world_sms_sprite_overflow(u16 count)
'''+bodies[tag]+'''
void test(const u16 *ys,u16 count,u16 preparing,u16 *out) {u16 n;for(n=0;n<80;n++)vdpSpriteCache[n].y=ys[n];world_video_preparing=preparing;world_video_next_overflow=9;world_sms_sprite_prepared_overflow=7;masked=terminated=0;prepare_world_sms_sprite_overflow(count);out[0]=world_video_next_overflow;out[1]=world_sms_sprite_prepared_overflow;out[2]=masked;out[3]=terminated;}
'''
  src=folder/(tag+'.c');src.write_bytes(text.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];dll=folder/(tag+'.dll');subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-Wall','-Wextra','-Werror','-shared',str(src),'-o',str(dll)],env=env,check=True);lib=c.CDLL(str(dll));lib.test.argtypes=[c.POINTER(c.c_uint16),c.c_uint16,c.c_uint16,c.POINTER(c.c_uint16)];libs.append(lib)
 rng=random.Random(0x0938_0808);cases=0;overflows=clips=terminators=0
 def check(ys,count,prep):
  nonlocal cases,overflows,clips,terminators
  arg=(c.c_uint16*80)(*ys);outs=[]
  for lib in libs:
   out=(c.c_uint16*4)();lib.test(arg,count,prep,out);outs.append(tuple(out))
  assert outs[0]==outs[1],(ys,count,prep,outs);cases+=1;overflows+=outs[1][0]!=0;clips+=outs[1][2]!=0;terminators+=outs[1][3]!=0
 for raw in range(256):
  for count in [0,1,8,9,16,64,80]:
   for prep in [0,1]:check([raw+145]*80,count,prep)
 for n in range(20000):
  mode=n%4;base=rng.randrange(256)
  ys=[((rng.randrange(512) if mode==0 else (base+rng.randrange(24) if mode==1 else (rng.randrange(12)*16 if mode==2 else rng.choice([0,1,183,184,185,191,192,200,207,208,209,247,248,255]))))+145)&65535 for _ in range(80)]
  check(ys,rng.randrange(81),n&1)
 assert overflows and clips and terminators
 result=dict(passed=True,cases=cases,overflow_cases=overflows,masking_cases=clips,terminator_cases=terminators,baseline_commit='25b70e0',production_body_sha256={k:sha(v.encode()) for k,v in bodies.items()},scope='Host compiled actual production function bodies; exact overflow/mask/terminator/prepared-status decisions including clipped/transparent/offscreen Y scan. Physical native rendering is checked separately.')
 (ROOT/'analysis/sprite_overflow_bands_host_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
