"""Run timed RNG C and its instruction clock on a dedicated68000 cartridge."""
import contextlib,io,json,os,re,subprocess
from run_core import ROOT,run
from source_rng_reference import source_rng
from archive_lossless_evidence import sha

def main():
 folder=ROOT/'validation/rng-timed-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True);host=json.loads((ROOT/'analysis/rng_timed_host_report.json').read_bytes());assert host['passed'];cases=json.loads((ROOT/'validation/rng-timed-host/boundary-cases.json').read_bytes());sdk=ROOT.parents[1]/'work/sgdk'
 lines=['static const u16 expected_seed[65536]={']
 values=[source_rng(seed,0)['seed'] for seed in range(65536)]
 lines += [','.join(map(str,values[n:n+16]))+',' for n in range(0,65536,16)]+['};','typedef struct {u32 input[4],expected[16];} Boundary;','static const Boundary boundary[]={']
 lines += ['{{'+','.join(map(str,r['input']))+'},{'+','.join(str(v)+'UL' for v in r['output'])+'}},' for r in cases]+['};']
 (src/'expected.h').write_bytes(('\n'.join(lines)+'\n').encode())
 for name in ['source_clock','source_rng','source_rng_timed']:(src/(name+'.c')).write_bytes(('#include "../../../megadrive/src/'+name+'.c"\n').encode())
 main=r'''#include <genesis.h>
#include "../../../megadrive/src/source_rng_timed.h"
#include "expected.h"
volatile u32 gaw_timed_cases,gaw_timed_failures,gaw_timed_first_error;
volatile u16 gaw_timed_done;
static u8 interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work)
{work->tstates=IRQ_T;work->fetches=IRQ_M;return 1;}
static void failure(u32 code) {if(!gaw_timed_failures)gaw_timed_first_error=code;gaw_timed_failures++;}
int main(bool hard_reset)
{
 SourceClock clock;SourceRngTimedOutput out;u8 state[2],value,initial,sample;u16 i,r,first;u32 seed,n,actual[16];const u8 refreshes[3]={0,127,255};
 VDP_setEnable(FALSE);SYS_disableInts();
 for(seed=0;seed<65536UL;seed++) for(r=0;r<3;r++) for(first=0;first<2;first++)
 {
  initial=first?refreshes[r]:(refreshes[r]&128)|((refreshes[r]-1)&127);
  if(!source_clock_init(&clock,262,0,initial,1,0,0)) failure(1);
  clock.first=first;state[0]=seed;state[1]=seed>>8;
  if(!source_rng_timed(&clock,state,&out,interrupt,0)) failure(2);
  sample=(refreshes[r]&128)|((refreshes[r]+17+(seed==0))&127);
  if(out.seed!=expected_seed[seed] || out.value!=(sample^(u8)expected_seed[seed]) || out.sampled_refresh!=sample || out.zero_replaced!=(seed==0) ||
     state[0]!=(u8)expected_seed[seed] || state[1]!=(expected_seed[seed]>>8) || clock.foreground_tstates!=(seed?130:135) ||
     clock.foreground_m1!=(seed?21:22) || clock.refresh!=((sample&128)|((sample+3)&127)) || clock.irq_count) failure(3);
  gaw_timed_cases++;
 }
 for(n=0;n<sizeof(boundary)/sizeof(boundary[0]);n++)
 {
  const Boundary *b=boundary+n;
  if(!source_clock_init(&clock,b->input[0],b->input[1],b->input[2],1,0,0)) failure(4);
  state[0]=b->input[3];state[1]=b->input[3]>>8;
  if(!source_rng_timed(&clock,state,&out,interrupt,0)) failure(5);
  actual[0]=out.seed;actual[1]=out.value;actual[2]=out.sampled_refresh;
  actual[3]=clock.raster;actual[4]=clock.until_vint;actual[5]=clock.elapsed;actual[6]=clock.foreground_tstates;actual[7]=clock.foreground_m1;
  actual[8]=clock.irq_tstates;actual[9]=clock.irq_m1;actual[10]=clock.refresh;actual[11]=clock.iff;actual[12]=clock.blocked;actual[13]=clock.pending;actual[14]=clock.first;actual[15]=clock.irq_count;
  for(i=0;i<16;i++) if(actual[i]!=b->expected[i]) failure(100+n);
  if(state[0]!=(u8)out.seed || state[1]!=(out.seed>>8)) failure(6);
  gaw_timed_cases++;
 }
 for(r=0;r<256;r++)
 {
  if(!source_clock_init(&clock,262,0,r,1,0,0) || !source_rng_read_refresh(&clock,&value,interrupt,0)) failure(7);
  if(value!=((r&128)|((r+1)&127)) || clock.foreground_tstates!=9 || clock.foreground_m1!=2) failure(8);
  gaw_timed_cases++;
 }
 gaw_timed_done=1;while(TRUE);return 0;
}
'''.replace('IRQ_T',str(host['irq_tstates'])).replace('IRQ_M',str(host['irq_fetches']))
 (src/'main.c').write_bytes(main.encode());env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix];built=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 cartridge=folder/'out/release/rom.bin';assert cartridge.stat().st_size<=0x400000;sy={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};results=[]
 for region in ['auto','pal']:
  observed={}
  def observe(f,ram):
   value=lambda key,n:int.from_bytes(bytes(ram[(sy[key]+i)^1] for i in range(n)),'big')
   observed.update(frame=f,done=value('gaw_timed_done',2),cases=value('gaw_timed_cases',4),failures=value('gaw_timed_failures',4),first_error=value('gaw_timed_first_error',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cartridge,100000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
  assert observed['done'] and observed['cases']==398048 and not observed['failures'],(region,observed);results.append(dict(region=region,**observed));print(region,observed,flush=True)
 r=dict(passed=True,results=results,native_cases=796096,module_sha256=host['module_sha256'],test_rom_sha256=sha(cartridge.read_bytes()),playable_rom_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),production_rng_integrated=False,limits=['Dedicated68000 test cartridge, native IRQs disabled; virtual source IRQ callback is the paused-audio563T/59M1 model. Controlled SourceClock entry states; no natural game clock claim.','Both fast and instruction-boundary paths execute; original gameplay ROM stays unchanged. Host seed mutation/failure checks are separate.'])
 assert all(sha((ROOT/'megadrive/src'/n).read_bytes())==h for n,h in host['module_sha256'].items());(ROOT/'analysis/rng_timed_68k_report.json').write_bytes((json.dumps(r,indent=2)+'\n').encode())
if __name__=='__main__':main()
