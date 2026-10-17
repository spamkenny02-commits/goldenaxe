"""Replay complete wait and restore-edge source vectors on compiled68000."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from native_wait_return_support import MODULES,WRAPPER,helpers


def main():
    folder=ROOT/'validation/native-wait-return-68k';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    cases=[]
    for name in ['unit-cases.json','restore-cases.json','live-cases.json']:
        cases+=json.loads((ROOT/'validation/native-wait-return'/name).read_text())
    fixtures=sorted({row['fixture'] for row in cases});lows=[]
    for fixture in fixtures:
        image=(ROOT/fixture).read_bytes();digest=hashlib.sha256(image).hexdigest()
        assert all(row['fixture_sha256']==digest for row in cases if row['fixture']==fixture)
        lows.append(image[:32768])
    bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000];max_events=max(len(row['events']) for row in cases);results=[]
    for part,start in enumerate(range(0,len(cases),2000)):
        rows=cases[start:start+2000];base=folder/f'part-{part}';src=base/'src';src.mkdir(parents=True,exist_ok=True)
        lines=['static const u8 low[][32768]={'+','.join('{'+','.join(map(str,data))+'}' for data in lows)+'};',
               'static const u8 bank6[]={'+','.join(map(str,bank))+'};',
               f'typedef struct {{u32 phase[12];u8 refresh,fixture,tail;u16 tile_count;u8 ram[336],audio[400],after_ram[336],after_audio[400];u32 expected[18],events[{max_events}];}} WaitCase;',
               'static const WaitCase cases[]={']
        for row in rows:
            events=row['events']+[0]*(max_events-len(row['events']))
            lines.append('{{'+','.join(str(v)+'UL' for v in row['phase'])+'},'+str(row['refresh'])+','+str(fixtures.index(row['fixture']))+','+str(row['tail'])+','+str(row['tile_count'])+
                         ',{'+','.join(map(str,row['ram']))+'},{'+','.join(map(str,row['audio']))+'},{'+','.join(map(str,row['expected_ram']))+
                         '},{'+','.join(map(str,row['expected_audio']))+'},{'+','.join(str(v)+'UL' for v in row['expected'])+'},{'+','.join(str(v)+'UL' for v in events)+'}},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../../megadrive/src/{name}.c"\n')
        (src/'wrapper.c').write_text(WRAPPER.replace('#include "source_wait_restore.h"','#include "../../../../megadrive/src/source_wait_restore.h"'))
        (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 wait_return_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,const u8 *bank6,u16 tile_count,u8 tail,u32 *out,u32 *events);
volatile u32 gaw_return_cases,gaw_return_failures;
volatile u16 gaw_return_done;
static u8 ram[336],audio[400];static u32 output[18],events[96];
int main(bool hard_reset)
{
 u32 row;u16 n;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  if(!wait_return_case(cases[row].phase,cases[row].refresh,ram,audio,low[cases[row].fixture],bank6,cases[row].tile_count,cases[row].tail,output,events)) gaw_return_failures++;
  for(n=0;n<18;n++) if(output[n]!=cases[row].expected[n]) gaw_return_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_return_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_return_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_return_failures++;
  gaw_return_cases++;
 }
 gaw_return_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
        env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
        args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
        built=subprocess.run(args,cwd=base,env=env,capture_output=True,text=True);(base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-3000:]
        cartridge=base/'out/release/rom.bin';assert cartridge.stat().st_size<=0x400000
        symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
        for region in ['auto','pal']:
            observed={}
            def observe(frame,raw):
                def value(name,n):return int.from_bytes(bytes(raw[(symbols[name]+i)^1] for i in range(n)),'big')
                observed.update(frame=frame,done=value('gaw_return_done',2),cases=value('gaw_return_cases',4),failures=value('gaw_return_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):
                run(cartridge,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
            assert observed.get('done') and (observed['cases'],observed['failures'])==(len(rows),0),(part,region,observed)
            results.append(dict(part=part,region=region,ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed));print(part,region,observed,flush=True)
    report=dict(cases=len(cases),results=results,helper_sha256=helpers(),production_md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                limits=['Compiled68000 complete wait and restore tails, source-derived phase/R/M1/331RAM/400audio/duration/IRQ entry proofs, plus host parity for other fields.',
                        'Test frontend stops after authoritative done flag; input source contexts observed. Production clock wiring, hardware acknowledgement/waveforms/full natural progression remain open.'])
    (ROOT/'analysis/native_wait_return_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
