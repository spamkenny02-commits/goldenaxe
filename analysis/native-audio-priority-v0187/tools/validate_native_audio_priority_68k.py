"""Compiled68000 execution of all queue/standalone restoration vectors."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run

def main():
    folder=ROOT/'validation/native-audio-priority-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();fixture=json.loads((ROOT/'validation/native-audio-priority/cases.json').read_text())
    fields=fixture['fields'];cases=fixture['cases'];bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]
    lines=['static const u8 bank6[]={'+','.join(map(str,bank))+'};',
           'static const u16 fields[]={'+','.join(map(str,fields))+'};',
           f'typedef struct {{u8 kind,salt,accepted,count,write,input[{len(fields)}],expected[{len(fields)}];u16 de,expected_de;u32 tstates,fetches;}} PriorityCase;',
           'static const PriorityCase cases[]={']
    for r in cases:
        values=[r['kind'],r['salt'],r['accepted'],len(r['writes']),r['writes'][0] if r['writes'] else 0]
        lines.append('{'+','.join(map(str,values))+',{'+','.join(map(str,r['input']))+'},{'+','.join(map(str,r['expected']))+'},'+','.join(map(str,[r['de'],r['expected_de']]))+','+str(r['tstates'])+'UL,'+str(r['fetches'])+'UL},')
    lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
    (src/'source_audio_priority.c').write_text('#include "../../../megadrive/src/source_audio_priority.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_audio_priority.h"
#include "expected.h"
volatile u32 gaw_priority_cases,gaw_priority_failures;
volatile u16 gaw_priority_done;
int main(bool hard_reset)
{
 u32 row;u16 n,de;u8 state[400],expected[400],value,accepted;
 SourceClockWork work;SourceAudioDispatchOutput output;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  value=cases[row].salt;de=cases[row].de;
  for(n=0;n<400;n++) {state[n]=expected[n]=value;value+=37;}
  for(n=0;n<sizeof(fields)/sizeof(fields[0]);n++)
  {state[fields[n]]=cases[row].input[n];expected[fields[n]]=cases[row].expected[n];}
  if(cases[row].kind) accepted=source_audio_restore(state,bank6,state[14],&de,&work,&output);
  else accepted=source_audio_priority(state,bank6,&de,&work,&output);
  if(accepted!=cases[row].accepted || work.tstates!=cases[row].tstates || work.fetches!=cases[row].fetches ||
     de!=cases[row].expected_de || output.mute || output.count!=cases[row].count) gaw_priority_failures++;
  if(output.count && output.writes[0]!=cases[row].write) gaw_priority_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_priority_failures++;
  gaw_priority_cases++;
 }
 gaw_priority_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
    args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
    built=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-3000:]
    cartridge=folder/'out/release/rom.bin';symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,ram):
            if observed.get('done'):return
            def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
            observed.update(frame=frame,done=value('gaw_priority_done',2),cases=value('gaw_priority_cases',4),failures=value('gaw_priority_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,20000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
        assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(region,observed)
        results.append(dict(region=region,**observed));print(region,observed,flush=True)
    report=dict(results=results,test_ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_priority.c').read_bytes()).hexdigest(),
                limits=['Compiled68000 under GPG; all400 bytes, T/M1/DE and explicit PSG decisions.',
                        '15 invalid paths reject without mutation. Not a physical-console or full game proof.'])
    (ROOT/'analysis/native_audio_priority_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
