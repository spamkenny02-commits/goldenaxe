"""Execute all native audio-prefix vectors in an isolated SGDK cartridge."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run

def main():
 folder=ROOT/'validation/native-audio-prefix-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve();data=json.loads((ROOT/'validation/native-audio-prefix/cases.json').read_text());fields=data['fields'];cases=data['cases'];bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]
 lines=['static const u8 bank6[]={'+','.join(str(v) for v in bank)+'};','static const u16 fields[]={'+','.join(str(v) for v in fields)+'};',f'typedef struct {{u8 kind,salt,cleared,gate;u8 input[{len(fields)}],expected[{len(fields)}];u32 tstates,fetches;}} AudioCase;','static const AudioCase cases[]={']
 for row in cases:lines.append('{'+','.join(str(row[k]) for k in ['kind','salt','cleared','gate'])+',{'+','.join(str(v) for v in row['input'])+'},{'+','.join(str(v) for v in row['expected'])+'},'+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL},')
 lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n');(src/'source_audio_prefix.c').write_text('#include "../../../megadrive/src/source_audio_prefix.c"\n')
 (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_audio_prefix.h"
#include "expected.h"
volatile u32 gaw_audio_cases,gaw_audio_failures;
volatile u16 gaw_audio_done;
int main(bool hard_reset)
{
 u32 row;u16 n;u8 state[400],expected[400],value,gate;SourceClockWork work;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  value=cases[row].salt;
  for(n=0;n<400;n++) { state[n]=expected[n]=value;value+=37; }
  for(n=0;n<sizeof(fields)/sizeof(fields[0]);n++) state[fields[n]]=expected[fields[n]]=cases[row].input[n];
  if(cases[row].cleared) { for(n=5;n<400;n++) expected[n]=0;expected[5]=128; }
  for(n=0;n<sizeof(fields)/sizeof(fields[0]);n++) expected[fields[n]]=cases[row].expected[n];
  gate=0;work.tstates=work.fetches=0;
  switch(cases[row].kind)
  {
   case 0:source_audio_tempo(state,&work);break;
   case 1:source_audio_stop(state,&work);break;
   case 2:source_audio_fade(state,&work);break;
   case 3:source_audio_arbitrate(state,bank6,&work);break;
   case 4:gate=source_audio_gate(state,&work);break;
   default:gaw_audio_failures++;break;
  }
  if(work.tstates!=cases[row].tstates || work.fetches!=cases[row].fetches || gate!=cases[row].gate) gaw_audio_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_audio_failures++;
  gaw_audio_cases++;
 }
 gaw_audio_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
 env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
 built=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-3000:]
 cartridge=folder/'out/release/rom.bin';symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};rows=[]
 for region in ['auto','pal']:
  observed={}
  def observe(frame,ram):
   if observed.get('done'):return
   def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
   observed.update(frame=frame,done=value('gaw_audio_done',2),cases=value('gaw_audio_cases',4),failures=value('gaw_audio_failures',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cartridge,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(region,observed)
  rows.append(dict(region=region,**observed));print(region,'68000 audio prefix execution:',observed,flush=True)
 report=dict(rows=rows,test_ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),production_ROM_changed=False,production_audio_replaced=False,limits=['All host vectors run on actual compiled68000 code under GPG PAL/NTSC. Each400-byte state compared directly from losslessly encoded reference outputs. Semantic work/state only,no PSG writes; reader composition/production integration/hardware remain open.'])
 (ROOT/'analysis/native_audio_prefix_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
