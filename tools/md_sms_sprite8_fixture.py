"""Captured SMS renderer inputs for the native sprite stream, never game-state injection."""
import hashlib,json
from pathlib import Path
from md_z80_source_video_fixture import convert_sms_patterns
ROOT=Path(__file__).resolve().parents[1]
def inputs(case=0):
 folder=ROOT/'validation/sms-vertical-check';p=json.loads((folder/'capture.json').read_bytes());assert p['rom_sha256']==hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest()
 v=(folder/'vram_03120.bin').read_bytes();regs=(folder/'vdp_regs_03120.bin').read_bytes();base=(regs[5]&126)*128;sat=v[base:base+64]+v[base+128:base+256];r0,r1,r6=regs[0],regs[1],regs[6]
 if case==5:
  from validate_source_sprite_scene import scene_seed,scene_sat
  rom=(ROOT/'input/original.sms').read_bytes();sat=scene_sat(scene_seed(),rom[0x30000:0x34000])
 elif case:
  original=sat;sat=bytearray([208]*192)
  if case==1:
   r0|=40
   for i in range(18):
    sat[i]=31 if i<9 else 63;sat[64+i*2]=(0 if i<8 else 88 if i==8 else 8+(i-9)*8 if i<17 else 216);sat[65+i*2]=original[65+(i%17)*2]
  elif case==2:
   for i,(y,x) in enumerate([(248,255),(255,0)]):sat[i]=y;sat[64+i*2]=x;sat[65+i*2]=original[65+i*2]
  elif case==4:
   for i in range(64):sat[i]=167;sat[64+i*2]=(i%8)*32;sat[65+i*2]=original[65+(i%17)*2]
  else:assert case==3
  sat=bytes(sat)
 return sat,v[:16384],(r0,r1,r6)
def assets(case=0):
 sat,vram,regs=inputs(case);packed=convert_sms_patterns(vram)
 legend=[n*0x11111111 for n in range(16) for row in range(8)]
 text=('static const u8 sprite8_sat[]={'+','.join(map(str,sat))+'};\nstatic const u8 sprite8_regs[]={'+','.join(map(str,regs))+'};\nstatic const u32 sprite8_patterns[]={'+','.join('0x'+packed[n:n+4].hex()+'UL' for n in range(0,16384,4))+'};\nstatic const u32 sprite8_legend[]={'+','.join(hex(v)+'UL' for v in legend)+'};\n')
 if case==5:
  from validate_source_sprite_scene import scene_seed
  text=text.replace('static const u8 sprite8_sat[]={'+','.join(map(str,sat))+'};','static u8 sprite8_sat[192];')
  for name,data in [('seed',scene_seed()),('actor_bank',(ROOT/'input/original.sms').read_bytes()[0x30000:0x34000])]:text+='static const u8 sprite8_'+name+'[]={'+','.join(map(str,data))+'};\n'
 return text
