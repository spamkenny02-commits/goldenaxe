"""Execute continuous graphics/map/HUD/palette/history vectors on native68000."""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_room_load import MODULES,build_wrapper

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--actors',action='store_true');args=parser.parse_args();actor_mode=args.actors
    folder=ROOT/('validation/native-room-load-actors' if actor_mode else 'validation/native-room-load');cases=json.loads((folder/'cases.json').read_text());WRAPPER=build_wrapper(actor_mode)
    base=folder/'kernel';src=base/'src';src.mkdir(parents=True,exist_ok=True)
    rom=(ROOT/'input/original.sms').read_bytes();max_events=max(len(row['events']) for row in cases)
    for row in cases:
        row['expected_ram']=row['states'][-736:-400];row['expected_audio']=row['states'][-400:]
    lines=['static const u8 low[]={'+','.join(map(str,rom[:32768]))+'};',
           'static const u8 bank6[]={'+','.join(map(str,rom[0x18000:0x1c000]))+'};',
           'static const u8 bank2[]={'+','.join(map(str,rom[0x8000:0xc000]))+'};',
           'static const u8 bank11[]={'+','.join(map(str,rom[0x2c000:0x30000]))+'};',
           'static const u8 bank8[]={'+','.join(map(str,rom[0x20000:0x24000]))+'};',
           'static const u8 bank9[]={'+','.join(map(str,rom[0x24000:0x28000]))+'};',
           'static const u8 bank4[]={'+','.join(map(str,rom[0x10000:0x14000]))+'};',
           'static const u8 patterns[]={'+','.join(map(str,rom[0x3c010:]))+'};',
           f'typedef struct {{u32 phase[12];u16 room;u8 refresh,hud[16],ram[336],audio[400],after_ram[336],after_audio[400],history[16],masks[256],after_history[16],after_masks[256];u32 expected[47],points[306];u8 states[12512];u32 events[{max_events}];}} PrefixCase;',
           'static const PrefixCase cases[]={']
    for row in cases:
        events=row['events']+[0]*(max_events-len(row['events']))
        lines.append('{{'+','.join(str(v)+'UL' for v in row['phase'])+'},'+str(row['room'])+','+str(row['refresh'])+',{'+','.join(map(str,row['hud']))+'}'+
                     ',{'+','.join(map(str,row['ram']))+'},{'+','.join(map(str,row['audio']))+'},{'+','.join(map(str,row['expected_ram']))+
                     '},{'+','.join(map(str,row['expected_audio']))+'},{'+','.join(map(str,row['history']))+'},{'+','.join(map(str,row['masks']))+'},{'+','.join(map(str,row['after_history']))+'},{'+','.join(map(str,row['after_masks']))+'},{'+','.join(str(v)+'UL' for v in row['expected'])+'},{'+','.join(str(v)+'UL' for v in row['points'])+'},{'+','.join(map(str,row['states']))+'},{'+','.join(str(v)+'UL' for v in events)+'}},')
    lines.append('};');header='\n'.join(lines)+'\n'
    if actor_mode:
        header=header.replace('expected[47],points[306];u8 states[12512]','expected[48],points[396];u8 states[16192]')
        header=header.replace('after_masks[256];u32','after_masks[256],actors[768];u32')
        for row in cases:
            needle='},{'+','.join(str(v)+'UL' for v in row['expected'])+'}'
            assert header.count(needle)==1
            header=header.replace(needle,'},{'+','.join(map(str,row['actors']))+needle,1)
        header='static const u8 bank12[]={'+','.join(map(str,rom[0x30000:0x34000]))+'};\n'+header
    (src/'expected.h').write_text(header)
    for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../../megadrive/src/{name}.c"\n')
    (src/'wrapper.c').write_text(WRAPPER.replace('#include "source_room_load.h"','#include "../../../../megadrive/src/source_room_load.h"').replace('#include "source_pattern_plan_generated.h"','#include "../../../../megadrive/src/source_pattern_plan_generated.h"'))
    main_source='''#include <genesis.h>
#include "expected.h"
u8 room_load_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,const u8 *bank6,u16 room,const u8 *map_bank,const u8 *patterns,const u8 *bank2,const u8 *bank11,const u8 *bank4,const u8 *hud,u8 *history,u8 *masks,u32 *out,u32 *events,u32 *points,u8 *states);
volatile u32 gaw_finish_cases,gaw_finish_failures;
volatile u16 gaw_finish_done;
static u8 ram[336],audio[400],history[16],masks[256];static u32 output[47],events[384],points[306];static u8 states[12512];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);SYS_disableInts();
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  for(n=0;n<16;n++) history[n]=cases[row].history[n];
  for(n=0;n<256;n++) masks[n]=cases[row].masks[n];
  if(!room_load_case(cases[row].phase,cases[row].refresh,ram,audio,low,bank6,cases[row].room,(cases[row].room&128)?bank9:bank8,patterns,bank2,bank11,bank4,cases[row].hud,history,masks,output,events,points,states)) gaw_finish_failures++;
  for(n=0;n<47;n++) if(output[n]!=cases[row].expected[n]) gaw_finish_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_finish_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_finish_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_finish_failures++;
  for(n=0;n<306;n++) if(points[n]!=cases[row].points[n]) gaw_finish_failures++;
  for(n=0;n<12512;n++) if(states[n]!=cases[row].states[n]) gaw_finish_failures++;
  for(n=0;n<16;n++) if(history[n]!=cases[row].after_history[n]) gaw_finish_failures++;
  for(n=0;n<256;n++) if(masks[n]!=cases[row].after_masks[n]) gaw_finish_failures++;
  gaw_finish_cases++;
 }
 gaw_finish_done=1;while(TRUE);return 0;
}
'''
    if actor_mode:
        main_source=main_source.replace('const u8 *hud,u8 *history,u8 *masks,u32 *out','const u8 *hud,const u8 *bank12,u8 *history,u8 *masks,u8 *actors,u32 *out')
        main_source=main_source.replace('history[16],masks[256];static u32 output[47],events[384],points[306];static u8 states[12512];','history[16],masks[256],actors[768];static u32 output[48],events[384],points[396];static u8 states[16192];')
        main_source=main_source.replace('cases[row].hud,history,masks,output','cases[row].hud,bank12,history,masks,actors,output')
        main_source=main_source.replace('n<47;','n<48;').replace('n<306;','n<396;').replace('n<12512;','n<16192;')
        main_source=main_source.replace('  gaw_finish_cases++;','  for(n=0;n<768;n++) if(actors[n]!=cases[row].actors[n]) gaw_finish_failures++;\n  gaw_finish_cases++;')
    (src/'main.c').write_text(main_source)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2',
                          'build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2500:]
    cartridge=base/'out/release/rom.bin';assert cartridge.stat().st_size<=0x400000
    symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,raw):
            def value(name,n):return int.from_bytes(bytes(raw[(symbols[name]+i)^1] for i in range(n)),'big')
            observed.update(frame=frame,done=value('gaw_finish_done',2),cases=value('gaw_finish_cases',4),failures=value('gaw_finish_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):
            run(cartridge,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(passed=True,actor_list_included=actor_mode,cases=len(cases),results=results,helpers={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                source_case_sha256=hashlib.sha256((folder/'cases.json').read_bytes()).hexdigest(),
                kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),production_clock_wired=False,
                limits=[f'Compiled68000 {22 if actor_mode else 17} checkpoint vectors retain source phase/R/M1/331RAM/400audio/IRQ-offset assertions; other fields are host parity.',
                        'Includes final seed/history/masks and368 cleared bytes. Physical IRQs disabled; source IRQs use live native audio. Changed class0 load only; physical uploads/contention, all graphics classes and global entry-state propagation remain pending.'])
    (ROOT/('analysis/native_room_load_actors_68k_report.json' if actor_mode else 'analysis/native_room_load_68k_report.json')).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
