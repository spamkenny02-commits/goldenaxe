"""Measure bare native loading CPU frames, without proof hashes or snapshots."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from actor_reference import ROOT
from run_core import run
from validate_native_room_finish import MODULES

def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    bare='--bare' in sys.argv;planned='--planned' in sys.argv;precise='--precise' in sys.argv;baseline_audio='--baseline-audio' in sys.argv;physical_video='--physical-video' in sys.argv
    assert not precise or bare,'Precise entry/exit sampling requires --bare'
    assert not baseline_audio or precise,'Baseline audio comparison requires --precise'
    assert not physical_video or (precise and planned),'Physical video requires --planned --bare --precise'
    audio_readiness='--audio-readiness' in sys.argv
    assert not audio_readiness or physical_video,'Audio readiness requires --physical-video'
    fast_timed_audio='--fast-timed-audio' in sys.argv
    timed_audio='--timed-audio' in sys.argv or fast_timed_audio
    assert not timed_audio or (physical_video and not baseline_audio),'Timed audio requires physical video and its own reader'
    base=ROOT/('validation/native-'+('planned-' if planned else '')+'loading-budget'+('-bare' if bare else '')+('-precise' if precise else '')+('-baseline-audio' if baseline_audio else '')+('-physical-video' if physical_video else ''));src=base/'src';src.mkdir(parents=True,exist_ok=True)
    if audio_readiness:
        base=base.with_name(base.name+'-audio-readiness');src=base/'src';src.mkdir(parents=True,exist_ok=True)
    modules=MODULES
    if timed_audio:
        from validate_reader_timing import MODULES as TIMED_MODULES
        modules=list(dict.fromkeys([name for name in MODULES if name!='source_irq_context']+['source_irq_fast_timed_context' if fast_timed_audio else 'source_irq_timed_context']+TIMED_MODULES+(['source_audio_fast_timed'] if fast_timed_audio else [])))
        base=base.with_name(base.name+('-fast-timed-audio' if fast_timed_audio else '-timed-audio'));src=base/'src';src.mkdir(parents=True,exist_ok=True)
    header=ROOT/('validation/native-'+('planned-' if planned else '')+'room-finish/kernel/src/expected.h');(src/'expected.h').write_bytes(header.read_bytes())
    for name in modules:
        if name=='source_irq_context' and baseline_audio:
            body=(ROOT/'megadrive/src/source_irq_context.c').read_text().replace('#include "source_irq_context.h"','#include "../../../megadrive/src/source_irq_context.h"').replace('#include "source_audio_fast.h"','#include "../../../megadrive/src/source_audio_fast.h"').replace('source_audio_reader_stream_fast(','source_audio_reader_stream(')
            (src/f'{name}.c').write_text(body)
        elif name=='source_irq_context' and not bare:
            body=(ROOT/'megadrive/src/source_irq_context.c').read_text().replace('#include "source_irq_context.h"','#include <genesis.h>\n#include "../../../megadrive/src/source_irq_context.h"')
            body=body.replace('#include "source_audio_fast.h"','#include "../../../megadrive/src/source_audio_fast.h"')
            body=body.replace('u8 source_irq_interrupt(', 'static u8 profiled_irq_inner(')
            body+='''
volatile u32 gaw_irq_ticks,gaw_irq_calls;
u8 source_irq_interrupt(void *ctx,const SourceClockIrq *entry,SourceClockWork *work)
{
 u32 started=getSubTick();u8 accepted=profiled_irq_inner(ctx,entry,work);
 gaw_irq_ticks+=getSubTick()-started;gaw_irq_calls++;return accepted;
}
'''
            (src/f'{name}.c').write_text(body)
        elif name=='source_clock' and not bare:
            body=(ROOT/'megadrive/src/source_clock.c').read_text().replace('#include "source_clock.h"','#include "../../../megadrive/src/source_clock.h"\nvolatile u32 gaw_exec_calls,gaw_repeat_calls,gaw_repeat_groups,gaw_repeat_reps;').replace('#include "source_rng.h"','#include "../../../megadrive/src/source_rng.h"')
            body=body.replace('u8 source_clock_execute(SourceClock *clock,u16 tstates,u8 fetches,u8 effect,SourceClockInterrupt interrupt,void *context)\n{','u8 source_clock_execute(SourceClock *clock,u16 tstates,u8 fetches,u8 effect,SourceClockInterrupt interrupt,void *context)\n{\n    gaw_exec_calls++;')
            body=body.replace('u16 source_clock_repeat(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions)\n{','u16 source_clock_repeat(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions)\n{\n    gaw_repeat_calls++;')
            body=body.replace('return count;','gaw_repeat_groups++;gaw_repeat_reps+=count;return count;')
            (src/f'{name}.c').write_text(body)
        else:(src/f'{name}.c').write_text(('#define source_irq_interrupt '+('source_irq_fast_timed_interrupt' if fast_timed_audio else 'source_irq_timed_interrupt')+'\n' if timed_audio and name not in ['source_irq_timed_context','source_irq_fast_timed_context'] else '')+f'#include "../../../megadrive/src/{name}.c"\n')
    if bare:(src/'profile_counters.c').write_text('#include <types.h>\nvolatile u32 gaw_irq_ticks,gaw_irq_calls,gaw_exec_calls,gaw_repeat_calls,gaw_repeat_groups,gaw_repeat_reps;\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_room_finish.h"
#include "expected.h"
volatile u32 gaw_budget[24][16],gaw_budget_cases,gaw_budget_failures;
volatile u16 gaw_budget_done;
volatile u32 gaw_graphics_marks[24][6];
static u16 profile_row,profile_point;
static u8 graphics_mark(void *user,u16 pc,const SourceClock *clock,const SourceIrqContext *ctx)
{
 (void)user;(void)pc;(void)clock;(void)ctx;
 if(profile_point>=6) return 0;gaw_graphics_marks[profile_row][profile_point++]=vtimer;return 1;
}
extern volatile u32 gaw_irq_ticks,gaw_irq_calls;
extern volatile u32 gaw_exec_calls,gaw_repeat_calls,gaw_repeat_groups,gaw_repeat_reps;
static u8 ram[336],audio[400],pixels[16384],meta[2048],backup[16],terrain[1024],saved[1024],cells[256],tilemap[1536];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);VDP_setVInterrupt(TRUE);SYS_enableInts();
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  SourceClock clock;SourceIrqContext ctx={0};SourceGraphicsData data;SourceWorldMapData map;SourceRoomFinish finish;
  u32 started,mark1,mark2,mark3,mark4,period=cases[row].phase[3]*3420;s32 raster=(s32)(cases[row].phase[1]*3420)+(s32)(cases[row].phase[0]-cases[row].phase[2]);u8 accepted;
  if((cases[row].phase[3]==313)!=SYS_isPAL()) continue;
  while(raster<0) raster+=period;
  while((u32)raster>=period) raster-=period;
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  for(n=0;n<16384;n++) pixels[n]=0xa7;
  for(n=0;n<2048;n++) meta[n]=0xa7;
  for(n=0;n<1024;n++) terrain[n]=0xa7;
  for(n=0;n<256;n++) cells[n]=0xa7;
  for(n=0;n<1536;n++) tilemap[n]=0xa7;
  source_clock_init(&clock,cases[row].phase[3],raster,cases[row].refresh,cases[row].phase[8],cases[row].phase[9],cases[row].phase[10]);
  ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.bank6=bank6;ctx.input.lines=cases[row].phase[3];ctx.input.reset_mask=16;
  data.patterns=pixels;data.metatiles=meta;data.backup=backup;data.terrain=terrain;data.saved_terrain=saved;map.cells=cells;map.tilemap=tilemap;
  SYS_doVBlankProcess();gaw_irq_ticks=gaw_irq_calls=0;gaw_exec_calls=gaw_repeat_calls=gaw_repeat_groups=gaw_repeat_reps=0;started=vtimer;profile_row=row;profile_point=0;
  accepted=source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,graphics_mark,0);mark1=vtimer;
  if(accepted) accepted=source_world_map_load(&clock,&ctx,cases[row].room,1,(cases[row].room&128)?bank9:bank8,bank2,&data,&map,0,0);mark2=vtimer;
  if(accepted) accepted=source_room_hud_prepare(&clock,&ctx,&data,&map,bank4,cases[row].hud,0,0);mark3=vtimer;
  if(accepted) accepted=source_room_finish(&clock,&ctx,&data,&map,cases[row].hud,&finish,0,0);mark4=vtimer;
  gaw_budget[row][0]=mark4-started;gaw_budget[row][1]=clock.elapsed;gaw_budget[row][2]=clock.foreground_m1;gaw_budget[row][3]=clock.irq_count;gaw_budget[row][4]=1;
  gaw_budget[row][5]=mark1-started;gaw_budget[row][6]=mark2-mark1;gaw_budget[row][7]=mark3-mark2;gaw_budget[row][8]=mark4-mark3;
  gaw_budget[row][9]=gaw_irq_ticks;gaw_budget[row][10]=gaw_irq_calls;gaw_budget[row][11]=started;
  gaw_budget[row][12]=gaw_exec_calls;gaw_budget[row][13]=gaw_repeat_calls;gaw_budget[row][14]=gaw_repeat_groups;gaw_budget[row][15]=gaw_repeat_reps;
  if(profile_point!=6 || !accepted || ctx.error || clock.elapsed!=cases[row].expected[2] || clock.foreground_m1!=cases[row].expected[4] || clock.refresh!=cases[row].expected[10]) gaw_budget_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_budget_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_budget_failures++;
  gaw_budget_cases++;
 }
 gaw_budget_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    if planned:
        main=src/'main.c';body=main.read_text().replace('#include "expected.h"','#include "expected.h"\n#include "../../../megadrive/src/source_pattern_plan_generated.h"')
        body=body.replace('source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,graphics_mark,0)','source_graphics_load_class0_planned(&clock,&ctx,patterns,bank2,bank11,&data,graphics_mark,0,&gaw_class0_pattern_plan)');main.write_text(body)
    if precise:
        main=src/'main.c';body=main.read_text()
        body=body.replace('int main(bool hard_reset)',
            '__attribute__((noinline,externally_visible)) void gaw_budget_begin(void) {__asm__ volatile ("nop":::"memory");}\n'
            '__attribute__((noinline,externally_visible)) void gaw_budget_end(void) {__asm__ volatile ("nop; nop":::"memory");}\nint main(bool hard_reset)')
        body=body.replace('  accepted=source_graphics_load_class0','  gaw_budget_begin();\n  accepted=source_graphics_load_class0')
        body=body.replace(';mark4=vtimer;',';gaw_budget_end();mark4=vtimer;');main.write_text(body)
    if physical_video:
        from generate_class0_video import generate
        generate();(src/'source_class0_video.c').write_text('#include "../../../megadrive/src/source_class0_video.c"\n')
        main=src/'main.c';body=main.read_text().replace('#include "expected.h"','#include "expected.h"\n#include "../../../megadrive/src/source_class0_video.h"')
        body=body.replace('int main(bool hard_reset)',
            'u16 gaw_video_map[768],gaw_video_palette[32];\nvolatile u32 gaw_video_psg_writes[24];\n'
            '__attribute__((noinline,externally_visible)) void gaw_video_convert(void) {__asm__ volatile ("nop; nop; nop":::"memory");}\n'
            '__attribute__((noinline,externally_visible)) void gaw_video_dma(void) {__asm__ volatile ("nop; nop; nop; nop":::"memory");}\n'
            'static const u32 guard[8]={0x5aa55aa5UL,0x5aa55aa5UL,0x5aa55aa5UL,0x5aa55aa5UL,0x5aa55aa5UL,0x5aa55aa5UL,0x5aa55aa5UL,0x5aa55aa5UL};\n'
            'static void physical_psg(void *unused,const u8 *writes,u16 count) {u16 n;(void)unused;gaw_video_psg_writes[profile_row]+=count;for(n=0;n<count;n++) PSG_write(writes[n]);}\nint main(bool hard_reset)')
        body=body.replace('SYS_enableInts();','SYS_enableInts();VDP_setScreenWidth256();VDP_setPlaneSize(64,32,TRUE);VDP_loadTileData(guard,15,1,DMA);VDP_loadTileData(guard,209,1,DMA);')
        body=body.replace('ctx.input.reset_mask=16;','ctx.input.reset_mask=16;ctx.sink=physical_psg;')
        body=body.replace('gaw_budget_end();mark4=vtimer;',
            'gaw_video_convert();source_class0_video_map(tilemap,gaw_video_map,768);source_class0_video_palette(cells+0xb0,gaw_video_palette);gaw_video_dma();if(!source_class0_video_upload(gaw_video_map,gaw_video_palette)) accepted=0;gaw_budget_end();mark4=vtimer;')
        body=body.replace('gaw_budget_cases++;','gaw_budget_cases++;SYS_doVBlankProcess();');main.write_text(body)
    if timed_audio:
        main=src/'main.c';body=main.read_text().replace('#include "expected.h"','#include "expected.h"\n#include "../../../megadrive/src/source_irq_timed_context.h"')
        body=body.replace('SourceIrqContext ctx={0};','SourceTimedIrqContext timed_ctx={0};').replace('ctx.','timed_ctx.core.').replace('&ctx','&timed_ctx.core')
        body=body.replace('timed_ctx.core.sink=physical_psg;','timed_ctx.sink=physical_psg;')
        old='static void physical_psg(void *unused,const u8 *writes,u16 count) {u16 n;(void)unused;gaw_video_psg_writes[profile_row]+=count;for(n=0;n<count;n++) PSG_write(writes[n]);}'
        new='''volatile u32 gaw_psg_deadlines[128];volatile u8 gaw_psg_values[128];volatile u16 gaw_psg_deadline_row;
static void physical_psg(void *unused,const u8 *writes,const u32 *master,u16 count)
{
 u16 n,first=gaw_video_psg_writes[profile_row];(void)unused;gaw_psg_deadline_row=profile_row;
 if(first+count>128) {gaw_budget_failures++;return;}
 for(n=0;n<count;n++) {gaw_psg_deadlines[first+n]=master[n];gaw_psg_values[first+n]=writes[n];PSG_write(writes[n]);}
 gaw_video_psg_writes[profile_row]+=count;
}'''
        assert old in body;body=body.replace(old,new);main.write_text(body)
    if audio_readiness:
        main=src/'main.c';body=main.read_text()
        body=body.replace('int main(bool hard_reset)', '''
volatile u32 gaw_audio_meta[24][32][3];
volatile u16 gaw_audio_count[24];
__attribute__((noinline,externally_visible)) void gaw_audio_ready(void) {__asm__ volatile ("nop; nop; nop; nop; nop":::"memory");}
static void audio_trace(void *unused,const SourceClockIrq *entry,const SourceClockWork *work)
{
 u16 n=gaw_audio_count[profile_row];(void)unused;
 if(n>=32) {gaw_budget_failures++;return;}
 gaw_audio_meta[profile_row][n][0]=entry->entry_elapsed;
 gaw_audio_meta[profile_row][n][1]=entry->entry_elapsed+(work->tstates-72)*15;
 gaw_audio_meta[profile_row][n][2]=gaw_video_psg_writes[profile_row];
 gaw_audio_count[profile_row]=n+1;gaw_audio_ready();
}
int main(bool hard_reset)''')
        if timed_audio:
            body=body.replace('timed_ctx.sink=physical_psg;','timed_ctx.sink=physical_psg;timed_ctx.core.trace=audio_trace;')
            body=body.replace('volatile u32 gaw_psg_deadlines[128];',
                'volatile u16 gaw_audio_packet_sizes[128],gaw_audio_packet_count;\nvolatile u32 gaw_psg_deadlines[128];')
            body=body.replace('if(first+count>128)',
                'if(gaw_audio_packet_count>=128) {gaw_budget_failures++;return;}\n gaw_audio_packet_sizes[gaw_audio_packet_count++]=count;\n if(first+count>128)')
            body=body.replace('  gaw_budget_begin();','  gaw_audio_packet_count=0;gaw_budget_begin();')
        else:
            body=body.replace('ctx.sink=physical_psg;','ctx.sink=physical_psg;ctx.trace=audio_trace;')
        main.write_text(body)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=base/'out/release/rom.bin'
    cases=json.loads((ROOT/('validation/native-'+('planned-' if planned else '')+'room-finish/cases.json')).read_text());results=[]
    core=None;observer=None
    if precise:
        core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll';observer=c.CDLL(str(core))
        full={m[2]:int(m[1],16) for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
        begin,end=full['gaw_budget_begin'],full['gaw_budget_end'];assert begin!=end
        watch_pcs=[begin,end]+([full['gaw_video_convert'],full['gaw_video_dma']] if physical_video else [])
        if audio_readiness:
            psg_pc,= [address for name,address in full.items() if name.split('.lto_priv.')[0]=='physical_psg']
            watch_pcs += [full['gaw_audio_ready'],psg_pc]
        observer.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)];observer.gaw_md_event_count.restype=c.c_uint;observer.gaw_md_event_data.restype=c.POINTER(c.c_uint)
    for region in ['auto','pal']:
        observed={};rows=[];events=[];previous=[0];line_count=313 if region=='pal' else 262;captures=set();snapshots={};last_completed=[0]
        matching=[n for n,row in enumerate(cases) if row['phase'][3]==line_count]
        if precise:observer.gaw_md_config(len(watch_pcs),(c.c_uint*len(watch_pcs))(*watch_pcs))
        def observe(frame,ram):
            if precise:
                count=observer.gaw_md_event_count();p=observer.gaw_md_event_data();assert count<8192
                for n in range(previous[0],count):events.append((p[n*3],(frame-1)*line_count*3420+p[n*3+1]))
                previous[0]=count
            def value(name,n,offset=0):return int.from_bytes(bytes(ram[(symbols[name]+offset+i)^1] for i in range(n)),'big')
            observed.update(done=value('gaw_budget_done',2),cases=value('gaw_budget_cases',4),failures=value('gaw_budget_failures',4),frame=frame)
            if physical_video and observed['cases']>last_completed[0]:
                assert observed['cases']==last_completed[0]+1
                snapshots[matching[observed['cases']-1]]=frame;captures.add(frame);last_completed[0]=observed['cases']
            if observed['done']:
                for n,case in enumerate(cases):
                    if not value('gaw_budget',4,n*64+16):continue
                    physical=value('gaw_budget',4,n*64);virtual=value('gaw_budget',4,n*64+4);logical_frames=virtual/(case['phase'][3]*3420)
                    marks=[value('gaw_graphics_marks',4,n*24+k*4) for k in range(6)];deltas=[marks[0]-value('gaw_budget',4,n*64+44)]+[marks[k]-marks[k-1] for k in range(1,6)]
                    rows.append(dict(graphics_return_frames=value('gaw_budget',4,n*64+20)-sum(deltas),graphics_stages=deltas,case=n,room=case['room'],physical_frames=physical,source_master=virtual,source_frames=logical_frames,compute_to_source_ratio=physical/logical_frames,stages=[value('gaw_budget',4,n*64+20+k*4) for k in range(4)],irq_subticks=value('gaw_budget',4,n*64+36),irq_calls=value('gaw_budget',4,n*64+40),clock_calls=[value('gaw_budget',4,n*64+48+k*4) for k in range(4)]))
                    if audio_readiness:
                        count=value('gaw_audio_count',2,n*2)
                        assert count==case['expected'][7] and count<=32
                        rows[-1]['irq_metadata']=[[value('gaw_audio_meta',4,(n*32+k)*12+j*4) for j in range(3)] for k in range(count)]
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,60000,base/region,captures,[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and (observed['cases'],observed['failures'])==(12,0),observed
        if precise:
            width=4 if physical_video else 2
            timing_events=[event for event in events if event[0] in watch_pcs[:width]]
            assert len(timing_events)==12*width and len(rows)==12,(region,len(timing_events),len(rows))
            for index,row in enumerate(rows):
                chunk=timing_events[index*width:(index+1)*width];a,b=chunk[0],chunk[-1]
                assert a[0]==begin and b[0]==end and b[1]>=a[1]
                measured=b[1]-a[1];row.update(measured_master=measured,measured_frames=measured/(line_count*3420),remaining_source_master=row['source_master']-measured)
                if physical_video:
                    assert [x[0] for x in chunk]==[begin,full['gaw_video_convert'],full['gaw_video_dma'],end]
                    row.update(compute_master=chunk[1][1]-a[1],video_conversion_master=chunk[2][1]-chunk[1][1],video_transfer_master=b[1]-chunk[2][1])
                if audio_readiness:
                    irq_events=[event for event in events if a[1]<=event[1]<=b[1] and event[0] in [psg_pc,full['gaw_audio_ready']]]
                    packets=[];batch=[];previous_bytes=0
                    for pc,stamp in irq_events:
                        if pc==psg_pc:
                            batch.append(stamp-a[1]);continue
                        k=len(packets);entry,completion,total=row['irq_metadata'][k]
                        expected=cases[row['case']]['events'][k*6:k*6+6]
                        assert entry==expected[0] and completion==entry+(expected[3]-72)*15
                        byte_count=total-previous_bytes
                        assert bool(batch)==bool(byte_count),(region,row['case'],k,'PSG batch presence')
                        packets.append(dict(source_entry_master=entry,source_completion_master=completion,psg_bytes=byte_count,batch_ready_master=batch,irq_ready_master=stamp-a[1],last_batch_margin_master=completion-batch[-1] if batch else None))
                        batch=[];previous_bytes=total
                    assert not batch and len(packets)==len(row['irq_metadata'])
                    row['audio_readiness']=packets
        if physical_video:
            assert len(snapshots)==12
            for row in rows:
                index=row['case'];frame=snapshots[index];folder=base/region
                raw=(folder/f'ram_{frame:05d}.bin').read_bytes();ram=bytes(raw[i^1] for i in range(len(raw)))
                def area(name,length):return ram[symbols[name]:symbols[name]+length]
                v=(folder/f'vram_{frame:05d}.bin').read_bytes();cram=(folder/f'cram_{frame:05d}.bin').read_bytes();regs=(folder/f'vdp_regs_{frame:05d}.bin').read_bytes();plane=(regs[2]&56)<<10
                assert not regs[12]&0x81,(region,index,'visible width not restored')
                assert regs[16]&3==1 and not regs[16]&0x30,(region,index,'physical plane is not64x32')
                assert not regs[1]&0x40,(region,index,'display unexpectedly enabled')
                def fnv(data):
                    h=2166136261
                    for value in data:h=((h^value)*16777619)&0xffffffff
                    return h
                sms=area('tilemap',1536);upper=area('cells',256)[0xb0:0xc0]
                assert fnv(sms)==cases[index]['expected'][37] and fnv(upper)==cases[index]['expected'][38],(region,index,'source endpoint buffers not retained')
                for n in range(768):
                    word=int.from_bytes(sms[n*2:n*2+2],'little');expected=16+(word&511)|((word&0x200)<<2)|((word&0x400)<<2)|((word&0x800)<<2)|((word&0x1000)<<3)
                    pos=plane+(n//32+2)*128+(n%32)*2;assert int.from_bytes(v[pos:pos+2],'little')==expected,(region,index,n,'physical map')
                from validate_native_patterns import decode
                from audit_item_reward_visuals import sms_pixels,md_pixels
                source_pixels,_=decode(rom[0x3c010:])
                for n in range(193):assert md_pixels(v,n+16)==sms_pixels(source_pixels,n),(region,index,n,'physical pattern')
                for n in [15,209]:assert md_pixels(v,n)==[5,10,10,5,5,10,10,5]*8,(region,index,'pattern guard',n)
                levels=[0,3,5,7];sms_colors=bytes(rom[0x3c000:0x3c010])+upper
                for n,color in enumerate(sms_colors):
                    expected=0 if not n else levels[color&3]|(levels[(color>>2)&3]<<3)|(levels[(color>>4)&3]<<6)
                    assert int.from_bytes(cram[n*2:n*2+2],'little')==expected,(region,index,n,'physical palette')
                row.update(extract_frame=frame,physical_map_words=768,physical_pattern_pixels=193*64,physical_palette_words=32,pattern_guard_tiles=2,display_disabled=True,visible_width_restored=256,physical_plane=[64,32],psg_writes=int.from_bytes(area('gaw_video_psg_writes',96)[index*4:index*4+4],'big'),vram_sha256=hashlib.sha256(v).hexdigest(),cram_sha256=hashlib.sha256(cram).hexdigest())
                if timed_audio:
                    archive=ROOT/'analysis/loading-psg-v0203';manifest=json.loads((archive/'manifest.json').read_text())
                    record_path='validation/loading-psg-deadlines/inputs.json';records_raw=(archive/record_path).read_bytes();assert hashlib.sha256(records_raw).hexdigest()==manifest['files'][record_path]
                    records=json.loads(records_raw);reference=json.loads((ROOT/'analysis/loading_psg_deadlines_report.json').read_text());reference_rows=next(x['rows'] for x in reference['results'] if x['region']==region)
                    expected_times=[time for item in reference_rows if item['case']==index for time in item['source_psg_master']]
                    expected_bytes=[byte for item in records if item['case']==index for byte in item['writes']]
                    count=row['psg_writes'];actual_times=[int.from_bytes(area('gaw_psg_deadlines',512)[n*4:n*4+4],'big') for n in range(count)];actual_bytes=list(area('gaw_psg_values',128)[:count])
                    assert int.from_bytes(area('gaw_psg_deadline_row',2),'big')==index
                    assert actual_times==expected_times and actual_bytes==expected_bytes,(region,index,'absolute source PSG dates/bytes')
                    row.update(source_psg_master=actual_times,source_psg_bytes=actual_bytes,source_psg_dates_verified=True)
                    if audio_readiness:
                        packets=row['audio_readiness'];ready=[time for packet in packets for time in packet['batch_ready_master']]
                        packet_count=int.from_bytes(area('gaw_audio_packet_count',2),'big');sizes_raw=area('gaw_audio_packet_sizes',256)
                        sizes=[int.from_bytes(sizes_raw[n*2:n*2+2],'big') for n in range(packet_count)]
                        assert len(ready)==len(sizes) and sum(sizes)==count and all(sizes)
                        offset=0
                        for packet in packets:
                            batch_sizes=sizes[offset:offset+len(packet['batch_ready_master'])];offset+=len(batch_sizes)
                            assert sum(batch_sizes)==packet['psg_bytes']
                            packet['batch_sizes']=batch_sizes
                        byte_ready=[time for time,size in zip(ready,sizes) for _ in range(size)]
                        margins=[due-available for due,available in zip(actual_times,byte_ready)]
                        row.update(source_psg_packet_sizes=sizes,source_psg_ready_master=byte_ready,
                                   source_psg_ready_margins_master=margins,late_source_psg_bytes=sum(m<0 for m in margins))
        results.append(dict(region=region,rows=rows,**observed));print(region,[(r['physical_frames'],round(r['source_frames'],2),r['stages'],r['graphics_stages'],round(r['irq_subticks']/(1536 if region=='pal' else 1280),2),r['clock_calls']) for r in rows],flush=True)
    report=dict(planned=planned,instrumented=not bare,results=results,helpers={name+suffix:hashlib.sha256((ROOT/'megadrive/src'/(name+suffix)).read_bytes()).hexdigest() for name in modules for suffix in ['.c','.h'] if (ROOT/'megadrive/src'/(name+suffix)).exists()},cases_sha256=hashlib.sha256((ROOT/('validation/native-'+('planned-' if planned else '')+'room-finish/cases.json')).read_bytes()).hexdigest(),clock_call_fields=['execute','generic_repeat','accepted_generic_groups','generic_repetitions'],inline_blocks_counted=False,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                limits=['Vtimer delta around four native calls, no hashes/checkpoint snapshots; stage marks and two getSubTick samples perIRQ add a small profiling overhead. Six additional vtimer checkpoints split graphics stages1706/170E/1720/1733/1748/24B9. One-frame stage resolution; IRQ subtick conversion approximate.',
                        'Only matching logical/physical region; controlled input contexts. Buffer initialization and correctness comparisons outside timing.',
                        'Display off,discarded PSG sink,no real renderer/uploads/input pacing; CPU lower-bound profile, not playable frame-rate proof.'])
    if planned:report['plan_sha256']=hashlib.sha256((ROOT/'megadrive/src/source_pattern_plan_generated.h').read_bytes()).hexdigest()
    if bare:report['limits'][0]='Vtimer delta around four native calls and six graphics checkpoints only. No per-instruction/repetition counters and no IRQ subtimer; counter fields are zero. One-frame resolution.'
    if precise:
        report['precise_read_only_observer']=True;report['observer_core_sha256']=hashlib.sha256(core.read_bytes()).hexdigest()
        report['clock_audio_fast']=(not baseline_audio and not timed_audio) or fast_timed_audio
        report['generated_source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in src.iterdir() if p.suffix in ['.c','.h']}
        report['limits'][0]='Read-only 68000 PC observations at two noinline markers around the four loading calls. Their call/return overhead is included. Vtimer stage marks remain at one-frame resolution; measured_master gives the finer complete-chain duration.'
    if physical_video:
        report['physical_video']=True;report['physical_psg_writes']=True;report['audio_deadline_pacing']=False
        report['video_module_sha256']=hashlib.sha256((ROOT/'megadrive/src/source_class0_video.c').read_bytes()).hexdigest();report['video_assets_sha256']=hashlib.sha256((ROOT/'megadrive/src/source_class0_video_assets_generated.h').read_bytes()).hexdigest();report['video_header_sha256']=hashlib.sha256((ROOT/'megadrive/src/source_class0_video.h').read_bytes()).hexdigest()
        report['map_transfer']='CPU port bursts,24 rows of16 longwords';report['pattern_palette_transfer']='DMA with temporary H40 during display-off';report['attribute_lut_bytes']=131072
        report['limits'][0]='Four read-only 68000 PC markers bracket source computation, video conversion and physical transfers. Marker call/return overhead and PSG write counters are included. Vtimer stage marks remain at one-frame resolution; measured_master gives the finer complete-chain duration.'
        report['limits'][2]='Display off;193 base-pattern tiles,768 map words and32 palette words physically uploaded after source computations. Actor/hero/HUD font tile uploads and backdrop initialization excluded. PSG bytes physically emitted during virtual IRQ computation without deadline pacing. Raw endpoint VRAM/CRAM verified; no displayed frame or source-relative publication-timing claim.'
    if audio_readiness:
        report['audio_readiness']=True
        report['limits'].append('IRQ metadata stores and a fifth marker per IRQ add CPU overhead. PSG function-entry observations mark batch readiness, not individual port-write times. Margins compare a budget-begin-relative epoch to source elapsed time; global physical/source phase alignment is not established. Source IRQ completion is only a necessary last-batch bound, not the deadline of each PSG byte. No publication queue or pacing is enabled.')
    if timed_audio:
        report['absolute_source_psg_dates']=True;report['clock_audio_timed']=True;report['clock_audio_fast_timed']=fast_timed_audio
        report['limits'].append('Separate timed IRQ adapter rebases reader OUT times onto SourceClock.elapsed master ticks. All retained loading dates/bytes are checked against the original-reader oracle. Deadline stores,conversion and immediate actual PSG writes are included in CPU time. No physical scheduling at these dates or global boot phase is enabled; clock_audio_fast_timed identifies the selected snapshot contract.')
        if audio_readiness:
            report['limits'].append('Packet sizes align each source-byte deadline with its packet function-entry readiness. This optimistic availability excludes sink/queue overhead after entry and includes diagnostic packet-size stores. Negative margins demonstrate lateness for this relative epoch; positive margins alone do not prove schedulability or absolute boot alignment.')
    (ROOT/('analysis/native_'+('planned_' if planned else '')+'loading_budget'+('_bare' if bare else '')+('_precise' if precise else '')+('_baseline_audio' if baseline_audio else '')+('_physical_video' if physical_video else '')+('_audio_readiness' if audio_readiness else '')+('_fast_timed_audio' if fast_timed_audio else '_timed_audio' if timed_audio else '')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
