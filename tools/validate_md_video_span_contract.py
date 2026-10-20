"""Native 68000 contiguous1..4tile DMA token bounds and retry/error contracts."""
import argparse
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
    parser=argparse.ArgumentParser();parser.add_argument('--variant',default='');parser.add_argument('--window-probe',action='store_true');parser.add_argument('--refresh-profile',action='store_true');parser.add_argument('--hidden-profile',action='store_true');parser.add_argument('--hidden-preflight',action='store_true');parser.add_argument('--preflight-prepared',action='store_true');parser.add_argument('--hidden-grant',action='store_true');args=parser.parse_args();assert not args.hidden_grant or (args.hidden_profile and not args.hidden_preflight);assert not args.hidden_preflight or args.hidden_profile;assert not args.preflight_prepared or args.hidden_preflight
    assert not args.variant or re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',args.variant)
    suffix='-'+args.variant if args.variant else ''
    folder=ROOT/('validation/md-video-span-contract'+suffix);src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    main=MAIN
    if args.window_probe:
        main=main.replace('#include "md_z80_video_span.h"','#include "md_z80_video_span.h"\nu8 gaw_span_window_probe(u8);')
        main=main.replace(' gaw_done=1;', ' for(n=0;n<256;n++) check((gaw_span_window_probe((u8)n)!=0)==((n>=224 && n<=228)||(n>=235 && n<=252)));\n gaw_done=1;')
    if args.refresh_profile:
        helpers='''static __attribute__((noinline)) void retry_refresh(MdZ80PsgMailbox *mb,MdZ80VideoSpan *job,u8 wanted) {save();check(md_z80_video_span_try_refresh(mb,job)==wanted && same());}
static __attribute__((noinline)) void invalid_refresh(const u32 *source,u16 tile,u16 count) {save();check(md_z80_video_span_prepare_refresh(&token,source,tile,count)==MD_Z80_PSG_INVALID && same());}
'''
        main=main.replace('#include "md_z80_video_span.h"','#include "md_z80_video_span.h"\nu8 gaw_span_window_large_probe(u8);')
        main=main.replace('int main(bool reset)',helpers+'int main(bool reset)')
        main=main.replace(' gaw_done=1;', ''' token.ready=0xd580;mailbox.stamp.error=0;mailbox.grant=0;
 retry_refresh(0,&token,MD_Z80_PSG_INVALID);retry_refresh(&mailbox,0,MD_Z80_PSG_INVALID);
 mailbox.stamp.ready=1;retry_refresh(&mailbox,&token,MD_Z80_PSG_INVALID);
 mailbox.stamp.ready=0;retry_refresh(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.stamp.ready=3;retry_refresh(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.stamp.error=1;retry_refresh(&mailbox,&token,MD_Z80_PSG_FAULT);
 {u16 k;for(k=1;k<=8;k++) {
  u32 address=0x20000UL-(u32)k*32;
  check(md_z80_video_span_prepare_refresh(&token,(const u32*)address,2048-k,k)==MD_Z80_PSG_OK);
  check(token.source_low==(0x9500|(256-k*16)) && token.source_mid==0x96ff && token.source_high==0x9700 && token.length_low==0x9300+k*16 && token.ready==0xd600 && token.command==VDP_DMA_VRAM_ADDR(65536UL-(u32)k*32));
  invalid_refresh((const u32*)(address+2),2048-k,k);invalid_refresh((const u32*)0x1000,2049-k,k);
 }
 invalid_refresh((const u32*)0x1000,0,0);invalid_refresh((const u32*)0x1000,0,9);
 }
 mailbox.stamp.error=0;retry(&mailbox,&token,MD_Z80_PSG_INVALID);
 retry_refresh(&mailbox,&token,MD_Z80_PSG_INVALID);
 mailbox.stamp.ready=7;retry_refresh(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.grant=0xc1;mailbox.busy=1;retry_refresh(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.busy=0;mailbox.head=1;mailbox.tail=0;retry_refresh(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.head=0;mailbox.grant=0;mailbox.stamp.error=1;
 retry_refresh(&mailbox,&token,MD_Z80_PSG_FAULT);
 invalid_refresh(0,0,8);invalid_refresh((const u32*)0x1001,0,8);invalid_refresh((const u32*)&token,0,8);
 save();check(md_z80_video_span_prepare_refresh(0,(const u32*)0x1000,0,8)==MD_Z80_PSG_INVALID && same());
 save();check(md_z80_video_span_prepare_refresh((MdZ80VideoSpan*)((u8*)&token+1),(const u32*)0x1000,0,8)==MD_Z80_PSG_INVALID && same());
 VDP_setScreenWidth320();invalid_refresh((const u32*)0x1000,0,8);VDP_setScreenWidth256();
 VDP_setScreenHeight240();if(SYS_isPAL()) invalid_refresh((const u32*)0x1000,0,8);else check(VDP_getScreenHeight()==224);VDP_setScreenHeight224();
 for(n=0;n<256;n++) check((gaw_span_window_large_probe((u8)n)!=0)==((n>=224 && n<=228)||(n>=235 && n<=251)));
 gaw_done=1;''')
    if args.hidden_profile:
        helper='static __attribute__((noinline)) void retry_hidden(MdZ80PsgMailbox *mb,MdZ80VideoSpan *job,u8 wanted) {save();check(md_z80_video_span_try_hidden(mb,job)==wanted && same());}\n'
        main=main.replace('int main(bool reset)',helper+'int main(bool reset)')
        main=main.replace(' gaw_done=1;',''' mailbox.stamp.error=0;mailbox.stamp.ready=0;mailbox.grant=0;
 check(md_z80_video_span_prepare_refresh(&token,(const u32*)0x1000,0,4)==MD_Z80_PSG_OK);
 retry_hidden(0,&token,MD_Z80_PSG_INVALID);retry_hidden(&mailbox,0,MD_Z80_PSG_INVALID);
 retry_hidden(&mailbox,(MdZ80VideoSpan*)((u8*)&token+1),MD_Z80_PSG_INVALID);
 retry_hidden(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.stamp.ready=1;retry_hidden(&mailbox,&token,MD_Z80_PSG_INVALID);
 mailbox.stamp.ready=3;retry_hidden(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.stamp.error=1;retry_hidden(&mailbox,&token,MD_Z80_PSG_FAULT);mailbox.stamp.error=0;
 VDP_setEnable(TRUE);retry_hidden(&mailbox,&token,MD_Z80_PSG_INVALID);VDP_setEnable(FALSE);
 check(md_z80_video_span_prepare_refresh(&token,(const u32*)0x1000,0,8)==MD_Z80_PSG_OK);
 retry_hidden(&mailbox,&token,MD_Z80_PSG_INVALID);
 check(md_z80_video_span_prepare_refresh(&token,(const u32*)0x1000,0,4)==MD_Z80_PSG_OK);
 retry_hidden(&mailbox,&token,MD_Z80_PSG_WAIT);
 gaw_done=1;''')
    if args.hidden_grant:
        needle='mailbox.stamp.ready=3;retry_hidden(&mailbox,&token,MD_Z80_PSG_WAIT);'
        assert main.count(needle)==1
        main=main.replace(needle,'mailbox.stamp.ready=3;retry_hidden(&mailbox,&token,MD_Z80_PSG_INVALID);mailbox.stamp.ready=7;retry_hidden(&mailbox,&token,MD_Z80_PSG_WAIT);')
        main=main.replace('md_z80_video_span_try_hidden(', 'md_z80_video_span_try_hidden_grant(')
    if args.hidden_preflight:
        main=main.replace(' gaw_done=1;',''' *(volatile u16*)0xc00010=0x38;
 mailbox.grant=1;mailbox.stamp.ready=3;mailbox.stamp.error=0;
 mailbox.stamp.v=(u8)((*(volatile u16*)0xc00008>>8)-8);
 retry_hidden(&mailbox,&token,MD_Z80_PSG_WAIT);
 mailbox.stamp.v=229;retry_hidden(&mailbox,&token,MD_Z80_PSG_WAIT);
 gaw_done=1;''')
        main=main.replace('md_z80_video_span_try_hidden(', 'md_z80_video_span_try_hidden_preflight'+('_prepared' if args.preflight_prepared else '')+'(')
    (src/'main.c').write_bytes(main.encode())
    for name in ['md_z80_video_span.c','md_z80_video_span.h']:
        text='#include "../../../megadrive/src/'+name+'"\n'
        if name.endswith('.c') and args.window_probe:text+='u8 gaw_span_window_probe(u8 v) {return in_window(v); }\n'
        if name.endswith('.c') and args.refresh_profile:text+='u8 gaw_span_window_large_probe(u8 v) {return in_window_mask(v,0x0ffff81fUL); }\n'
        (src/name).write_text(text)
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
        assert observed['done'] and observed['checks']==((300 if args.window_probe else 44)+(309 if args.refresh_profile else 0)+(13 if args.hidden_profile else 0)+(2 if args.hidden_preflight else 0)+(1 if args.hidden_grant else 0)) and not observed['failures'],observed
        markers=[(i,e[2]) for i,e in enumerate(events) if e[0]==3 and 0x34<=e[2]<=0x37]
        assert [x[1] for x in markers]==list(range(0x34,0x38))
        for a,b in [(markers[0][0],markers[1][0]),(markers[2][0],markers[3][0])]:
            assert not any(e[0] in (4,7) for e in events[a+1:b]),'Early rejection unexpectedly reads beam or takes bus'
        if args.window_probe or args.refresh_profile or args.hidden_profile:
            end=next(i for i,e in enumerate(events) if e[0]==3 and e[2]==0x38) if args.hidden_preflight else len(events)
            assert not any(e[0] in (4,7) for e in events[markers[-1][0]+1:end]),'Window/profile checks unexpectedly read beam or take bus'
            if args.hidden_preflight:
                assert not any(e[0]==7 for e in events[end+1:]),'Stale preflight took the bus'
                assert sum(e[0]==4 for e in events[end+1:])>=3,'Stale probes did not run'
        raw=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        results.append(dict(region=region,**observed,events_sha256=sha(raw)));print(results[-1],flush=True)
    report=dict(hidden_grant=args.hidden_grant,preflight_prepared=args.preflight_prepared,hidden_preflight=args.hidden_preflight,hidden_profile=args.hidden_profile,window_probe=args.window_probe,refresh_profile=args.refresh_profile,kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['md_z80_video_span.c','md_z80_video_span.h']},results=results,limits=['Native token layout, invalid preparation atomicity and pre-beam WAIT/FAULT retention only. Successful DMA consumption and held-bus safety require separate live capture. No production renderer or waveform proof.'])
    (ROOT/('analysis/md_video_span_contract'+suffix.replace('-','_')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
