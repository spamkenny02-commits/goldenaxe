"""Measure bare native loading CPU frames, without proof hashes or snapshots."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_room_finish import MODULES

def main():
    base=ROOT/'validation/native-loading-budget';src=base/'src';src.mkdir(parents=True,exist_ok=True)
    header=ROOT/'validation/native-room-finish/kernel/src/expected.h';(src/'expected.h').write_bytes(header.read_bytes())
    for name in MODULES:
        if name=='source_irq_context':
            body=(ROOT/'megadrive/src/source_irq_context.c').read_text().replace('#include "source_irq_context.h"','#include <genesis.h>\n#include "../../../megadrive/src/source_irq_context.h"')
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
        elif name=='source_clock':
            body=(ROOT/'megadrive/src/source_clock.c').read_text().replace('#include "source_clock.h"','#include "../../../megadrive/src/source_clock.h"\nvolatile u32 gaw_exec_calls,gaw_repeat_calls,gaw_repeat_groups,gaw_repeat_reps;').replace('#include "source_rng.h"','#include "../../../megadrive/src/source_rng.h"')
            body=body.replace('u8 source_clock_execute(SourceClock *clock,u16 tstates,u8 fetches,u8 effect,SourceClockInterrupt interrupt,void *context)\n{','u8 source_clock_execute(SourceClock *clock,u16 tstates,u8 fetches,u8 effect,SourceClockInterrupt interrupt,void *context)\n{\n    gaw_exec_calls++;')
            body=body.replace('u16 source_clock_repeat(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions)\n{','u16 source_clock_repeat(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions)\n{\n    gaw_repeat_calls++;')
            body=body.replace('return count;','gaw_repeat_groups++;gaw_repeat_reps+=count;return count;')
            (src/f'{name}.c').write_text(body)
        else:(src/f'{name}.c').write_text(f'#include "../../../megadrive/src/{name}.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_room_finish.h"
#include "expected.h"
volatile u32 gaw_budget[24][16],gaw_budget_cases,gaw_budget_failures;
volatile u16 gaw_budget_done;
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
  SYS_doVBlankProcess();gaw_irq_ticks=gaw_irq_calls=0;gaw_exec_calls=gaw_repeat_calls=gaw_repeat_groups=gaw_repeat_reps=0;started=vtimer;
  accepted=source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,0,0);mark1=vtimer;
  if(accepted) accepted=source_world_map_load(&clock,&ctx,cases[row].room,1,(cases[row].room&128)?bank9:bank8,bank2,&data,&map,0,0);mark2=vtimer;
  if(accepted) accepted=source_room_hud_prepare(&clock,&ctx,&data,&map,bank4,cases[row].hud,0,0);mark3=vtimer;
  if(accepted) accepted=source_room_finish(&clock,&ctx,&data,&map,cases[row].hud,&finish,0,0);mark4=vtimer;
  gaw_budget[row][0]=mark4-started;gaw_budget[row][1]=clock.elapsed;gaw_budget[row][2]=clock.foreground_m1;gaw_budget[row][3]=clock.irq_count;gaw_budget[row][4]=1;
  gaw_budget[row][5]=mark1-started;gaw_budget[row][6]=mark2-mark1;gaw_budget[row][7]=mark3-mark2;gaw_budget[row][8]=mark4-mark3;
  gaw_budget[row][9]=gaw_irq_ticks;gaw_budget[row][10]=gaw_irq_calls;gaw_budget[row][11]=1;
  gaw_budget[row][12]=gaw_exec_calls;gaw_budget[row][13]=gaw_repeat_calls;gaw_budget[row][14]=gaw_repeat_groups;gaw_budget[row][15]=gaw_repeat_reps;
  if(!accepted || ctx.error || clock.elapsed!=cases[row].expected[2] || clock.foreground_m1!=cases[row].expected[4] || clock.refresh!=cases[row].expected[10]) gaw_budget_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_budget_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_budget_failures++;
  gaw_budget_cases++;
 }
 gaw_budget_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=base/'out/release/rom.bin'
    cases=json.loads((ROOT/'validation/native-room-finish/cases.json').read_text());results=[]
    for region in ['auto','pal']:
        observed={};rows=[]
        def observe(frame,ram):
            def value(name,n,offset=0):return int.from_bytes(bytes(ram[(symbols[name]+offset+i)^1] for i in range(n)),'big')
            observed.update(done=value('gaw_budget_done',2),cases=value('gaw_budget_cases',4),failures=value('gaw_budget_failures',4),frame=frame)
            if observed['done']:
                for n,case in enumerate(cases):
                    if not value('gaw_budget',4,n*64+16):continue
                    physical=value('gaw_budget',4,n*64);virtual=value('gaw_budget',4,n*64+4);logical_frames=virtual/(case['phase'][3]*3420)
                    rows.append(dict(case=n,room=case['room'],physical_frames=physical,source_master=virtual,source_frames=logical_frames,compute_to_source_ratio=physical/logical_frames,stages=[value('gaw_budget',4,n*64+20+k*4) for k in range(4)],irq_subticks=value('gaw_budget',4,n*64+36),irq_calls=value('gaw_budget',4,n*64+40),clock_calls=[value('gaw_budget',4,n*64+48+k*4) for k in range(4)]))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and (observed['cases'],observed['failures'])==(12,0),observed
        results.append(dict(region=region,rows=rows,**observed));print(region,[(r['physical_frames'],round(r['source_frames'],2),r['stages'],round(r['irq_subticks']/(1536 if region=='pal' else 1280),2),r['clock_calls']) for r in rows],flush=True)
    report=dict(results=results,helpers={name+suffix:hashlib.sha256((ROOT/'megadrive/src'/(name+suffix)).read_bytes()).hexdigest() for name in MODULES for suffix in ['.c','.h'] if (ROOT/'megadrive/src'/(name+suffix)).exists()},cases_sha256=hashlib.sha256((ROOT/'validation/native-room-finish/cases.json').read_bytes()).hexdigest(),clock_call_fields=['execute','generic_repeat','accepted_generic_groups','generic_repetitions'],inline_blocks_counted=False,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                limits=['Vtimer delta around four native calls, no hashes/checkpoint snapshots; stage marks and two getSubTick samples perIRQ add a small profiling overhead. One-frame stage resolution; IRQ subtick conversion approximate.',
                        'Only matching logical/physical region; controlled input contexts. Buffer initialization and correctness comparisons outside timing.',
                        'Display off,discarded PSG sink,no real renderer/uploads/input pacing; CPU lower-bound profile, not playable frame-rate proof.'])
    (ROOT/'analysis/native_loading_budget_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
