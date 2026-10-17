"""Compiled68000 palette source vectors and disabled-repeat equivalence vectors."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_clock_disabled_repeat import WRAPPER as REPEAT_WRAPPER
from validate_native_palette import WRAPPER as PALETTE_WRAPPER,MODULES

def main():
    base=ROOT/'validation/finish-units-68k';src=base/'src';src.mkdir(parents=True,exist_ok=True)
    spans=json.loads((ROOT/'validation/clock-disabled-repeat/cases.json').read_text())
    palettes=json.loads((ROOT/'validation/native-palette/cases.json').read_text());rom=(ROOT/'input/original.sms').read_bytes()
    lines=['static const u8 low[]={'+','.join(map(str,rom[:32768]))+'};',
           'typedef struct {u16 lines,count;u32 raster;u8 refresh,pending;u32 expected[16];} Span;',
           'static const Span spans[]={']
    for row in spans:lines.append('{'+f"{row['lines']},{row['count']},{row['raster']}UL,{row['refresh']},{row['pending']}"+',{'+','.join(str(v)+'UL' for v in row['expected'])+'}},')
    lines+=['};','typedef struct {u8 blink,slot,counter,refresh,palette[16];u32 work[3];} PaletteCase;','static const PaletteCase palettes[]={']
    for row in palettes:lines.append('{'+f"{row['blink']},{row['slot']},{row['counter']},{row['entry_R']}"+',{'+','.join(map(str,row['palette']))+'},{'+','.join(str(v)+'UL' for v in row['work'])+'}},')
    lines+=['};','static const u16 guards[][6]={{1,0,0,29,3,127},{0,1,0,29,3,127},{0,0,1,29,3,127},{0,0,0,0,3,127},{0,0,0,29,0,127},{0,0,0,29,3,0},{0,0,0,65535,255,65535}};']
    (src/'expected.h').write_text('\n'.join(lines)+'\n')
    for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../megadrive/src/{name}.c"\n')
    wrapper=REPEAT_WRAPPER+PALETTE_WRAPPER
    for name in ['source_clock','source_room_finish']:wrapper=wrapper.replace(f'#include "{name}.h"',f'#include "../../../megadrive/src/{name}.h"')
    (src/'wrapper.c').write_text(wrapper)
    (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 disabled_case(u16 lines,u32 raster,u8 refresh,u8 pending,u16 count,u32 *out);
u8 disabled_guard(u8 first,u8 blocked,u8 enabled,u16 ticks,u8 m1,u16 count,u32 *out);
u8 palette_case(u8 blink,u8 slot,u8 counter,u8 refresh,const u8 *low,u8 *palette,u32 *out);
volatile u32 gaw_span_cases,gaw_palette_cases,gaw_unit_failures;
volatile u16 gaw_unit_done;
static u32 output[32];static u8 palette[16];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(spans)/sizeof(spans[0]);row++)
 {
  if(!disabled_case(spans[row].lines,spans[row].raster,spans[row].refresh,spans[row].pending,spans[row].count,output)) gaw_unit_failures++;
  for(n=0;n<16;n++) if(output[n]!=spans[row].expected[n] || output[16+n]!=spans[row].expected[n]) gaw_unit_failures++;
  gaw_span_cases++;
 }
 for(row=0;row<7;row++)
 {
  if(disabled_guard(guards[row][0],guards[row][1],guards[row][2],guards[row][3],guards[row][4],guards[row][5],output)) gaw_unit_failures++;
  for(n=0;n<16;n++) if(output[n]!=output[n+16]) gaw_unit_failures++;
 }
 for(row=0;row<sizeof(palettes)/sizeof(palettes[0]);row++)
 {
  if(!palette_case(palettes[row].blink,palettes[row].slot,palettes[row].counter,palettes[row].refresh,low,palette,output)) gaw_unit_failures++;
  for(n=0;n<16;n++) if(palette[n]!=palettes[row].palette[n]) gaw_unit_failures++;
  for(n=0;n<3;n++) if(output[n]!=palettes[row].work[n]) gaw_unit_failures++;
  gaw_palette_cases++;
 }
 gaw_unit_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2000:]
    cartridge=base/'out/release/rom.bin';symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,ram):
            def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
            observed.update(frame=frame,done=value('gaw_unit_done',2),spans=value('gaw_span_cases',4),palettes=value('gaw_palette_cases',4),failures=value('gaw_unit_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and (observed['spans'],observed['palettes'],observed['failures'])==(len(spans),len(palettes),0),observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(spans=len(spans),palette_cases=len(palettes),guards=7,results=results,
                helpers={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),input_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['validation/clock-disabled-repeat/cases.json','validation/native-palette/cases.json']},limits=['Palette16 bytes/T/M1/R are source vectors; disabled-repeat vectors are parity with slow instruction stepping.','Isolated IRQ-disabled units; full live IRQ/source-phase proof is the separate16-checkpoint chain.'])
    (ROOT/'analysis/finish_units_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
