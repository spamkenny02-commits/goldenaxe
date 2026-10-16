"""Unsupported command/memory/control loop must not commit RAM or PSG writes."""
import contextlib,ctypes as c,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from validate_native_audio_sequence import compile_helper,Output
from validate_native_audio_prefix import Work
from run_core import run

PROGRAMS=[[],[0xf3,0xe4,0xe1,7,0xec,0],[0xf6,0x80,0xde]]

def main():
    _,dll,function=compile_helper();rom=(ROOT/'input/original.sms').read_bytes()
    low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000])
    for number,program in enumerate(PROGRAMS):
        initial=bytearray((i*37+17)&255 for i in range(400));initial[0x40]=255;initial[0x43:0x45]=(0xc000 if number==0 else 0xde80).to_bytes(2,'little')
        initial[0x80:0x80+len(program)]=bytes(program);state=(c.c_uint8*400).from_buffer_copy(initial);work=Work();output=Output()
        assert not function(state,0x40,low,32768,bank,c.byref(work),c.byref(output))
        assert bytes(state)==initial and (work.tstates,work.fetches,output.de,output.count,output.unwind)==(0,0,0,0,0)
        assert output.error==[255,0xec,0xf6][number]
    folder=ROOT/'validation/native-audio-sequence-rejection-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    (src/'data.h').write_text('static const u8 low[]={'+','.join(map(str,rom[:32768]))+'};\nstatic const u8 bank6[]={'+','.join(map(str,rom[0x18000:0x1c000]))+'};\n')
    for name in ['source_audio_sequence','source_audio_priority','source_audio_memory']:
        (src/f'{name}.c').write_text(f'#include "../../../megadrive/src/{name}.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_audio_sequence.h"
#include "data.h"
static const u8 programs[3][6]={{0},{0xf3,0xe4,0xe1,7,0xec,0},{0xf6,0x80,0xde}};
static const u8 lengths[3]={0,6,3},errors[3]={255,0xec,0xf6};
static SourceAudioSequenceOutput output;
volatile u16 gaw_rejection_cases,gaw_rejection_failures,gaw_rejection_done;
int main(bool hard_reset)
{
 u8 state[400],expected[400],value;u16 row,n;SourceClockWork work;VDP_setEnable(FALSE);
 for(row=0;row<3;row++)
 {
  value=17;for(n=0;n<400;n++) {state[n]=value;value+=37;}
  state[0x40]=255;state[0x43]=row?0x80:0;state[0x44]=row?0xde:0xc0;
  for(n=0;n<lengths[row];n++) state[0x80+n]=programs[row][n];
  for(n=0;n<400;n++) expected[n]=state[n];
  if(source_audio_sequence(state,0x40,low,32768,bank6,&work,&output) || work.tstates || work.fetches ||
     output.de || output.count || output.unwind || output.error!=errors[row]) gaw_rejection_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_rejection_failures++;
  gaw_rejection_cases++;
 }
 gaw_rejection_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
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
            def value(name):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(2)),'big')
            observed.update(frame=frame,done=value('gaw_rejection_done'),cases=value('gaw_rejection_cases'),failures=value('gaw_rejection_failures'))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,300,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
        assert observed.get('done') and (observed['cases'],observed['failures'])==(3,0),(region,observed)
        results.append(dict(region=region,**observed));print(region,observed,flush=True)
    report=dict(host_cases=3,results=results,test_ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                limits=['API failure contract only: uncaptured RAM, EC after staged PSG/state changes, nonterminating F6.',
                        'All400 bytes restored, no emitted output list orwork committed; not SMS equivalence for unsupported paths.'])
    (ROOT/'analysis/audio_sequence_rejection_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