HELPER=r'''
static MdSmsSprite8Stream sprite8;
volatile u32 gaw_sprite8_jobs,gaw_sprite8_pattern_jobs,gaw_sprite8_sat_jobs,gaw_sprite8_readback_words,gaw_sprite8_readback_errors;
volatile u16 gaw_sprite8_count,gaw_sprite8_overflow,gaw_sprite8_poisoned;
static void sprite8_setup(void) {
 u16 n;VDP_loadTileData(sprite8_legend,600,16,CPU);
 for(n=0;n<16;n++) VDP_setTileMapXY(BG_A,0x2000|(600+n),n,27);
}
static void sprite8_flush(void) {
 u8 status;u32 spins=0;u16 n;
 if(session_failed) return;
 *(volatile u16*)0xc00010=0x2c;
 if(SPRITE_CASE==3) {
  VDP_setAutoInc(2);*(volatile u32*)VDP_CTRL_PORT=VDP_WRITE_VRAM_ADDR(VDP_getSpriteListAddress());
  for(n=0;n<64;n++) {*(volatile u16*)VDP_DATA_PORT=200;*(volatile u16*)VDP_DATA_PORT=n==63?0:n+1;*(volatile u16*)VDP_DATA_PORT=0x2000|601;*(volatile u16*)VDP_DATA_PORT=128;}
  gaw_sprite8_poisoned++;
 }
 status=md_sms_sprite8_stream_begin(&sprite8,sprite8_sat,sprite8_patterns,sprite8_regs[0],sprite8_regs[1],sprite8_regs[2],1024,1);
 if(status) {fault(0xe00|status);return;}
 gaw_sprite8_count=sprite8.frame.count;gaw_sprite8_overflow=sprite8.frame.overflow;
 while(!sprite8.done && !session_failed && ++spins<1000000UL) {
  status=md_sms_sprite8_stream_step(&sprite8,&mailbox);
  if(status==MD_Z80_PSG_OK) {gaw_sprite8_jobs++;if(sprite8.last_kind==1) gaw_sprite8_pattern_jobs++;else gaw_sprite8_sat_jobs++;}
  else if(status!=MD_Z80_PSG_WAIT) fault(0xe20|status);
  work();
 }
 gaw_sprite8_readback_words+=sprite8.readback_words;gaw_sprite8_readback_errors+=sprite8.readback_errors;
 if(!sprite8.done) fault(0xe10);
 *(volatile u16*)0xc00010=0x2d;
}
'''
def instrument(main,case=0):
 main=main.replace('#include "md_class0_video_stream.h"','#include "md_class0_video_stream.h"\n#include "md_sms_sprite8_stream.h"\n#include "sprite8-input.h"')
 needle='static void video_setup(void)';assert main.count(needle)==1;main=main.replace(needle,HELPER.replace('SPRITE_CASE',str(case))+needle)
 needle='gaw_video_updates=1;VDP_setEnable(TRUE);';assert main.count(needle)==1;main=main.replace(needle,'gaw_video_updates=1;sprite8_setup();VDP_setEnable(TRUE);')
 needle=' video_flush();';assert main.count(needle)==1;main=main.replace(needle,needle+'sprite8_flush();')
 if case==5:
  main=main.replace('#include "sprite8-input.h"','#include "sprite8-input.h"\n#include "source_sprite_scene.h"\nstatic u8 sprite8_game_ram[8192];volatile u16 gaw_sprite8_builds;')
  needle=' *(volatile u16*)0xc00010=0x2c;';assert main.count(needle)==1
  main=main.replace(needle,needle+'\n {SourceSpriteSceneOutput result;memcpy(sprite8_game_ram,sprite8_seed,8192);if(!source_sprite_scene(sprite8_game_ram,sprite8_actor_bank,&result)) {fault(0xe40);return;}memcpy(sprite8_sat,sprite8_game_ram+0x1d40,192);gaw_sprite8_builds++;}')
 return main
def validate(folder,region,frame,observed,vram,regs,case=0):
 from validate_sms_sprite8 import source_plane
 sat,patterns,r=inputs(case);count=next((i for i,y in enumerate(sat[:64]) if y==208),64);plane,overflow,_=source_plane(sat,patterns,r[0],r[2])
 assert observed['sprite8_count']==count and bool(observed['sprite8_overflow'])==overflow
 jobs=(count+3)//4;assert observed['sprite8_jobs']==48*(jobs+4) and observed['sprite8_pattern_jobs']==48*jobs and observed['sprite8_sat_jobs']==192
 assert observed['sprite8_readback_words']==48*(count*16+256) and not observed['sprite8_readback_errors']
 assert observed['sprite8_poisoned']==(48 if case==3 else 0)
 if case==5:assert observed['sprite8_builds']==48
 physical=bytes(vram[n^1] for n in range(65536));base=(regs[5]&127)<<9
 # Verify the native SAT chain and decode clone pixels independently.
 entries=[physical[base+i*8:base+i*8+8] for i in range(64)]
 for i in range(count):
  assert int.from_bytes(entries[i][4:6],'big')==(0x2000|1024+i)
  assert int.from_bytes(entries[i][2:4],'big')==(i+1 if i+1<count else 0)
 assert physical[base+count*8:base+512]==bytes((64-count)*8)
 if not count:assert physical[base:base+512]==bytes(512)
 actual=bytearray(256*192)
 for y in range(192):
  eligible=[];index=0
  for _ in range(64):
   e=entries[index];top=(int.from_bytes(e[:2],'big')&511)-144
   if top<=y<top+8:eligible.append((e,y-top))
   link=e[3]&127
   if not link:break
   assert link<64;index=link
  for e,row in reversed(eligible[:16]):
   x=(int.from_bytes(e[6:8],'big')&511)-128;tile=int.from_bytes(e[4:6],'big')&2047;word=int.from_bytes(physical[tile*32+row*4:tile*32+row*4+4],'big')
   for c in range(8):
    xx=x+c;color=(word>>((7-c)*4))&15
    if color and 0<=xx<256:actual[y*256+xx]=color
 assert bytes(actual)==plane,(region,'physical sprite-plane mismatch')
 result=dict(case=case,sprites=count,overflow=overflow,plane_sha256=hashlib.sha256(plane).hexdigest(),readback_words=observed['sprite8_readback_words'],input_sat_sha256=hashlib.sha256(sat).hexdigest(),input_patterns_sha256=hashlib.sha256(patterns).hexdigest())
 if case==5:
  from validate_source_sprite_scene import scene_seed
  result.update(native_actor_sat=True,scene_seed_sha256=hashlib.sha256(scene_seed()).hexdigest(),scene_bank_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()[0x30000:0x34000]).hexdigest())
 return result
