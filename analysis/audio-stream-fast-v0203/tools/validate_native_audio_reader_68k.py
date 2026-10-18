"""Execute full-reader source vectors on compiled68000, bounded-size cartridges."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from actor_reference import ROOT
from run_core import run
from validate_native_audio_reader import MODULES


def main():
    fast='--fast' in sys.argv
    folder=ROOT/('validation/native-audio-fast-reader-68k' if fast else 'validation/native-audio-reader-68k');folder.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    suites=json.loads((ROOT/'validation/native-audio-reader/cases.json').read_text())+json.loads((ROOT/'validation/native-audio-reader/extension-cases.json').read_text())
    lows=[]
    for suite in suites:
        image=(ROOT/suite['fixture']).read_bytes()
        assert hashlib.sha256(image).hexdigest()==suite['fixture_sha256']
        lows.append(image[:32768])
    bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]
    all_cases=[(index,row) for index,suite in enumerate(suites) for row in suite['cases']];results=[]
    # Full before/after states keep the captured oracle transparent. Splitting
    # at3500 keeps each test ROM below4MiB, with no mapper assumption.
    for part,start in enumerate(range(0,len(all_cases),3500)):
        cases=all_cases[start:start+3500];base=folder/f'part-{part}';src=base/'src';src.mkdir(parents=True,exist_ok=True)
        lines=['static const u8 bank6[]={'+','.join(map(str,bank))+'};',
               'static const u8 low[][32768]={'+','.join('{'+','.join(map(str,data))+'}' for data in lows)+'};',
               'typedef struct {u8 suite,before[400],after[400];u16 de_in,de;u32 tstates,fetches;} ReaderCase;',
               'static const ReaderCase cases[]={']
        for index,row in cases:
            lines.append('{'+str(index)+',{'+','.join(map(str,row['before']))+'},{'+','.join(map(str,row['after']))+'},'+str(row['de_in'])+','+str(row['de'])+','+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../../megadrive/src/{name}.c"\n')
        (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_audio_reader.h"
#include "../../../../megadrive/src/source_audio_fast.h"
#include "expected.h"
volatile u32 gaw_reader_cases,gaw_reader_failures;
volatile u16 gaw_reader_done;
static SourceAudioReaderOutput output;
int main(bool hard_reset)
{
 u32 row;u16 n,de;u8 state[400],accepted;SourceClockWork work;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  de=cases[row].de_in;
  for(n=0;n<400;n++) state[n]=cases[row].before[n];
  accepted=source_audio_reader(state,low[cases[row].suite],32768,bank6,&de,&work,&output);
  if(!accepted || output.error || output.count>SOURCE_AUDIO_READER_WRITES ||
     work.tstates!=cases[row].tstates || work.fetches!=cases[row].fetches || de!=cases[row].de) gaw_reader_failures++;
  for(n=0;n<400;n++) if(state[n]!=cases[row].after[n]) gaw_reader_failures++;
  gaw_reader_cases++;
 }
 gaw_reader_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
'''.replace('accepted=source_audio_reader(', 'accepted=source_audio_reader_fast(' if fast else 'accepted=source_audio_reader('))
        env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
        sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
        args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
        built=subprocess.run(args,cwd=base,env=env,capture_output=True,text=True)
        (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-3000:]
        cartridge=base/'out/release/rom.bin';assert cartridge.stat().st_size<=0x400000
        symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
        for region in ['auto','pal']:
            observed={}
            def observe(frame,ram):
                if observed.get('done'):return
                def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
                observed.update(frame=frame,done=value('gaw_reader_done',2),cases=value('gaw_reader_cases',4),failures=value('gaw_reader_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):
                run(cartridge,40000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
            assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(part,region,observed)
            results.append(dict(part=part,region=region,ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed))
            print(part,region,observed,flush=True)
    report=dict(fast=fast,cases=len(all_cases),results=results,
                module_sha256={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                reader_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_reader.c').read_bytes()).hexdigest(),
                limits=['Compiled68000, full400/T/M1/DE from hashed source captures and source-verified gates.',
                        'PSG writes/full IRQ clock/waveform/hardware/natural full progression require separate evidence.'])
    (ROOT/('analysis/native_audio_fast_reader_68k_report.json' if fast else 'analysis/native_audio_reader_68k_report.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
