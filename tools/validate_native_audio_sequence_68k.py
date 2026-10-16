"""Run all retained and new source sequence vectors on compiled68000, in parts."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run

def main():
    folder=ROOT/'validation/native-audio-sequence-68k';folder.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();fixture=json.loads((ROOT/'validation/native-audio-sequence/cases.json').read_text())
    suites=fixture['suites'];fields=fixture['fields'];extensions=json.loads((ROOT/'validation/native-audio-sequence/extension-cases.json').read_text())
    for suite in suites:
        for row in suite['cases']:row['patches']=[(fields[row['patches'][n]],row['patches'][n+1]) for n in range(0,len(row['patches']),2)]
    suites.extend(extensions);fields=sorted({offset for s in suites for row in s['cases'] for offset,_ in row['patches']});assert len(fields)<=255
    all_cases=[(index,row) for index,suite in enumerate(suites) for row in suite['cases']]
    low=[]
    for suite in suites:
        raw=(ROOT/suite['fixture']).read_bytes();assert hashlib.sha256(raw).hexdigest()==suite['fixture_sha256']
        assert raw[0x3430:0x3430+400]==bytes((i*37+17)&255 for i in range(400));low.append(raw[:32768])
    bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000];results=[]
    for part,start in enumerate(range(0,len(all_cases),30000)):
        cases=all_cases[start:start+30000];base=folder/f'part-{part}';src=base/'src';src.mkdir(parents=True,exist_ok=True)
        max_patches=max(len(row['patches']) for _,row in cases)
        lines=['static const u8 bank6[]={'+','.join(map(str,bank))+'};',
               'static const u8 low[][32768]={'+','.join('{'+','.join(map(str,data))+'}' for data in low)+'};',
               'static const u16 fields[]={'+','.join(map(str,fields))+'};',
               'static const u8 offset_count[]={'+','.join(str(len(s['offsets'])) for s in suites)+'};',
               'static const u16 input_offsets[][16]={'+','.join('{'+','.join(map(str,s['offsets']))+'}' for s in suites)+'};',
               f'typedef struct {{u8 suite,patch_count,unwind,input[16],patches[{max_patches*2}];u16 de;u32 tstates,fetches;}} SequenceCase;',
               'static const SequenceCase cases[]={']
        for index,row in cases:
            patches=[v for offset,value in row['patches'] for v in [fields.index(offset),value]]
            patches.extend([0]*(max_patches*2-len(patches)))
            lines.append('{'+','.join(map(str,[index,len(row['patches']),row['unwind']]))+',{'+','.join(map(str,row['input']))+'},{'+','.join(map(str,patches))+'},'+str(row['de'])+','+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        for name in ['source_audio_sequence','source_audio_priority','source_audio_memory']:
            (src/f'{name}.c').write_text(f'#include "../../../../megadrive/src/{name}.c"\n')
        (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_audio_sequence.h"
#include "expected.h"
volatile u32 gaw_sequence_cases,gaw_sequence_failures;
volatile u16 gaw_sequence_done;
static SourceAudioSequenceOutput output;
int main(bool hard_reset)
{
 u32 row;u16 n,offset;u8 state[400],expected[400],value,accepted,suite;
 SourceClockWork work;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  value=17;suite=cases[row].suite;
  for(n=0;n<400;n++) {state[n]=expected[n]=value;value+=37;}
  for(n=0;n<offset_count[suite];n++) {offset=input_offsets[suite][n];state[offset]=expected[offset]=cases[row].input[n];}
  for(n=0;n<cases[row].patch_count;n++) expected[fields[cases[row].patches[n*2]]]=cases[row].patches[n*2+1];
  accepted=source_audio_sequence(state,0x40,low[suite],32768,bank6,&work,&output);
  if(!accepted || output.error || output.count>512 || work.tstates!=cases[row].tstates || work.fetches!=cases[row].fetches ||
     output.de!=cases[row].de || output.unwind!=cases[row].unwind) gaw_sequence_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_sequence_failures++;
  gaw_sequence_cases++;
 }
 gaw_sequence_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
        env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
        args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
        built=subprocess.run(args,cwd=base,env=env,capture_output=True,text=True);(base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-3000:]
        cartridge=base/'out/release/rom.bin';symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
        for region in ['auto','pal']:
            observed={}
            def observe(frame,ram):
                if observed.get('done'):return
                def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
                observed.update(frame=frame,done=value('gaw_sequence_done',2),cases=value('gaw_sequence_cases',4),failures=value('gaw_sequence_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):run(cartridge,40000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(part,region,observed)
            results.append(dict(part=part,region=region,ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed));print(part,region,observed,flush=True)
    report=dict(cases=len(all_cases),results=results,
                helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_sequence.c').read_bytes()).hexdigest(),
                limits=['Actual compiled68000 under GPG; all400 bytes,T/M1,DE/unwind from independent source fixtures/models.',
                        'PGS write lists not independently compared here; production audio checks remain required.',
                        'Unsupported R/context commands andfull native clock remain open.'])
    (ROOT/'analysis/native_audio_sequence_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
