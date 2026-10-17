"""Replay original IRQ state/stage vectors on compiled68000 cartridges."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run


def main():
    folder=ROOT/'validation/native-source-irq-68k';folder.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    cases=json.loads((ROOT/'validation/native-source-irq/cases.json').read_text())
    extra=ROOT/'validation/native-source-irq/extension-cases.json'
    if extra.exists():cases+=json.loads(extra.read_text())
    results=[]
    for part,start in enumerate(range(0,len(cases),4000)):
        rows=cases[start:start+4000];base=folder/f'part-{part}';src=base/'src';src.mkdir(parents=True,exist_ok=True)
        lines=['typedef struct {u8 before[336],after[336];SourceIrqInput input;SourceClockWork reader;SourceIrqOutput output;} IrqCase;',
               'static const IrqCase cases[]={']
        for row in rows:
            stages='{'+','.join('{'+','.join(str(v)+'UL' for v in pair)+'}' for pair in row['stages'])+'}'
            whole='{'+','.join(str(v)+'UL' for v in row['whole'])+'}'
            lines.append('{{'+','.join(map(str,row['before']))+'},{'+','.join(map(str,row['after']))+'},{'+','.join(map(str,row['input']))+'},{'+','.join(str(v)+'UL' for v in row['reader'])+'},{'+stages+','+whole+','+str(row['palette_taken'])+',0}},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        (src/'source_irq.c').write_text('#include "../../../../megadrive/src/source_irq.c"\n')
        (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_irq.h"
#include "expected.h"
volatile u32 gaw_irq_cases,gaw_irq_failures;
volatile u16 gaw_irq_done;
int main(bool hard_reset)
{
 u32 row;u16 n;u8 state[336],accepted;SourceIrqOutput output;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) state[n]=cases[row].before[n];
  accepted=source_irq(state,&cases[row].input,&cases[row].reader,&output);
  if(!accepted || output.palette_taken!=cases[row].output.palette_taken || output.reset_requested ||
     output.whole.tstates!=cases[row].output.whole.tstates || output.whole.fetches!=cases[row].output.whole.fetches) gaw_irq_failures++;
  for(n=0;n<SOURCE_IRQ_STAGES;n++)
   if(output.stages[n].tstates!=cases[row].output.stages[n].tstates || output.stages[n].fetches!=cases[row].output.stages[n].fetches) gaw_irq_failures++;
  for(n=0;n<336;n++) if(state[n]!=cases[row].after[n]) gaw_irq_failures++;
  gaw_irq_cases++;
 }
 gaw_irq_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
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
                observed.update(frame=frame,done=value('gaw_irq_done',2),cases=value('gaw_irq_cases',4),failures=value('gaw_irq_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):
                run(cartridge,40000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
            assert observed.get('done') and (observed['cases'],observed['failures'])==(len(rows),0),(part,region,observed)
            results.append(dict(part=part,region=region,ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed))
            print(part,region,observed,flush=True)
    report=dict(cases=len(cases),results=results,irq_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_irq.c').read_bytes()).hexdigest(),
                production_md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                limits=['Compiled68000: all336 bytes/nine stages/whole T/M1/palette polling; source-derived reader work supplied.',
                        'No playable-IRQ wiring, original video transfer values, hardware acknowledgement or full progression claim.'])
    (ROOT/'analysis/native_source_irq_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
