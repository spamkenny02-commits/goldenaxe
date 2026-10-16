"""Execute every native pitch vector in an isolated SGDK68000 cartridge."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run

def main():
    folder=ROOT/'validation/native-audio-pitch-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();fixture=json.loads((ROOT/'validation/native-audio-pitch/cases.json').read_text())
    fields=fixture['fields'];cases=fixture['cases'];rom=(ROOT/'input/original.sms').read_bytes()
    lines=['static const u8 bank6[]={'+','.join(map(str,rom[0x18000:0x1c000]))+'};',
           'static const u8 low[]={'+','.join(map(str,rom[:32768]))+'};',
           'static const u16 fields[]={'+','.join(map(str,fields))+'};',
           f'typedef struct {{u16 offset,de,expected_de,return_address,hl;u8 salt,zero,accepted,unwind,input[{len(fields)}],expected[{len(fields)}];u32 tstates,fetches;}} PitchCase;',
           'static const PitchCase cases[]={']
    for r in cases:
        values=[r[k] for k in ['offset','de','expected_de','return_address','hl','salt']]+[int(r.get('zero_baseline',False)),r['accepted'],r['unwind']]
        lines.append('{'+','.join(map(str,values))+',{'+','.join(map(str,r['input']))+'},{'+','.join(map(str,r['expected']))+'},'+str(r['tstates'])+'UL,'+str(r['fetches'])+'UL},')
    lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
    for name in ['source_audio_pitch','source_audio_memory']:
        (src/f'{name}.c').write_text(f'#include "../../../megadrive/src/{name}.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_audio_pitch.h"
#include "expected.h"
volatile u32 gaw_pitch_cases,gaw_pitch_failures;
volatile u16 gaw_pitch_done;
int main(bool hard_reset)
{
 u32 row;u16 n,de,offset;u8 state[400],expected[400],value,accepted;
 SourceClockWork work;SourceAudioPitchOutput output;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  value=cases[row].salt;de=cases[row].de;offset=cases[row].offset;
  for(n=0;n<400;n++) {state[n]=expected[n]=cases[row].zero?0:value;value+=37;}
  for(n=0;n<sizeof(fields)/sizeof(fields[0]);n++)
  {state[offset+fields[n]]=cases[row].input[n];expected[offset+fields[n]]=cases[row].expected[n];}
  accepted=source_audio_pitch(state,offset,low,32768,bank6,cases[row].return_address,&de,&work,&output);
  if(accepted!=cases[row].accepted || work.tstates!=cases[row].tstates || work.fetches!=cases[row].fetches ||
     de!=cases[row].expected_de || output.hl!=cases[row].hl || output.unwind!=cases[row].unwind) gaw_pitch_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_pitch_failures++;
  gaw_pitch_cases++;
 }
 gaw_pitch_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
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
            observed.update(frame=frame,done=value('gaw_pitch_done',2),cases=value('gaw_pitch_cases',4),failures=value('gaw_pitch_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,40000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
        assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(region,observed)
        results.append(dict(region=region,**observed));print(region,observed,flush=True)
    report=dict(results=results,test_ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_pitch.c').read_bytes()).hexdigest(),
                limits=['Actual compiled68000 under GPG; all400 bytes,T/M1,HL/DE/unwind compared directly.',
                        'Three unavailable-memory reads reject without mutation; other source RAM,hardware/full-game timing remain open.'])
    (ROOT/'analysis/native_audio_pitch_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
