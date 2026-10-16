"""Run retained and new source84C7 state/T/M1 vectors on compiled68000."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_audio_tone import MODULES


def main():
    folder=ROOT/'validation/native-audio-tone-68k';folder.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    suites=json.loads((ROOT/'validation/native-audio-tone/cases.json').read_text())+json.loads((ROOT/'validation/native-audio-tone/extension-cases.json').read_text())
    fields=sorted({i for suite in suites for row in suite['cases'] for i,_ in row['patches']})
    assert len(fields)<=255
    lows=[]
    for suite in suites:
        image=(ROOT/suite['fixture']).read_bytes()
        assert hashlib.sha256(image).hexdigest()==suite['fixture_sha256']
        lows.append(image[:32768])
    bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]
    all_cases=[(index,row) for index,suite in enumerate(suites) for row in suite['cases']];results=[]
    for part,start in enumerate(range(0,len(all_cases),30000)):
        cases=all_cases[start:start+30000];base=folder/f'part-{part}';src=base/'src';src.mkdir(parents=True,exist_ok=True)
        max_patches=max(len(row['patches']) for _,row in cases)
        lines=['static const u8 bank6[]={'+','.join(map(str,bank))+'};',
               'static const u8 low[][32768]={'+','.join('{'+','.join(map(str,data))+'}' for data in lows)+'};',
               'static const u8 seeds[][400]={'+','.join('{'+','.join(map(str,s['seed']))+'}' for s in suites)+'};',
               'static const u16 fields[]={'+','.join(map(str,fields))+'};',
               'static const u16 slots[]={'+','.join(str(s['offset']) for s in suites)+'};',
               'static const u8 offset_count[]={'+','.join(str(len(s['offsets'])) for s in suites)+'};',
               'static const u16 input_offsets[][16]={'+','.join('{'+','.join(map(str,s['offsets']))+'}' for s in suites)+'};',
               f'typedef struct {{u8 suite,patch_count,input[16],patches[{max_patches*2}];u16 de_in,de;u32 tstates,fetches;}} ToneCase;',
               'static const ToneCase cases[]={']
        for index,row in cases:
            patches=[v for offset,value in row['patches'] for v in [fields.index(offset),value]]
            patches.extend([0]*(max_patches*2-len(patches)))
            lines.append('{'+str(index)+','+str(len(row['patches']))+',{'+','.join(map(str,row['input']))+'},{'+','.join(map(str,patches))+'},'+str(row['de_in'])+','+str(row['de'])+','+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../../megadrive/src/{name}.c"\n')
        (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_audio_tone.h"
#include "expected.h"
volatile u32 gaw_tone_cases,gaw_tone_failures;
volatile u16 gaw_tone_done;
static SourceAudioSequenceOutput output;
int main(bool hard_reset)
{
 u32 row;u16 n,offset,de;u8 state[400],expected[400],accepted,suite;SourceClockWork work;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  suite=cases[row].suite;de=cases[row].de_in;
  for(n=0;n<400;n++) state[n]=expected[n]=seeds[suite][n];
  for(n=0;n<offset_count[suite];n++) {offset=input_offsets[suite][n];state[offset]=expected[offset]=cases[row].input[n];}
  for(n=0;n<cases[row].patch_count;n++) expected[fields[cases[row].patches[n*2]]]=cases[row].patches[n*2+1];
  accepted=source_audio_tone(state,slots[suite],low[suite],32768,bank6,&de,&work,&output);
  if(!accepted || output.error || output.count>512 || work.tstates!=cases[row].tstates || work.fetches!=cases[row].fetches ||
     de!=cases[row].de || output.de!=de || output.unwind) gaw_tone_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_tone_failures++;
  gaw_tone_cases++;
 }
 gaw_tone_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
        env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
        sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
        args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
        built=subprocess.run(args,cwd=base,env=env,capture_output=True,text=True)
        (base/'build.log').write_text(built.stdout+built.stderr)
        assert built.returncode==0,built.stderr[-3000:]
        cartridge=base/'out/release/rom.bin'
        symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
        for region in ['auto','pal']:
            observed={}
            def observe(frame,ram):
                if observed.get('done'):return
                def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
                observed.update(frame=frame,done=value('gaw_tone_done',2),cases=value('gaw_tone_cases',4),failures=value('gaw_tone_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):
                run(cartridge,40000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(part,region,observed)
            results.append(dict(part=part,region=region,ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed))
            print(part,region,observed,flush=True)
    report=dict(cases=len(all_cases),results=results,
                tone_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_tone.c').read_bytes()).hexdigest(),
                limits=['Compiled68000 in GPG, state400/T/M1/DE and consumed inner returns.',
                        'PSG writes and real reader composition require production checks; waveforms/full IRQ clock remain open.'])
    (ROOT/'analysis/native_audio_tone_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
