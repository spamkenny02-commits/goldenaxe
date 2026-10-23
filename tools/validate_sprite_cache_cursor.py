"""Differential actual entity sprite emitter bodies with ROM descriptors."""
import ctypes as c,json,os,random,subprocess
from pathlib import Path
from run_core import ROOT
from archive_lossless_evidence import sha

def extract(text):
 start=text.index('static u16 add_world_entity_sprites(');start=text.index('{',start);end=start+1;depth=1
 while depth:depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]
def main():
 folder=ROOT/'validation/sprite-cache-cursor-host';folder.mkdir(exist_ok=True);libs=[];bodies={};env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 prefix='''#include <stdint.h>
#include <string.h>
typedef uint8_t u8;typedef uint16_t u16;typedef int16_t s16;
#define PAL1 1
#define SPRITE_SIZE(a,b) 0
#define TILE_ATTR_FULL(p,pr,v,h,t) (((p)<<13)|((pr)<<15)|((v)<<12)|((h)<<11)|(t))
/* Host little-endian union keeps link in the low word byte, as on MD. */
typedef struct {s16 y;union {struct {u8 link,size;};u16 size_link;};u16 attribut;s16 x;} VDPSprite;
VDPSprite vdpSpriteCache[80];static u8 memory[65792];
static u16 descriptor_word(u16 address) {return memory[address]|((u16)memory[(u16)(address+1)]<<8);}
static const u8 *descriptor_frame(u16 address) {return memory+address;}
static __attribute__((unused)) void VDP_setSpriteFull(u16 index,s16 x,s16 y,u8 size,u16 attribut,u8 link) {VDPSprite *s=vdpSpriteCache+index;s->y=y+128;s->size=size;s->link=link;s->attribut=attribut;s->x=x+128;}
static u16 add_world_entity_sprites(u16 index,u8 *entity)
'''
 suffix='''
void setup(const u8 *rom) {memcpy(memory,rom,32768);memcpy(memory+32768,rom+0x30000,16384);}
u16 test(u8 *e,u16 index,u8 *out) {u16 result;memset(vdpSpriteCache,0xa5,sizeof(vdpSpriteCache));result=add_world_entity_sprites(index,e);memcpy(out,vdpSpriteCache,sizeof(vdpSpriteCache));return result;}
'''
 for tag in ['baseline','current']:
  text=subprocess.check_output(['git','show','25b70e0:megadrive/src/actors.c'],cwd=ROOT).decode() if tag=='baseline' else (ROOT/'megadrive/src/actors.c').read_text();bodies[tag]=extract(text);src=folder/(tag+'.c');src.write_bytes((prefix+bodies[tag]+suffix).encode());dll=folder/(tag+'.dll');subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror',str(src),'-o',str(dll)],env=env,check=True);lib=c.CDLL(str(dll));lib.test.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8)];lib.test.restype=c.c_uint16;libs.append(lib)
 rom=(ROOT/'input/original.sms').read_bytes();data=(c.c_uint8*len(rom)).from_buffer_copy(rom)
 for lib in libs:lib.setup(data)
 rng=random.Random(0x09ee_0270);cases=emitted=0;tables=[0x84ce,0x84e1,0x90cc,0x80a0,0x2acd,0x3d8d]
 for i in range(24000):
  before=bytearray(rng.randbytes(48));table=tables[i%len(tables)];before[8:10]=table.to_bytes(2,'little');before[10]=rng.randrange(4);before[11]=rng.randrange(6);before[0]=i%101;index=i%65;outs=[]
  for lib in libs:
   e=(c.c_uint8*48).from_buffer_copy(before);out=(c.c_uint8*640)();n=lib.test(e,index,out);outs.append((n,bytes(e),bytes(out)))
  assert outs[0]==outs[1],(i,table,index);cases+=1;emitted+=outs[1][0]>index
 assert emitted
 r=dict(passed=True,cases=cases,emitted_cases=emitted,baseline_commit='25b70e0',source_sha256=sha(rom),production_body_sha256={k:sha(v.encode()) for k,v in bodies.items()},scope='Actual baseline/current emitter bodies compiled on host, full640 cache bytes/48 entity bytes/count exact. Original low ROM and bank12 descriptors, varied pose/direction/base/type/X/Y/index. Host union layout models the MD size/link word. Native pixels are checked separately.')
 (ROOT/'analysis/sprite_cache_cursor_host_report.json').write_bytes((json.dumps(r,indent=2)+'\n').encode());print(r)
if __name__=='__main__':main()
