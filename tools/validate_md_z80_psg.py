"""Actual native source loader/reader/FIFO -> independently paced Z80 PSG IO."""
import contextlib
import argparse
from bisect import bisect_right
import ctypes as c
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_md_psg_replay import MAIN
from validate_queued_loading import wrapper
from validate_native_room_finish import MODULES
from validate_reader_timing import MODULES as TIMED_MODULES

OUTPUT=r'''
static MdZ80PsgMailbox mailbox;static MdServiceClock timer;static MdZ80PsgProducer producer;
volatile u32 gaw_z80_failure_code;
static SourceMdPsgBlock blocks[128];static u32 full_waits;
volatile u32 gaw_z80_foreground,gaw_z80_work_count;
volatile u32 gaw_z80_queue_full,gaw_z80_grant_wait,gaw_z80_wrap_head,gaw_z80_wrap_tail,gaw_z80_refresh_counter;
static void work(void) {gaw_z80_foreground=(gaw_z80_foreground<<1)^((gaw_z80_foreground&0x80000000UL)?0x04c11db7UL:0);gaw_z80_work_count++;}
static void run_z80(u16 count,u16 marker,u32 epoch) {
 u16 n,used;u8 status;u32 spins=0;
 if(marker==88) used=512;
 else if(source_md_psg_plan(stream,count,blocks,128,&used)) {gaw_replay_failures++;return;}
 Z80_requestBus(TRUE);*(volatile u16*)0xc00010=marker;
 status=md_z80_psg_start(&mailbox,physical_lines,driver,sizeof(driver));if(status) {gaw_z80_failure_code=0x100|status;gaw_replay_failures++;return;}
 status=md_service_clock_init(&timer,&mailbox.stamp,physical_lines,epoch);if(status) {gaw_z80_failure_code=0x200|status;gaw_replay_failures++;return;}
 status=md_z80_psg_init(&producer,&mailbox,&timer);if(status) {gaw_z80_failure_code=0x300|status;gaw_replay_failures++;return;}
 SYS_disableInts();full_waits=0;
 while(!mailbox.stamp.ready && !mailbox.stamp.error && ++spins<100000UL) work();
 if(!mailbox.stamp.ready || mailbox.stamp.error) {gaw_z80_failure_code=0x400|mailbox.stamp.error;gaw_replay_failures++;return;}
 for(n=0;n<used;n++) {
  u16 one;SourceMdPsgBlock *next=blocks;
  if(marker!=88) next+=n;
  if(marker==88) {
   stream[0].due=epoch+(u32)physical_lines*6840+(u32)n*547200UL;stream[0].value=(u8)(99+n*13);
   if(source_md_psg_plan(stream,1,blocks,128,&one) || one!=1) {gaw_replay_failures++;break;}next=blocks;
  }
  spins=0;
  do {
   status=md_z80_psg_push(&producer,next,1);work();
   if(status==MD_Z80_PSG_FULL || status==MD_Z80_PSG_WAIT) full_waits++;
   if(status==MD_Z80_PSG_FULL) gaw_z80_queue_full++;
   if(status==MD_Z80_PSG_WAIT) gaw_z80_grant_wait++;
  } while((status==MD_Z80_PSG_FULL || status==MD_Z80_PSG_WAIT) && ++spins<100000UL);
  if(status) {gaw_z80_failure_code=0x500|status;gaw_replay_failures++;break;}
 }
 spins=0;
 while((mailbox.head!=mailbox.tail || mailbox.busy) && !mailbox.stamp.error && ++spins<1000000UL) work();
 if(mailbox.head!=mailbox.tail || mailbox.busy || mailbox.stamp.error || producer.error || producer.published!=used) {gaw_z80_failure_code=0x600|(mailbox.stamp.error<<4)|producer.error;gaw_replay_failures++;}
 if(marker==88) {gaw_z80_wrap_head=mailbox.head;gaw_z80_wrap_tail=mailbox.tail;gaw_z80_refresh_counter=producer.counter;if(mailbox.head || mailbox.tail || producer.counter==100) gaw_replay_failures++;}
 spins=0;while(md_z80_psg_stop(&mailbox)==MD_Z80_PSG_WAIT && ++spins<100000UL) work();spins=0;
 while(mailbox.stamp.ready && ++spins<100000UL) work();
 if(mailbox.stamp.ready) {gaw_z80_failure_code=0x700;gaw_replay_failures++;}
}
static void synthetic(void) {
 u16 row,n,count,spacing;u32 epoch;
 for(row=0;row<24;row++) {
  count=row<16?row+1:row-15;spacing=row<16?315:630;epoch=(row&1)?0xffff0000UL:0;
  for(n=0;n<count;n++) {stream[n].due=epoch+(u32)physical_lines*6840+(u32)row*133%3420+(u32)n*spacing;stream[n].value=(u8)(row*7+n*13);}
  run_z80(count,64+row,epoch);gaw_replay_extra_cases++;
 }
 run_z80(0,88,0xffff0000UL);gaw_replay_extra_cases++;
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',default='',help='Separate named experiment output; preserves baseline captures/report')
    parser.add_argument('--driver',default='md_psg_output_z80.asm',help='Z80 source basename inside megadrive/z80')
    parser.add_argument('--expect-prefetch',action='store_true',help='Require final stopped session to have prefetched commands (ZRAM011A)')
    parser.add_argument('--phase-offset',type=int,default=0,help='Physical replay offset in master ticks; source checkpoints stay unchanged')
    parser.add_argument('--live-loader',action='store_true',help='Run actual native loading while the Z80 consumes per-IRQ publications')
    parser.add_argument('--bare',action='store_true',help='Live-loader measurement without intermediate diagnostic state copies')
    parser.add_argument('--packets',action='store_true',help='Publish during reader packet callbacks instead of after complete source IRQs')
    parser.add_argument('--deferred',action='store_true',help='Retry pending descriptors later instead of blocking reader callbacks')
    parser.add_argument('--service',action='store_true',help='Experimental deferred pump at native source-clock function boundaries')
    parser.add_argument('--retained-fifo',action='store_true',help='Read diagnostic capture from intact bounded FIFO storage after loading')
    parser.add_argument('--bulk-drain',action='store_true',help='Use bounded native FIFO batch take in the publisher callback')
    parser.add_argument('--poll-transfer',type=int,default=0,help='Prepare once for up to this many synchronous bus-transfer attempts')
    parser.add_argument('--video',choices=['off','display','cpu','dma'],default='off',help='Visible raster; CPU uploads or retained jobs for grant-gated32byte DMA')
    parser.add_argument('--video-service',type=int,default=0,help='Pump DMA every N source-clock function boundaries (power of two)')
    parser.add_argument('--video-service-kind',choices=['all','repeat-disabled'],default='all',help='Choose all clock functions or only disabled repetition batch boundaries')
    parser.add_argument('--video-cache-pattern',action='store_true',help='Prepare each queued diagnostic pattern once, retain across WAIT')
    parser.add_argument('--video-prepared-job',action='store_true',help='Retain prepared DMA control words across retries too')
    parser.add_argument('--video-source-patterns',action='store_true',help='Upload all512 actual source pattern tiles per loader case, with native VRAM readback')
    parser.add_argument('--scene-hidden',action='store_true',help='Keep display off for whole-frame bounded H32 transfers')
    parser.add_argument('--scene-native-palette',action='store_true',help='Compile default palette path without diagnostic trace hook')
    parser.add_argument('--video-scene',action='store_true',help='Native193tile/map/palette pipeline with ROM resident assets')
    parser.add_argument('--video-source-phases',action='store_true',help='Release prefix at1706 and tail at1deb; service during actual loading')
    parser.add_argument('--video-grant-backoff',action='store_true',help='After video WAIT, retry only after the fresh grant byte changes')
    parser.add_argument('--video-source-refresh',action='store_true',help='Use the capability-gated early window with the post-publication-refresh driver')
    parser.add_argument('--video-source-during-delivery',action='store_true',help='Service actual source video while final queued audio is still being delivered')
    parser.add_argument('--video-source-no-readback',action='store_true',help='Measure uploads without per-word diagnostic VRAM reads; final tiles still checked independently')
    parser.add_argument('--video-source-tiles',type=int,default=1,choices=[1,2,3,4,8],help='Contiguous source tiles per DMA job')
    parser.add_argument('--max-frames',type=int,default=20000)
    args=parser.parse_args()
    assert not args.variant or re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',args.variant)
    assert re.fullmatch(r'[a-z0-9_]+\.asm',args.driver)
    assert 0<=args.phase_offset<3420
    assert args.variant or (not args.phase_offset and args.driver=='md_psg_output_z80.asm' and not args.expect_prefetch)
    assert not args.bare or args.live_loader
    assert not args.packets or args.live_loader
    assert not args.deferred or (args.live_loader and args.packets)
    assert not args.service or args.deferred
    assert not args.retained_fifo or (args.live_loader and args.packets)
    assert not args.bulk_drain or args.live_loader
    assert 0<=args.poll_transfer<=65535
    assert not args.poll_transfer or (args.variant and not args.deferred)
    assert args.video=='off' or (args.live_loader and args.variant)
    assert not args.video_service or (args.video=='dma' and not args.service and 1<=args.video_service<=1024 and not args.video_service&(args.video_service-1))
    assert not args.video_cache_pattern or args.video=='dma'
    assert not args.scene_hidden or args.video_scene
    assert not args.scene_native_palette or args.video_scene
    assert not args.video_scene or (args.video=='dma' and args.live_loader and args.video_service==1 and args.video_service_kind=='repeat-disabled' and args.driver=='md_psg_refresh_z80.asm' and not args.video_source_patterns and not args.video_cache_pattern and not args.video_prepared_job)
    assert not args.video_source_phases or (args.video_source_patterns and args.video_service and args.video_service_kind=='repeat-disabled' and args.video_source_tiles==4)
    assert not args.video_grant_backoff or (args.video_source_refresh and args.driver in ('md_psg_grant_z80.asm','md_psg_idle_grant_z80.asm'))
    assert not args.video_source_refresh or (args.video_source_patterns and args.video_source_tiles>1 and args.driver in ('md_psg_refresh_z80.asm','md_psg_grant_z80.asm','md_psg_idle_grant_z80.asm'))
    assert not args.video_source_during_delivery or args.video_source_patterns
    assert not args.video_source_no_readback or (args.video_source_patterns or args.video_scene)
    assert args.video_source_tiles<=4 or (args.video_source_refresh and args.driver in ('md_psg_grant_z80.asm','md_psg_idle_grant_z80.asm'))
    assert args.video_source_tiles==1 or args.video_source_patterns
    assert not args.video_source_patterns or (args.video_prepared_job and (not args.video_service or args.video_source_phases))
    assert 20000<=args.max_frames<=100000
    assert not args.video_prepared_job or args.video_cache_pattern
    assert args.video_service_kind=='all' or args.video_service
    assert not args.live_loader or (args.variant and not args.expect_prefetch and not args.phase_offset)
    suffix='-'+args.variant if args.variant else ''
    folder=ROOT/('validation/md-z80-psg'+suffix);src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    frozen=ROOT/'analysis/native-copy-pointers-v0203';m=json.loads((frozen/'manifest.json').read_text());item=m['compressed']['validation/native-planned-room-finish/kernel/src/expected.h']
    encoded=(frozen/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'];(src/'expected.h').write_bytes(raw)
    oracle=ROOT/'analysis/loading-psg-v0203';m=json.loads((oracle/'manifest.json').read_text());name='validation/loading-psg-deadlines/inputs.json';raw=(oracle/name).read_bytes();assert sha(raw)==m['files'][name];inputs=json.loads(raw)
    dates_raw=(ROOT/'analysis/loading_psg_deadlines_report.json').read_bytes();dates=json.loads(dates_raw)['results'][0]['rows'];expected=[]
    for case in range(24):
        times=[t for row in dates if row['case']==case for t in row['source_psg_master']];values=[v for row in inputs if row['case']==case for v in row['writes']];assert len(times)==len(values)<=128;expected.append((times,values))
    (src/'psg.h').write_text('static const u16 psg_counts[]={'+','.join(str(len(t)) for t,_ in expected)+'};\n'+'static const u32 psg_due[24][128]={'+','.join('{'+','.join(str(t)+'UL' for t in times)+'}' for times,_ in expected)+'};\n'+'static const u8 psg_values[24][128]={'+','.join('{'+','.join(map(str,v))+'}' for _,v in expected)+'};\n')
    main=MAIN.replace('#include "source_md_psg_replay.h"','#include "source_md_psg_replay.h"\n#include "md_z80_psg.h"\n#include "driver.h"')
    first=main.index('static void synthetic(void)');last=main.index('int main(bool hard_reset)',first);main=main[:first]+OUTPUT+main[last:]
    if args.phase_offset:
        main=main.replace('physical_lines,epoch);if(status)', 'physical_lines,epoch-'+str(args.phase_offset)+'UL);if(status)')
    if args.expect_prefetch:
        main=main.replace('if(marker==88) used=512;','if(marker==88) used=512;\n else if(marker==89) used=64;')
        main=main.replace('  spins=0;\n  do {','''  if(marker==89) {
   u16 k,total=n<32?n%16+1:n%8+1,spacing=n<32?315:630;
   for(k=0;k<total;k++) {stream[k].due=epoch+(u32)physical_lines*6840+(u32)n*136800UL+(u32)k*spacing;stream[k].value=(u8)(n*37+k*13+5);}
   if(source_md_psg_plan(stream,total,blocks,128,&one) || one!=1) {gaw_replay_failures++;break;}next=blocks;
  }
  spins=0;
  do {''')
        main=main.replace(' run_z80(0,88,0xffff0000UL);',' run_z80(0,89,0xffff0000UL);gaw_replay_extra_cases++;\n run_z80(0,88,0xffff0000UL);')
    first=main.index('  while((*(volatile u16*)0xc00008>>8)!=90) {}');last=main.index('  gaw_replay_cases++;',first)
    main=main[:first]+'''  run_z80(psg_counts[row],128+row*2+mode,epoch);
  gaw_replay_clocks[row*2+mode][0]=mailbox.head;
  gaw_replay_clocks[row*2+mode][1]=mailbox.tail;
  gaw_replay_clocks[row*2+mode][2]=full_waits;
'''+main[last:]
    main=main.replace(' synthetic();',' gaw_z80_foreground=0x8123905UL;synthetic();')
    body=wrapper()
    if args.poll_transfer and not args.live_loader:
        assert main.count('md_z80_psg_push(&producer,next,1)')==1
        main=main.replace('md_z80_psg_push(&producer,next,1)','md_z80_psg_push_poll(&producer,next,'+str(args.poll_transfer)+')')
    if args.live_loader:
        from md_live_z80_kernel import sources
        main,body=sources(args.bare,args.packets,args.deferred,args.retained_fifo,args.bulk_drain,args.poll_transfer)
        (folder/'live-kernel.py.snapshot').write_bytes((ROOT/'tools/md_live_z80_kernel.py').read_bytes())
    if args.video!='off':
        from md_z80_video_fixture import instrument
        if args.video_scene:
            from md_class0_scene_fixture import instrument as scene_instrument,assets as scene_assets
            main,body=scene_instrument(main,body,verify=not args.video_source_no_readback,proof=not args.bare,hidden=args.scene_hidden)
            (src/'scene-resident.h').write_text(scene_assets((ROOT/'input/original.sms').read_bytes()))
            (folder/'scene-fixture.py.snapshot').write_bytes((ROOT/'tools/md_class0_scene_fixture.py').read_bytes())
        elif args.video_source_patterns:
            from md_z80_source_video_fixture import instrument_source
            main,body=instrument_source(main,body,args.video_source_tiles,not args.video_source_no_readback,args.video_source_during_delivery,args.video_source_refresh,args.video_grant_backoff)
            (folder/'source-video-fixture.py.snapshot').write_bytes((ROOT/'tools/md_z80_source_video_fixture.py').read_bytes())
            if args.video_source_phases:
                from md_z80_phase_video_fixture import instrument as phase_instrument
                main,body=phase_instrument(main,body,args.video_service,not args.bare)
                (folder/'phase-video-fixture.py.snapshot').write_bytes((ROOT/'tools/md_z80_phase_video_fixture.py').read_bytes())
        else:
            main=instrument(main,args.video=='cpu',args.video=='dma',args.video_service,args.video_cache_pattern,args.video_prepared_job)
        (folder/'video-fixture.py.snapshot').write_bytes((ROOT/'tools/md_z80_video_fixture.py').read_bytes())
    (src/'main.c').write_text(main);(src/'wrapper.c').write_text(body);(folder/'validator.py.snapshot').write_bytes((ROOT/'tools/validate_md_z80_psg.py').read_bytes())
    modules=list(dict.fromkeys([n for n in MODULES if n!='source_irq_context']+TIMED_MODULES+['source_audio_fast_timed','source_irq_queue_context','source_psg_queue','source_psg_stream','source_md_psg_plan','md_service_clock','md_service_clock_start','md_z80_psg','md_z80_psg_start']))
    if args.video=='dma':
        modules.append('md_z80_video_dma')
        if args.video_source_patterns:
            modules.append('pattern_convert')
            if args.video_source_tiles>1:
                modules.append('md_z80_video_span')
                (src/'md_z80_video_span.h').write_text('#include "../../../megadrive/src/md_z80_video_span.h"\n')
            (src/'pattern_convert.h').write_text('#include "../../../megadrive/src/pattern_convert.h"\n')
        (src/'md_z80_video_dma.h').write_text('#include "../../../megadrive/src/md_z80_video_dma.h"\n')
    if args.video_scene:
        modules += ['source_class0_video','md_class0_video_stream','md_z80_video_span']
        for name in ['source_class0_video','md_class0_video_stream']:(src/(name+'.h')).write_text('#include "../../../megadrive/src/'+name+'.h"\n')
    for module in modules:
        prefix='#define source_irq_interrupt source_irq_queue_interrupt\n' if module!='source_irq_queue_context' else ''
        if args.video_scene and not args.scene_native_palette and module=='md_class0_video_stream':prefix+='#define MD_CLASS0_PALETTE_TRACE(v) (*(volatile unsigned short*)0xc00010=(v))\n'
        (src/(module+'.c')).write_text(prefix+'#include "../../../megadrive/src/'+module+'.c"\n')
    if args.service or args.video_service:
        from md_clock_service_kernel import source as service_source
        (src/'source_clock.c').write_text(service_source(bool(args.video_service),args.video_service_kind))
        (folder/'clock-service.py.snapshot').write_bytes((ROOT/'tools/md_clock_service_kernel.py').read_bytes())
    for name in ['source_room_finish.h','source_irq_queue_context.h','source_pattern_plan_generated.h','source_md_psg_replay.h','md_service_clock.h','source_md_psg_plan.h','md_z80_psg.h']:(src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    (src/'md_service_clock_hv.s').write_bytes((ROOT/'megadrive/src/md_service_clock_hv.s').read_bytes())
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    asm=ROOT/'megadrive/z80'/args.driver;(folder/'driver-source.asm.snapshot').write_bytes(asm.read_bytes())
    built=subprocess.run([str(sdk/'bin/sjasm.exe'),str(asm),str(folder/'driver.bin'),str(folder/'driver.lst')],env=env,capture_output=True,text=True);(folder/'z80-build.log').write_text(built.stdout+built.stderr);assert not built.returncode and 'Errors: 0' in built.stdout,built.stdout+built.stderr
    driver=(folder/'driver.bin').read_bytes();(src/'driver.h').write_text('static const u8 driver[]={'+','.join(map(str,driver))+'};\n')
    clock_pc=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*(?:clock|sample):\s+ld a,\(0x7f08\)',(folder/'driver.lst').read_text(),re.M)[1],16)+3
    listing=(folder/'driver.lst').read_text()
    refresh_sample=re.search(r'^\d+\s+([0-9A-F]+)[^\n]*resample:',listing,re.M)
    refresh_pc=int(refresh_sample[1],16)+3 if refresh_sample else None
    if refresh_pc is not None:
        refresh_entry=refresh_pc-3
        assert driver[refresh_entry:refresh_entry+4]==bytes.fromhex('3a087fc3')
        assert int.from_bytes(driver[refresh_entry+4:refresh_entry+6],'little')==clock_pc
        assert driver[clock_pc]==0x47  # Shared private update begins LD B,A.
        sequence_address=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*sequence:\s*db',listing,re.M)[1],16)
        publication_end=bytes([0x32])+sequence_address.to_bytes(2,'little')+bytes.fromhex('fd7700cd')+refresh_entry.to_bytes(2,'little')+bytes([0xc9])
        assert driver.count(publication_end)==1 and sum(driver.count(bytes.fromhex(x)) for x in ['fd360403','fd360407'])==1
    grant_sample=re.search(r'^\d+\s+([0-9A-F]+)[^\n]*grant_stamp:',listing,re.M)
    grant_pc=int(grant_sample[1],16)+3 if grant_sample else None
    if grant_pc is not None:
        assert driver[grant_pc-3:grant_pc+7]==bytes.fromhex('3a087f87f601fd7708c9')
        assert driver.count(bytes.fromhex('fd360407'))==1
        publication_entry=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*clock:\s+call sample',listing,re.M)[1],16)
        assert driver[grant_pc-6:grant_pc-3]==bytes([0xcd])+publication_entry.to_bytes(2,'little')
    fast_setup=re.search(r'^\d+\s+([0-9A-F]+)[^\n]*setupcounter:',listing,re.M)
    vwait_pc=hwait_pc=None
    if fast_setup:
        setup_address=int(fast_setup[1],16)
        vwait_address=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*vwait:\s+ld a,\(0x7f08\)',listing,re.M)[1],16)
        hwait_pc=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*hwait:\s+ld a,\(0x7f08\)',listing,re.M)[1],16)+3
        # Verify the control-flow signature before treating a Vwait read as a
        # counter update: CP B; JR Z to the two stores, EXX, then Hwait read.
        assert driver[vwait_address+3:vwait_address+5]==bytes([0xb8,0x28])
        displacement=driver[vwait_address+5];displacement-=256 if displacement>=128 else 0
        assert vwait_address+6+displacement==setup_address
        assert driver[setup_address]==0x22 and driver[setup_address+3]==0x32
        assert driver[setup_address+6:setup_address+10]==bytes([0xd9,0x3a,0x08,0x7f])
        counter_address=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*counter:\s*dw',listing,re.M)[1],16)
        lastv_address=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*lastv:\s*db',listing,re.M)[1],16)
        assert int.from_bytes(driver[setup_address+1:setup_address+3],'little')==counter_address
        assert int.from_bytes(driver[setup_address+4:setup_address+6],'little')==lastv_address
        assert hwait_pc==setup_address+10
        vwait_pc=vwait_address+3
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2500:]
    symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_z80_psg_io_libretro.dll';dll=c.CDLL(str(core));dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None;dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint);results=[]
    dll.gaw_z80_ram.restype=c.POINTER(c.c_uint8);dll.gaw_z80_pc.restype=c.c_uint
    for region,lines in [('ntsc',262),('pal',313)]:
        events=[];observed={};records=[];publications=[];active=[None];dll.gaw_io_reset(0);period=lines*3420
        mb=next(v for k,v in symbols.items() if k.split('.')[0]=='mailbox')&65535
        def observe(frame,ram):
            size=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data();events.extend([[int(ptr[n*4]),(frame-1)*period+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(size)]);dll.gaw_io_reset(1)
            def value(name,width,offset=0):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+offset+i)&65535)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_replay_done',2),cases=value('gaw_replay_cases',4),extra_cases=value('gaw_replay_extra_cases',4),failures=value('gaw_replay_failures',4),bytes=value('gaw_replay_bytes',4),failure_code=value('gaw_z80_failure_code',4),foreground=value('gaw_z80_foreground',4),work_count=value('gaw_z80_work_count',4),queue_full=value('gaw_z80_queue_full',4),grant_wait=value('gaw_z80_grant_wait',4),wrap_head=value('gaw_z80_wrap_head',4),wrap_tail=value('gaw_z80_wrap_tail',4),refresh_counter=value('gaw_z80_refresh_counter',4))
            if args.video!='off':observed['video_updates']=value('gaw_video_updates',4)
            if args.video=='dma':observed.update(video_requests=value('gaw_video_requests',4),video_dma_attempts=value('gaw_video_dma_attempts',4))
            if args.video_service:observed['video_service_calls']=value('gaw_video_service_calls',4)
            if args.video_cache_pattern:observed['video_pattern_preparations']=value('gaw_video_pattern_preparations',4)
            if args.video_prepared_job:observed['video_job_preparations']=value('gaw_video_job_preparations',4)
            if args.video_source_phases:
                observed['video_prefix_ready']=value('gaw_video_prefix_ready',4);observed['video_tail_ready']=value('gaw_video_tail_ready',4);observed['video_service_calls']=value('gaw_video_service_calls',4)
            if args.video_scene:
                for name in ['sources','maps','palettes','pattern_commits','map_commits','palette_commits','readback_words','readback_errors']:observed['scene_'+name]=value('gaw_scene_'+name,4)
                observed['scene_upper']=[value('gaw_scene_upper',1,n) for n in range(16)]
                observed['scene_state_checks']=0 if args.bare else value('gaw_scene_state_checks',4)
            if args.video_grant_backoff:observed['video_grant_skips']=value('gaw_video_grant_skips',4)
            if args.video_source_tiles==8:observed['video_span_sizes']=[value('gaw_video_span_sizes',4,n*4) for n in range(9)]
            if args.video_source_patterns:
                observed.update(video_sources=value('gaw_video_sources',4),video_readback_words=value('gaw_video_readback_words',4),video_readback_errors=value('gaw_video_readback_errors',4),video_dma_commits=value('gaw_video_dma_commits',4))
            for e in events[-size:] if size else []:
                if e[0]==3 and (64<=e[2]<=89 or 128<=e[2]<176):active[0]=e[2]
            stamp=[ram[(mb+i)^1] for i in range(6)]
            if active[0] is not None and stamp[4] and not stamp[0]&1:publications.append(dict(tag=active[0],frame=frame,counter=stamp[2]*256+stamp[3],v=stamp[1]))
            if observed['done'] and (args.video_source_patterns or args.video_scene):
                source_symbol=next(v for k,v in symbols.items() if k.split('.')[0]=='pixels')
                source=bytes(ram[(((source_symbol&65535)+i)&65535)^1] for i in range(16384))
                (folder/(region+'-source-patterns.bin')).write_bytes(source)
                observed['video_source_sha256']=sha(source)
                source_hash=2166136261
                for byte in source:source_hash=((source_hash^byte)*16777619)&0xffffffff
                assert source_hash==value(next(k for k in symbols if k.split('.')[0]=='output'),4,18*4)
            if observed['done']:
                observed['z80_pc']=dll.gaw_z80_pc();observed['z80_variables']=list(dll.gaw_z80_ram()[0x100:0x121]);observed['ram_sha256']=sha(bytes(ram));records[:]=[[value('gaw_replay_clocks',4,n*12+i*4) for i in range(3)] for n in range(48)]
        with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',args.max_frames,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        raw=json.dumps(dict(events=events,observed=observed,records=records,publications=publications),separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        extra_count=0 if args.live_loader else 26 if args.expect_prefetch else 25
        assert observed.get('done') and not observed['failures'] and observed['cases']==48 and observed['bytes']==2976 and observed['extra_cases']==extra_count,observed
        if not args.live_loader:assert not observed['wrap_head'] and not observed['wrap_tail'] and observed['refresh_counter']!=100 and observed['queue_full'] and observed['grant_wait'],observed
        if args.expect_prefetch:
            observed['prefetched_commands']=observed['z80_variables'][26]+256*observed['z80_variables'][27]
            observed['max_prefetched_pending']=observed['z80_variables'][28]
            assert observed['prefetched_commands']>0 and observed['max_prefetched_pending']==15,observed
        markers=[i for i,e in enumerate(events) if e[0]==3 and 64<=e[2]<=89 or e[0]==3 and 128<=e[2]<176];assert len(markers)==48+extra_count
        work=0x8123905
        for _ in range(observed['work_count']):work=((work<<1)^(0x04c11db7 if work&0x80000000 else 0))&0xffffffff
        assert observed['work_count']>0 and work==observed['foreground'],observed
        rows=[]
        for ordinal,index in enumerate(markers):
            marker=events[index];part=events[index+1:markers[ordinal+1] if ordinal+1<len(markers) else len(events)]
            reads=[e for e in part if e[0]==6];seed=next(e for e in reads if e[2]>>8==100);assert (seed[1]//3420+224)%lines==100;origin=seed[1]//3420*3420
            writes=[e for e in part if e[0]==5];tag=marker[2]
            if tag==88:times=[period*2+n*547200 for n in range(512)];values=[(99+n*13)&255 for n in range(512)]
            elif tag==89:
                times=[];values=[]
                for n in range(64):
                    count=n%16+1 if n<32 else n%8+1;spacing=315 if n<32 else 630
                    times.extend(period*2+n*136800+k*spacing for k in range(count))
                    values.extend((n*37+k*13+5)&255 for k in range(count))
            elif tag<128:
                n=tag-64;count=n+1 if n<16 else n-15;spacing=315 if n<16 else 630;times=[period*2+n*133%3420+k*spacing for k in range(count)];values=[(n*7+k*13)&255 for k in range(count)]
            else:times,values=expected[(tag-128)//2]
            assert [e[2] for e in writes]==values,(region,tag,len(writes),len(values))
            errors=[e[1]-origin-t-args.phase_offset for e,t in zip(writes,times)];assert min(errors)>=0,(region,tag,errors)
            gaps=[b[1]-a[1] for a,b in zip(reads,reads[1:])];assert max(gaps)<17100,(region,tag,max(gaps))
            fast_reads=[a for a,b in zip(reads,reads[1:]) if vwait_pc is not None and a[3]==vwait_pc and b[3]==hwait_pc]
            fast_times={e[1] for e in fast_reads}
            clocks=[e for e in reads if e[3] in (clock_pc,refresh_pc) or e[1] in fast_times];assert clocks
            publication_basis=[e for e in clocks if e[3]!=refresh_pc]
            if refresh_pc is not None:assert max(b[1]-a[1] for a,b in zip(clocks,clocks[1:]))<17100,(region,tag,'private sample gap')
            advances=[b[1]//3420-a[1]//3420 for a,b in zip(clocks,clocks[1:])];assert min(advances)>=0 and max(advances)<=5,(region,tag,min(advances),max(advances))
            counter_values=[(100+e[1]//3420-origin//3420)&65535 for e in clocks];counter_wraps=sum(b<a for a,b in zip(counter_values,counter_values[1:]))
            if tag==88:assert counter_wraps>=1,(region,tag,counter_wraps)
            checks=0
            for pub in (p for p in publications if p['tag']==tag):
                candidates=[e for e in publication_basis if e[1]//period+1<=pub['frame']][-2:]
                assert any(pub['counter']==(100+e[1]//3420-origin//3420)&65535 and pub['v']==e[2]>>8 for e in candidates),(region,tag,pub,candidates)
                checks+=1
            first=0;spacing_checks=0;bursts=[]
            while first<len(times):
                spacing=times[first+1]-times[first] if first+1<len(times) else 0;limit=16 if spacing==315 else 8 if spacing==630 else 1;count=1
                while first+count<len(times) and count<limit and times[first+count]-times[first+count-1]==spacing:count+=1
                for k in range(1,count):assert writes[first+k][1]-writes[first+k-1][1]==spacing,(region,tag,first,k,spacing);spacing_checks+=1
                if count>1:bursts.append((writes[first][1],writes[first+count-1][1]))
                first+=count
            holds=[];held_ranges=[];start=None
            for e in part:
                if e[0]!=7 or e[1]<origin:continue
                if e[2] and start is None:start=e[1]
                if not e[2] and start is not None:holds.append(e[1]-start);held_ranges.append((start,e[1]));start=None
            # The next session requests the bus immediately before its marker;
            # that unmatched final request belongs to the following startup.
            assert (start is None or start>=writes[-1][1]) and holds,(region,tag,start,holds)
            video_holds=[];transport_holds=holds
            if args.video=='dma':
                native_reads=[e[1] for e in part if e[0]==4 and e[3]!=symbols['md_service_clock_hv']+6]
                assert native_reads==sorted(native_reads)
                video_ranges=[(a,b) for a,b in held_ranges if (i:=bisect_right(native_reads,a))<len(native_reads) and native_reads[i]<b]
                video_holds=[b-a for a,b in video_ranges]
                video_range_set=set(video_ranges)
                transport_holds=[b-a for a,b in held_ranges if (a,b) not in video_range_set]
                assert video_holds and max(video_holds)<17100,(region,tag,'video hold',video_holds)
            assert transport_holds and max(transport_holds)<6840,(region,tag,'transport hold',transport_holds)
            assert not any(a<end and b>begin for a,b in held_ranges for begin,end in bursts),(region,tag,'BUSREQ overlaps burst')
            row=dict(marker=tag,errors_master=errors,sample_gap_master=[min(gaps),max(gaps)],clock_line_advance=[min(advances),max(advances)],counter_wraps=counter_wraps,clock_publication_checks=checks,fast_target_samples=len(fast_reads),spacing_checks=spacing_checks,bus_holds_master=[min(holds),max(holds)])
            if args.video=='dma':row.update(video_bus_holds_master=[min(video_holds),max(video_holds)],transport_bus_holds_master=[min(transport_holds),max(transport_holds)])
            if args.live_loader:
                finished=[e for e in part if e[0]==3 and e[2]==0x32];assert len(finished)==1
                queried=[e for e in part if e[0]==3 and e[2]==0x33];assert len(queried)==1
                samples=[e for e in part if e[0]==4 and e[3]==symbols['md_service_clock_hv']+6];assert samples
                first_query=[e for e in samples if finished[0][1]<e[1]<queried[0][1]];assert first_query
                assert records[ordinal][0]==first_query[-1][1]//20*20-origin
                assert records[ordinal][1]==samples[-1][1]//20*20-origin
                callbacks=[];started=None
                for event in part:
                    if event[0]==3 and event[2]==0x30:assert started is None;started=event[1]
                    if event[0]==3 and event[2]==0x31:assert started is not None;callbacks.append((started,event[1]));started=None
                assert started is None and callbacks
                overlap=[e for e in writes if e[1]<finished[0][1]]
                row.update(loader_finish_master=finished[0][1]-origin,loader_query_master=records[ordinal][0],delivery_finish_master=records[ordinal][1],source_finish_master=records[ordinal][2],loader_finish_delta=finished[0][1]-origin-records[ordinal][2],writes_before_loader_finish=len(overlap),writes_outside_publisher=sum(not any(a<=e[1]<=b for a,b in callbacks) for e in overlap),publisher_callbacks=len(callbacks),publisher_total_master=sum(b-a for a,b in callbacks),publisher_peak_master=max(b-a for a,b in callbacks))
            if refresh_pc is not None:row['private_sample_gap_master']=[min(b[1]-a[1] for a,b in zip(clocks,clocks[1:])),max(b[1]-a[1] for a,b in zip(clocks,clocks[1:]))]
            if refresh_pc is not None:row['post_publication_samples']=sum(e[3]==refresh_pc for e in reads)
            rows.append(row)
        if fast_setup:assert sum(row['fast_target_samples'] for row in rows)>0
        if args.live_loader:
            assert sum(row['writes_before_loader_finish'] for row in rows)>0
            assert sum(row['writes_outside_publisher'] for row in rows)>0
            assert all(row['loader_finish_master']<=row['delivery_finish_master'] for row in rows)
        plain={}
        def plain_observe(frame,ram):
            done=int.from_bytes(bytes(ram[(((symbols['gaw_replay_done']&65535)+i)&65535)^1] for i in range(2)),'big');plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',args.max_frames,folder/(region+'-plain'),{observed['frame']} if args.video!='off' else set(),[],skip_intro=False,ram_observer=plain_observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={k:observed[k] for k in plain},(plain,observed)
        video_evidence=None
        if args.video!='off':
            from md_z80_video_fixture import expected_pattern
            from PIL import Image
            capture=folder/(region+'-plain');frame=observed['frame']
            vram=(capture/f'vram_{frame:05d}.bin').read_bytes();regs=(capture/f'vdp_regs_{frame:05d}.bin').read_bytes()
            assert regs[1]&0x40 and not regs[1]&8 and not regs[12]&1
            plane=(regs[2]&0x38)<<10
            scene_evidence={}
            if args.video_scene:
                from md_class0_scene_fixture import validate as scene_validate
                scene_evidence=scene_validate(folder,region,frame,observed,vram,regs,(ROOT/'input/original.sms').read_bytes(),not args.bare,not args.video_source_no_readback)
            elif args.video_source_patterns:
                from md_z80_source_video_fixture import convert_sms_patterns,jobs_per_case
                source=(folder/(region+'-source-patterns.bin')).read_bytes()
                expected_tiles=convert_sms_patterns(source)
                actual_tiles=bytes(vram[(512+n)^1] for n in range(16384))
                assert actual_tiles==expected_tiles
                assert observed['video_sources']==48 and observed['video_requests']==48*512
                if args.video_source_phases:assert observed['video_prefix_ready']==observed['video_tail_ready']==48 and observed['video_service_calls']>0
                if args.video_source_tiles==8:
                    sizes=observed['video_span_sizes'];assert sum(sizes)==observed['video_dma_commits'] and sum(n*x for n,x in enumerate(sizes))==48*512
                    assert all(not sizes[n] for n in [0,1,2,3,5,6,7]) and 48*64<=observed['video_dma_commits']<=48*128
                else:assert observed['video_dma_commits']==48*jobs_per_case(args.video_source_tiles)
                assert observed['video_readback_words']==(0 if args.video_source_no_readback else 48*512*16) and not observed['video_readback_errors']
                assert all(int.from_bytes(vram[plane+(y*64+x)*2:plane+(y*64+x)*2+2],'little')==(16+y*32+x if y<16 else 1) for y in range(28) for x in range(32))
            else:
                assert bytes(vram[(32+n)^1] for n in range(32))==expected_pattern(observed['video_updates'])
                assert all(int.from_bytes(vram[plane+(y*64+x)*2:plane+(y*64+x)*2+2],'little')==1 for y in range(28) for x in range(32))
                assert observed['video_updates']==1+(sum(x['publisher_callbacks'] for x in rows) if args.video in ['cpu','dma'] else 0)
            image=Image.open(capture/f'frame_{frame:05d}.png');colors=image.convert('RGB').getcolors(image.width*image.height)
            assert colors is not None and len(colors)>=(2 if args.video_scene else 8)
            if args.video=='dma':assert observed['video_requests']==observed['video_updates']-1 and observed['video_dma_attempts']>=observed['video_requests']
            jobs=observed['video_dma_commits'] if args.video_source_patterns else observed.get('video_requests')
            if args.video_cache_pattern:assert observed['video_pattern_preparations']==jobs
            if args.video_prepared_job:assert observed['video_job_preparations']==jobs
            video_evidence=dict(mode=args.video,updates=observed['video_updates'],colors=len(colors),vram_sha256=sha(vram),registers_sha256=sha(regs),image_sha256=sha((capture/f'frame_{frame:05d}.png').read_bytes()))
        if args.video_scene:video_evidence.update(scene_evidence)
        result=dict(region=region,**observed,plain_core_identical=True,errors_master=[min(e for r in rows for e in r['errors_master']),max(e for r in rows for e in r['errors_master'])],rows=rows,events_sha256=sha(raw))
        if video_evidence:result['video']=video_evidence
        results.append(result);print(region,{k:v for k,v in result.items() if k!='rows'},flush=True)
    report=dict(live_loader=args.live_loader,bare=args.bare,packet_publication=args.packets,physical_phase_offset=args.phase_offset,kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),driver_sha256=sha(driver),driver_source_sha256=sha(asm.read_bytes()),observer_core_sha256=sha(core.read_bytes()),headers={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['md_z80_psg.h','md_service_clock.h','source_md_psg_plan.h']},sources={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in modules},results=results,
                limits=['Actual native source loader/IRQ/reader/FIFO checked against all16source checkpoints before output. Producer completes before timed replay; foreground polynomial work runs while native publisher/Z80consumer communicate. No actual loader/audio overlap or full-game/DMA/input/boot proof.',
                        'Separate32descriptor ring in Z80RAM;Z80 cannot read68000RAM. Native writer takes bounded BUSREQ only under a Z80grant;one descriptor per grant,grant revoked by native writer before release. Z80 copies values locally before releasing tail;busy excludes in-flight command from drain. Status/timestamps written to68000RAM. Critical wait/burst keeps publication sequence odd. Internal timer must not advance more than5physical lines between samples;rawVC alias at6is unsupported.',
                        'Every315/630intraburst interval exact for original streams and24partial-burst synthetics. Long512command session forces32slot/full-queue pressure,two8bitcursorwraps,16bitlinecounterwrap androlling clock epoch refresh,withu32sourcewrap. Native volatile foreground polynomial checked independently from counted iterations. Every visible even clock stamp checked against last two physically sampled counters. No maximum lateness acceptance gate: initial backend measurement,not production success.'])
    report['polled_transfer_attempts']=args.poll_transfer
    report['video_fixture']=args.video
    report['video_scene']=args.video_scene
    report['scene_hidden']=args.scene_hidden
    report['scene_palette_trace']=args.video_scene and not args.scene_native_palette
    report['video_service_stride']=args.video_service
    report['video_service_kind']=args.video_service_kind
    report['video_pattern_cached']=args.video_cache_pattern
    report['video_job_prepared']=args.video_prepared_job
    report['video_source_patterns']=args.video_source_patterns
    report['video_source_tiles']=args.video_source_tiles
    report['video_grant_backoff']=args.video_grant_backoff
    report['video_source_phases']=args.video_source_phases
    report['video_prefix_immutable_hash_checked']=args.video_source_phases and not args.bare
    if args.video_source_tiles>1:report['video_span_split_window']=args.video_source_refresh
    report['post_publication_refresh']=refresh_pc is not None
    report['fresh_grant_stamps']=grant_pc is not None
    report['video_source_readback']=not args.video_source_no_readback
    report['video_during_delivery']=args.video_source_during_delivery
    if args.video_source_tiles>1:report['headers']['md_z80_video_span.h']=sha((ROOT/'megadrive/src/md_z80_video_span.h').read_bytes())
    report['max_frames']=args.max_frames
    if args.video=='dma':report['headers']['md_z80_video_dma.h']=sha((ROOT/'megadrive/src/md_z80_video_dma.h').read_bytes())
    if args.video_scene:
        for name in ['source_class0_video.h','source_class0_video_assets_generated.h','md_class0_video_stream.h','md_z80_video_span.h']:report['headers'][name]=sha((ROOT/'megadrive/src'/name).read_bytes())
    if args.live_loader:
        report['loader_boundary_before_clock_query']=True
        report['deferred_publication']=args.deferred
        report['source_clock_service']=args.service
        report['retained_fifo_capture']=args.retained_fifo
        report['bulk_fifo_drain']=args.bulk_drain
        report['limits']=['Actual source loader/IRQ/reader/FIFO publishes per IRQ while the Z80 consumes; no precomputed replay or synthetic foreground substitute. Native source output/state/IRQ logs checked against reference; proof mode also checks all16intermediate state copies; bare mode checks final RAM/audio and hashes without those copies.',
                          'Diagnostic markers delimit publisher callbacks and loader finish before its clock query. Writes before finish/outside publisher show overlap with the live loading call, including remaining diagnostic overhead. The separate query and delivery times are checked against independent native HV reads. No deadline acceptance gate; no DMA/native IRQ/input/boot/full-game/hardware proof. Stop only after drain; no fatal abort implementation.']
        if args.packets:report['limits'][0]=report['limits'][0].replace('per IRQ','during reader packet callbacks')
        if args.deferred:report['limits'].append('Deferred experiment: at most128 pending descriptors for this bounded source fixture; WAIT/FULL ends the callback publication attempt, retried at the next packet or drained after the loader-return marker before querying the shared clock. Not a production queue, quiet-gap pump, or bounded whole-game delivery proof.')
        if args.service:report['limits'].append('Experimental source_clock execute/repeat/repeat_disabled/checkpoint wrappers pump before/after each call. Inline source_clock_block and computation inside a call are not serviced. Publisher callback markers exclude these service attempts; callback duration is not total publisher overhead.')
        if args.retained_fifo:report['limits'].append('Bounded-fixture diagnostic capture is read after loading from FIFO slots that remain intact: at most128 produced events in512 slots; cursor distance/capacity checked. No per-callback duplicate event capture. Native source enqueue/take/planner/publisher remain active; this is reduced observer overhead, not a production queue optimization or a general retention guarantee.')
        if args.bulk_drain:report['limits'].append('Publisher consumes due FIFO events with source_psg_queue_take_many: one queue validation and cursor release per batch, original enqueue/plan/transport remain active.')
        if args.poll_transfer:report['limits'].append('Synchronous polled transfer prepares once per call and retries only WAIT up to the configured attempt limit. Diagnostic grant_wait counts exhausted outer calls, not internal transfer attempts; FULL/errors return immediately. No deferred queue or source work runs inside the polling loop.')
        if args.video!='off':report['limits'].append('H32/224 display enabled with a synthetic repeated diagnostic tile and palette, verified against final physical VRAM/registers/image. CPU mode uploads one32byte tile per publisher callback; DMA mode retains jobs for guarded transfers. This is a diagnostic video fixture, not the game renderer, SMS image fidelity, native IRQs, or full-game proof. Callback marker duration includes video work attempted in that callback.')
        if args.video=='dma':report['limits'].append('DMA experiment queues one deterministic diagnostic tile job per callback, tries only with grant/even stamp at most2raw lines old in rawV235..252 (excluding NTSC duplicate range), rechecks after BUSREQ. Precomputed fixed32byte DMA command words issued only inside the granted critical section, source128KiB boundary checked; SGDK auto-increment set before acquisition. Jobs are retained in order and all drained while Z80 clock is still active before stop; some may complete after loader/audio delivery markers. No job frame deadlines or game renderer queue are established; native IRQs remain masked.')
        if args.video_service:report['limits'].append('Video service experiment wraps the selected source_clock function boundaries (all four or only repeat_disabled) and attempts DMA every configured number of boundaries. Inline source_clock_block and computation inside helpers are not serviced. Adds native cost without changing the logical source clock; no maximum service interval or frame deadline is established.')
        if args.video_cache_pattern:report['limits'].append('Diagnostic tile payload is prepared once per queued job and remains intact across WAIT, reset after successful DMA. This removes fixture preparation overhead; DMA primitive/control preparation and its guards remain unchanged. No renderer payload/deadline claim.')
        if args.video_prepared_job:
            report['limits']=[x.replace('grant/even stamp','grant and atomic8bit V stamp') for x in report['limits']]
        if args.video_prepared_job:report['limits'].append('DMA control token prepared once per immutable diagnostic payload, retained across WAIT and consumed on OK. Bus/timestamp/window are rechecked each attempt. Mode/ownership/source lifetime must remain intact; no renderer frame deadline is established.')
        if args.video_source_patterns:
            report['limits']=[x for x in report['limits'] if not x.startswith(('H32/224 display enabled with a synthetic','DMA experiment queues one deterministic','Diagnostic tile payload'))]
        if args.video_source_patterns:report['limits'].append('Actual source-checked16384byte SMS pattern mirror converted into512 MD tiles per case after source loading. Native physical VRAM readback checks every word before payload release; independent planar conversion checks all final tiles. The visible atlas uses a diagnostic palette/map, not the game scene. Uploads begin after source work and drain after audio: no overlap/deadline or production integration claim. Generic one-job-per-callback description does not apply to this mode.')
        if args.video_source_no_readback:report['limits']=[x.replace('Native physical VRAM readback checks every word before payload release;', 'Per-word native VRAM readback disabled for this performance measurement;') for x in report['limits']]
        if args.video_source_phases:report['limits']=[x.replace('Upload'+ 's begin after source work and drain after audio:', 'Uploads release in two actual loader phases and drain remaining jobs afterwards:') for x in report['limits']]
        if args.video_source_phases:report['limits'].append('Actual loader checkpoints release prefix0..0x37ff at1706 and tail0x3800..0x3fff at1deb. Native service at repeat_disabled boundaries plus checkpoints. Prefix is not modified by intervening source routines; proof mode also compares its14336byte hash at both boundaries. Atlas remains diagnostic; no scene/palette/sprite/deadline proof. Uploads can begin during loading; physical captures must count actual overlap.')
        if args.video_grant_backoff:report['limits'].append('Caller grant-backoff experiment: after video WAIT retain token/payload and skip attempts until atomic fresh grant byte changes, unless mailbox error is set. Does not cache authorization for a successful transfer; held-bus guards remain active. Skip count is separate from actual DMA API attempts.')
        if args.video_source_refresh:report['limits'].append('Optional post-publication private timer resample capability is required for the early rawV224..228 window; raw229..234 excluded. The original API and driver remain distinct. Timer safety is independently checked, not inferred from ready/grant.')
        if args.video_source_tiles==8:report['limits'].append('Adaptive spans use8tiles only with no pending/in-flight PSG descriptor, otherwise4tiles. Above4tiles requires a fresh encoded grant V stamp of age0; all fresh-grant spans clip the late window at rawV251. Physical private-update gaps remain strictly below17100master ticks. Transfer sizes/counts are observed separately; this does not establish per-frame deadlines.')
        if args.video_source_tiles==3:report['limits'].append('Three-tile stress starts with1tile then2tiles, followed by3tile jobs and a final2tile tail:172 commits per512tiles, exercising1/2/3tile spans in actual DMA.')
        if args.video_source_during_delivery:report['limits']=[x.replace('Uploads begin after source work and drain after audio:', 'Uploads begin after source work; video is also serviced during the final audio delivery wait, with remaining jobs drained afterwards:') for x in report['limits']]
        report['limits'].append('Native PSG-word diagnostic markers add writes outside the checked Z80 source-byte stream; these kernels measure source-byte transport/timing and do not establish an unmodified audio waveform.')
    if args.video_scene:
        report['limits']=[x for x in report['limits'] if not x.startswith(('H32/224 display enabled with a synthetic','DMA experiment queues one deterministic'))]
        report['limits'].append('Native class0 background pipeline:193ROM patterns in retained1..4tile spans,24translated64byte map rows, CPU32color publish in guarded blank. Resident HUD/menu/icon patterns initialized from native entry ROM resources; all319outside pattern slots must remain intact. Actual source checkpoints1706/1deb/24bf queue owned data. Independent final VRAM/map/CRAM checks; optional native per-word readback is specified by video_source_readback; no sprites/fullboot/whole-game/deadline/waveform proof. CPU palette trace hook enabled only in fixture; default backend emits no PSG diagnostic markers.')
    if args.scene_hidden:report['limits']=[x.replace('CPU32color publish in guarded blank','CPU32color publish while display is disabled') for x in report['limits']]+['Hidden H32 mode: display disabled before clock start, kept off through all pattern/map/palette jobs, enabled only after successful flush. Hidden small-DMA path excludes duplicated rawV229..234 and retains age/grant/refresh/error guards. No H40 change; timing and display intervals require physical capture. The fixture reveal boundary is not yet the original game enable deadline.']
    if args.poll_transfer and not args.live_loader:report['limits'].append('Precomputed replay uses the bounded polled API; configured attempt count applies to WAIT only. grant_wait counts exhausted outer calls, not internal attempts.')
    (ROOT/('analysis/md_z80_psg'+suffix.replace('-','_')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
