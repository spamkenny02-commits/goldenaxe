"""Compile exact old/new production row-mask functions and compare their outputs."""
import ctypes,json,os,subprocess
from run_core import ROOT
from archive_lossless_evidence import sha

def main():
    old=subprocess.check_output(['git','show','56c6131:megadrive/src/main.c'],cwd=ROOT).decode().replace('\r\n','\n');new=(ROOT/'megadrive/src/main.c').read_text()
    def body(text,prefix):
        start=text.index('static void mask_world_sms_sprite_rows(u16 count)');end=text.index('\nstatic u16 dungeon_bitmap_pending;',start)
        out=text[start:end]
        for name in ['mask_world_sms_sprite_rows','terminate_world_sprite_list','prepare_world_sms_sprite_overflow']:out=out.replace(name,prefix+name)
        return out
    folder=ROOT/'validation/sprite-mask-v0226';folder.mkdir(exist_ok=True)
    code=r'''
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef int16_t s16;typedef uint32_t u32;typedef u8 bool;
#define TRUE 1
#define FALSE 0
typedef struct {u16 y,x,size_link,attribut;u8 link;} Sprite;
typedef struct {const u32 *source;u16 tile,count;} WorldTileJob;
typedef struct {u16 tile,index;u32 words[8];} Upload;
static Sprite vdpSpriteCache[64];static WorldTileJob world_tile_jobs[68];
static u32 world_clone_tiles[65][8],patterns[512*8];static Upload uploads[65];
static u16 world_tile_job_count,world_video_next_overflow,world_sms_sprite_prepared_overflow,upload_count;
static u8 world_video_preparing;static volatile u32 control;static volatile u16 data=0xa55a;
#define VDP_DATA_PORT (&data)
#define VDP_CTRL_PORT (&control)
#define VDP_READ_VRAM_ADDR(x) (x)
static void VDP_setAutoInc(u16 n) {(void)n;}
static void VDP_setSpriteTile(u16 n,u16 tile) {vdpSpriteCache[n].attribut=(vdpSpriteCache[n].attribut&0xf800)|tile;}
static void world_clone_upload(const u32 *source,u16 tile,u16 index) {
 Upload *u=uploads+upload_count++;u->tile=tile;u->index=index;memcpy(u->words,source,32);
 if(world_video_preparing) {WorldTileJob *j=world_tile_jobs+world_tile_job_count++;memcpy(world_clone_tiles[index],source,32);j->source=world_clone_tiles[index];j->tile=tile;j->count=1;}
}
'''+body(old,'old_')+body(new,'new_')+r'''
unsigned cases,failure;
unsigned check(void) {
 Sprite initial[64],expected[64];Upload eu[65];WorldTileJob ej[68];u32 ec[65][8],control_old;
 unsigned count,raw,layout,mode,i,jobs,ecount,of,prepared;
 for(i=0;i<512*8;i++)patterns[i]=0x12345678u^(i*0x10204081u);
 cases=failure=0;
 for(count=0;count<=64;count++)for(raw=0;raw<256;raw++)for(layout=0;layout<4;layout++)for(mode=0;mode<2;mode++) {
  memset(initial,0,sizeof(initial));
  for(i=0;i<64;i++) {
   unsigned y=layout==0?raw:layout==1?(raw+i%5)&255:layout==2?(raw*31+i*13+(i*i)%29)&255:(i==count/2?208:raw);
   initial[i].y=145+y;initial[i].x=128+(i*17)%256;initial[i].attribut=0xa000|(16+(i*13)%512);initial[i].link=i+1;
  }
  memcpy(vdpSpriteCache,initial,sizeof(initial));memset(uploads,0,sizeof(uploads));memset(world_clone_tiles,0x55,sizeof(world_clone_tiles));memset(world_tile_jobs,0,sizeof(world_tile_jobs));world_video_preparing=mode;upload_count=0;control=0;
  world_tile_job_count=raw%5;world_sms_sprite_prepared_overflow=0x33;
  for(i=0;i<world_tile_job_count;i++){world_tile_jobs[i].source=patterns+i*16;world_tile_jobs[i].tile=16+i*13;world_tile_jobs[i].count=2;}
  old_prepare_world_sms_sprite_overflow(count);memcpy(expected,vdpSpriteCache,sizeof(expected));memcpy(eu,uploads,sizeof(eu));memcpy(ej,world_tile_jobs,sizeof(ej));memcpy(ec,world_clone_tiles,sizeof(ec));jobs=world_tile_job_count;ecount=upload_count;of=world_video_next_overflow;prepared=world_sms_sprite_prepared_overflow;control_old=control;
  memcpy(vdpSpriteCache,initial,sizeof(initial));memset(uploads,0,sizeof(uploads));memset(world_clone_tiles,0x55,sizeof(world_clone_tiles));memset(world_tile_jobs,0,sizeof(world_tile_jobs));world_video_preparing=mode;upload_count=0;control=0;
  world_tile_job_count=raw%5;world_sms_sprite_prepared_overflow=0x33;
  for(i=0;i<world_tile_job_count;i++){world_tile_jobs[i].source=patterns+i*16;world_tile_jobs[i].tile=16+i*13;world_tile_jobs[i].count=2;}
  new_prepare_world_sms_sprite_overflow(count);cases++;
  if(memcmp(expected,vdpSpriteCache,sizeof(expected)) || memcmp(eu,uploads,sizeof(eu)) || memcmp(ej,world_tile_jobs,sizeof(ej)) || memcmp(ec,world_clone_tiles,sizeof(ec)) || jobs!=world_tile_job_count || ecount!=upload_count || of!=world_video_next_overflow || prepared!=world_sms_sprite_prepared_overflow || control_old!=control) {failure=cases;return 0;}
 }
 return cases;
}
'''
    source=folder/'mask.c';source.write_text(code);env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared',str(source),'-o',str(folder/'mask.dll')],env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=ctypes.CDLL(str(folder/'mask.dll'));count=dll.check();assert count==65*256*4*2,ctypes.c_uint.in_dll(dll,'failure').value
    result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),passed=True,compiled_c_cases=count,reference_commit='56c6131',source_sha256=sha((ROOT/'megadrive/src/main.c').read_bytes()),scope='Exact old/new production functions compiled on host, with SDK IO stubs: all0..64 sprite counts,256 encoded Y values,four layouts,two preparation modes,0..4 base pattern jobs. SAT attributes/links,full clone pixels,queued DMA records,overflow status and final read command match. Source reads return a constant word except varied queued pattern rows; actual68000/VDP/cycle integration is separate.')
    (ROOT/'analysis/sprite_mask_equivalence_v0226_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
