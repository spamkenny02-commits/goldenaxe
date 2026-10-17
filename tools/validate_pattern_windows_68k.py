"""Bytewise compiled68000 comparison for long multi-command window boundaries."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_graphics_prefix import MODULES

def main():
 base=ROOT/'validation/pattern-windows-68k';src=base/'src';src.mkdir(parents=True,exist_ok=True)
 contexts=json.loads((ROOT/'analysis/native-room-finish-v0198/validation/native-room-finish/cases.json').read_text());rom=(ROOT/'input/original.sms').read_bytes()
 lines=['static const u8 low[]={'+','.join(map(str,rom[:32768]))+'};','static const u8 bank6[]={'+','.join(map(str,rom[0x18000:0x1c000]))+'};'];rows=[]
 for case,(length,mode) in enumerate([(295,0),(295,2),(324,1),(324,2),(325,0),(325,1),(1024,0),(1024,2)]):
  data=bytearray()
  for plane in range(4):
   for n in range(length):data.extend([0x81 if mode==1 or (mode==2 and n&1) else 1,(n*37+plane)&255])
   data.append(0)
  lines.append('static const u8 stream'+str(case)+'[]={'+','.join(map(str,data))+'};')
  for region in [262,313]:
   row=next(r for r in contexts if r['phase'][3]==region);phase=row['phase'][:];raster=193*3420-1 if case&1 else 0;phase[0]=raster%3420;phase[1]=raster//3420;phase[2]=0
   rows.append(dict(stream=case,phase=phase,ram=row['ram'],audio=row['audio'],refresh=case*31&255))
 lines+=['typedef struct {const u8 *stream;u32 phase[12];u8 ram[336],audio[400],refresh;} Case;','static const Case cases[]={']
 for row in rows:lines.append('{stream'+str(row['stream'])+',{'+','.join(str(v)+'UL' for v in row['phase'])+'},{'+','.join(map(str,row['ram']))+'},{'+','.join(map(str,row['audio']))+'},'+str(row['refresh'])+'},')
 (src/'expected.h').write_text('\n'.join(lines+['};'])+'\n')
 for name in MODULES:(src/(name+'.c')).write_text('#include "../../../megadrive/src/'+name+'.c"\n')
 for name in ['fast','scalar']:
  text=(ROOT/'validation/pattern-clock-batch'/(name+'.c')).read_text().replace('#include "source_pattern_clock.h"','#include "../../../megadrive/src/source_pattern_clock.h"\nextern u8 shared_pixels[16384];')
  text=text.replace('static u8 pixels[16384];u32 hash=2166136261UL;','u8 *pixels=shared_pixels;')
  text=text.replace('sizeof(pixels)','16384').replace(' for(n=0;n<16384;n++) hash=(hash^pixels[n])*16777619UL;','').replace('out[18]=hash;','out[18]=0;out[19]=0;')
  if name=='scalar':text=text.replace('for(n=0;n<16384;n++) pixel_output[n]=pixels[n];','for(n=0;n<16384;n++) if(pixel_output[n]!=pixels[n]) out[19]=1;')
  (src/(name+'.c')).write_text(text)
 reference=ROOT/'analysis/native-room-finish-v0198/megadrive/src/source_pattern_clock.c'
 (src/'reference.c').write_text(reference.read_text().replace('#include "source_pattern_clock.h"','#include "../../../megadrive/src/source_pattern_clock.h"').replace('source_graphics_prefix_class0(','source_graphics_prefix_scalar('))
 (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 prefix_fast_case(const u32*,u8,u8*,u8*,const u8*,const u8*,const u8*,u16,u32*,u32*,u8*);
u8 prefix_scalar_case(const u32*,u8,u8*,u8*,const u8*,const u8*,const u8*,u16,u32*,u32*,u8*);
u8 shared_pixels[16384];static u8 expected_pixels[16384],ram[2][336],audio[2][400];
static u32 output[2][20],events[2][384];
volatile u32 gaw_window_cases,gaw_window_failures;volatile u16 gaw_window_done;
int main(bool hard_reset)
{
 u16 row,n;
 VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) ram[0][n]=ram[1][n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[0][n]=audio[1][n]=cases[row].audio[n];
  for(n=0;n<384;n++) events[0][n]=events[1][n]=0;
  if(!prefix_fast_case(cases[row].phase,cases[row].refresh,ram[0],audio[0],low,bank6,cases[row].stream,0,output[0],events[0],expected_pixels)) gaw_window_failures++;
  if(!prefix_scalar_case(cases[row].phase,cases[row].refresh,ram[1],audio[1],low,bank6,cases[row].stream,0,output[1],events[1],expected_pixels)) gaw_window_failures++;
  for(n=0;n<20;n++) if(output[0][n]!=output[1][n]) gaw_window_failures++;
  for(n=0;n<336;n++) if(ram[0][n]!=ram[1][n]) gaw_window_failures++;
  for(n=0;n<400;n++) if(audio[0][n]!=audio[1][n]) gaw_window_failures++;
  for(n=0;n<384;n++) if(events[0][n]!=events[1][n]) gaw_window_failures++;
  gaw_window_cases++;
 }
 gaw_window_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
 sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True)
 (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2000:]
 symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=base/'out/release/rom.bin';results=[]
 for region in ['auto','pal']:
  observed={}
  def observe(frame,ram):
   def get(name,size):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(size)),'big')
   observed.update(frame=frame,done=get('gaw_window_done',2),cases=get('gaw_window_cases',4),failures=get('gaw_window_failures',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cartridge,150000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
  assert observed.get('done') and (observed['cases'],observed['failures'])==(len(rows),0),observed
  results.append(dict(region=region,**observed));print(results[-1],flush=True)
 report=dict(cases=len(rows),results=results,reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_pattern_clock.c').read_bytes()).hexdigest(),kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),limits=['Compiled68000 pairwise16384 pattern bytes,336RAM,400audio,all clock outputs and completeIRQ traces. Long295/324/325/1024-command planes around frame and65535T limits.','Both logical regions executed under both physical regions; original source full-chain proof and bare CPU profile are separate.'])
 (ROOT/'analysis/pattern_windows_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
