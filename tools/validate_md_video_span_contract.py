"""Native 68000 contiguous1..4tile DMA token bounds and retry/error contracts."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from run_core import run

ROOT=Path(__file__).resolve().parents[1]
MAIN=r'''
#include <genesis.h>
#include "md_z80_video_span.h"
volatile u32 gaw_checks,gaw_failures;
volatile u16 gaw_done;
static MdZ80VideoSpan token;
static MdZ80PsgMailbox mailbox;
static u8 saved[sizeof(token)];
static void check(u16 pass) {gaw_checks++;if(!pass) gaw_failures++;}
static void save(void) {u16 n;for(n=0;n<sizeof(token);n++) saved[n]=((u8*)&token)[n];}
static u16 same(void) {u16 n;for(n=0;n<sizeof(token);n++) if(saved[n]!=((u8*)&token)[n]) return FALSE;return TRUE;}
static __attribute__((noinline)) void invalid(MdZ80VideoSpan *job,const u32 *source,u16 tile) {
 save();check(md_z80_video_span_prepare(job,source,tile,4)==MD_Z80_PSG_INVALID && same());
}
static __attribute__((noinline)) void invalid_count(const u32 *source,u16 tile,u16 count) {
 save();check(md_z80_video_span_prepare(&token,source,tile,count)==MD_Z80_PSG_INVALID && same());
}
static __attribute__((noinline)) void retry(MdZ80PsgMailbox *mb,MdZ80VideoSpan *job,u8 wanted) {
 save();check(md_z80_video_span_try(mb,job)==wanted && same());
}
int main(bool reset) {
 u16 n;(void)reset;
 SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 for(n=0;n<sizeof(token);n++) ((u8*)&token)[n]=0xa5;
 *(volatile u16*)0xc00010=0x34;
 check(sizeof(token)==14);
 invalid(0,(const u32*)0x1000,1);
 invalid((MdZ80VideoSpan*)((u8*)&token+1),(const u32*)0x1000,1);
 invalid((MdZ80VideoSpan*)0x1000,(const u32*)0x2000,1);
 invalid((MdZ80VideoSpan*)0xfffff6,(const u32*)0x1000,1);
 invalid(&token,0,1);invalid(&token,(const u32*)0x1001,1);
 invalid(&token,(const u32*)0x1ffe2,1);invalid(&token,(const u32*)0x3fff0,1);
 invalid(&token,(const u32*)0x1000,2048);
 invalid(&token,(const u32*)&token,1);
 invalid(&token,(const u32*)((u32)&token-30),1);
 invalid(&token,(const u32*)((u8*)&token+10),1);
 *(volatile u16*)0xc00010=0x35;
 VDP_setScreenWidth320();invalid(&token,(const u32*)0x1000,1);VDP_setScreenWidth256();
 VDP_setScreenHeight240();if(SYS_isPAL()) invalid(&token,(const u32*)0x1000,1);else check(VDP_getScreenHeight()==224);VDP_setScreenHeight224();
 *(volatile u16*)0xc00010=0x36;
 check(md_z80_video_span_prepare(&token,(const u32*)0x1ffe0,2047,1)==MD_Z80_PSG_OK);
 check(token.source_low==0x95f0 && token.source_mid==0x96ff && token.source_high==0x9700 && token.command==VDP_DMA_VRAM_ADDR(65504UL) && token.ready==0xd580 && token.length_low==0x9310);
 check(md_z80_video_span_prepare(&token,(const u32*)0x20000,0,4)==MD_Z80_PSG_OK);
 check(token.source_low==0x9500 && token.source_mid==0x9600 && token.source_high==0x9701 && token.command==VDP_DMA_VRAM_ADDR(0) && token.length_low==0x9340);
 {static const u16 lows[]={0x95f0,0x95e0,0x95d0,0x95c0};u16 k;
  for(k=1;k<=4;k++) {
   u32 address=0x20000UL-(u32)k*32;
   check(md_z80_video_span_prepare(&token,(const u32*)address,2048-k,k)==MD_Z80_PSG_OK);
   check(token.source_low==lows[k-1] && token.source_mid==0x96ff && token.source_high==0x9700 && token.length_low==0x9300+k*16 && token.command==VDP_DMA_VRAM_ADDR(65536UL-(u32)k*32));
   invalid_count((const u32*)(address+2),2048-k,k);
   invalid_count((const u32*)0x1000,2049-k,k);
  }
  invalid_count((const u32*)0x1000,0,0);invalid_count((const u32*)0x1000,0,5);
 }
 retry(0,&token,MD_Z80_PSG_INVALID);
 retry(&mailbox,0,MD_Z80_PSG_INVALID);
 retry(&mailbox,(MdZ80VideoSpan*)((u8*)&token+1),MD_Z80_PSG_INVALID);
 retry(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.stamp.ready=1;retry(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.stamp.error=1;retry(&mailbox,&token,MD_Z80_PSG_FAULT);
 mailbox.stamp.error=0;token.ready=0;retry(&mailbox,&token,MD_Z80_PSG_INVALID);
 *(volatile u16*)0xc00010=0x37;
 gaw_done=1;while(TRUE) {}return 0;
}
'''

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    folder=ROOT/'validation/md-video-span-contract';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    (src/'main.c').write_bytes(MAIN.encode())
    for name in ['md_z80_video_span.c','md_z80_video_span.h']:
        (src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2500:]
    symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_z80_psg_io_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    results=[]
    for region,lines in [('ntsc',262),('pal',313)]:
        observed={};events=[];dll.gaw_io_reset(0)
        def observe(frame,ram):
            count=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
            events.extend([[int(ptr[n*4]),(frame-1)*lines*3420+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(count)]);dll.gaw_io_reset(1)
            def val(name,width):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+i)&65535)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=val('gaw_done',2),checks=val('gaw_checks',4),failures=val('gaw_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',120,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed['done'] and observed['checks']==44 and not observed['failures'],observed
        markers=[(i,e[2]) for i,e in enumerate(events) if e[0]==3 and 0x34<=e[2]<=0x37]
        assert [x[1] for x in markers]==list(range(0x34,0x38))
        for a,b in [(markers[0][0],markers[1][0]),(markers[2][0],markers[3][0])]:
            assert not any(e[0] in (4,7) for e in events[a+1:b]),'Early rejection unexpectedly reads beam or takes bus'
        raw=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        results.append(dict(region=region,**observed,events_sha256=sha(raw)));print(results[-1],flush=True)
    report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['md_z80_video_span.c','md_z80_video_span.h']},results=results,limits=['Native token layout, invalid preparation atomicity and pre-beam WAIT/FAULT retention only. Successful DMA consumption and held-bus safety require separate live capture. No production renderer or waveform proof.'])
    (ROOT/'analysis/md_video_span_contract_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
