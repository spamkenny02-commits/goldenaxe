"""Run the original native dispatch C and reference vectors on compiled 68000."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_audio_dispatch import make_cases

def main():
    folder=ROOT/'validation/native-audio-dispatch-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();cases=make_cases();bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]
    lines=['static const u8 bank6[]={'+','.join(map(str,bank))+'};',
           'typedef struct {u8 command,latch,flags,salt,accepted,mute,count,writes[4],expected[400];u32 tstates,fetches;} DispatchCase;',
           'static const DispatchCase cases[]={']
    for row in cases:
        values=[row[k] for k in ['command','latch','flags','salt','accepted','mute']]+[len(row['writes'])]
        lines.append('{'+','.join(map(str,values))+',{'+','.join(map(str,row['writes']+[0]*(4-len(row['writes']))))+'},{'+','.join(map(str,row['expected']))+'},'+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL},')
    lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
    for name in ['source_audio_dispatch','source_audio_prefix']:
        (src/f'{name}.c').write_text(f'#include "../../../megadrive/src/{name}.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_audio_dispatch.h"
#include "expected.h"
volatile u32 gaw_dispatch_cases,gaw_dispatch_failures;
volatile u16 gaw_dispatch_done;
int main(bool hard_reset)
{
 u32 row;u16 n;u8 state[400],value,accepted;SourceClockWork work;SourceAudioDispatchOutput output;
 VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  value=cases[row].salt;
  for(n=0;n<400;n++) {state[n]=value;value+=37;}
  state[5]=cases[row].command;state[15]=cases[row].latch;state[0x160]=cases[row].flags;
  accepted=source_audio_dispatch(state,bank6,&work,&output);
  if(accepted!=cases[row].accepted || work.tstates!=cases[row].tstates || work.fetches!=cases[row].fetches ||
     output.mute!=cases[row].mute || output.count!=cases[row].count) gaw_dispatch_failures++;
  for(n=0;n<output.count && n<4;n++) if(output.writes[n]!=cases[row].writes[n]) gaw_dispatch_failures++;
  for(n=0;n<400;n++) if(state[n]!=cases[row].expected[n]) gaw_dispatch_failures++;
  gaw_dispatch_cases++;
 }
 gaw_dispatch_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
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
            observed.update(frame=frame,done=value('gaw_dispatch_done',2),cases=value('gaw_dispatch_cases',4),failures=value('gaw_dispatch_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,5000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
        assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(region,observed)
        results.append(dict(region=region,**observed));print(region,observed,flush=True)
    report=dict(results=results,test_ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_dispatch.c').read_bytes()).hexdigest(),
                limits=['Isolated compiled68000 execution under GPG; all400 bytes, T/M1 and explicit PSG decisions compared.',
                        'No full game or hardware proof; unaudited commands reject without mutation.'])
    (ROOT/'analysis/native_audio_dispatch_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
