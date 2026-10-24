"""Native68000 execution of the continuous16D0 through fade to the first contour wait source-checked chain."""
import contextlib,io,json,os,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
from validate_native_room_contours_dirty import MODULES,WRAPPER

def main():
 folder=ROOT/'validation/native-room-contours-dirty';cases=json.loads((folder/'cases.json').read_bytes());host=json.loads((ROOT/'analysis/native_room_contours_dirty_report.json').read_bytes());assert host['passed'] and len(cases)==24
 for n,h in host['module_sha256'].items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 base=folder/'kernel';src=base/'src';src.mkdir(parents=True,exist_ok=True);rom=(ROOT/'input/original.sms').read_bytes();array=lambda values:'{'+','.join(str(v)+'UL' for v in values)+'}'
 lines=['static const u8 rom[]='+array(rom)+';',
 'typedef struct {u32 phase[12];u8 refresh,body[8192];u32 expected[24],events[768],points[2166];u8 states[83904],after_body[8192],patterns[16384],hero_before[475],hero_after[475],dirty_tiles[64],dirty_names[96];u32 dirty_palette;u8 dirty_sat;} Case;','static const Case cases[]={']
 for c in cases:
  fields=[array(c['phase']),str(c['refresh']),array(c['body']),array(c['expected']),array(c['events']+[0]*(768-len(c['events']))),array(c['points']+[0]*(2166-len(c['points']))),array(c['states']+[0]*(83904-len(c['states']))),array(c['after_body']),array(c['patterns']),array(c['hero_before']),array(c['hero_after']),array(c['dirty_tiles']),array(c['dirty_names']),str(c['dirty_palette'])+'UL',str(c['dirty_sat'])]
  lines.append('{'+','.join(fields)+'},')
 lines.append('};');(src/'expected.h').write_bytes(('\n'.join(lines)+'\n').encode())
 for n in MODULES:(src/(n+'.c')).write_bytes(('#include "../../../../megadrive/src/'+n+'.c"\n').encode())
 wrapper=WRAPPER.replace('#include "source_room_contours.h"','#include "../../../../megadrive/src/source_room_contours.h"\nstatic const u8 *expected_states;\nvolatile u32 gaw_ready_state_errors;\nvoid room_ready_expect(const u8 *p){expected_states=p;}')
 wrapper=wrapper.replace('#include "source_irq_video.h"','#include "../../../../megadrive/src/source_irq_video.h"')
 wrapper=wrapper.replace('s=t->states+t->points*736;','s=t->states;').replace(' t->points++;return 1;',' for(n=0;n<736;n++){if(s[n]!=expected_states[t->points*736+n])gaw_ready_state_errors++;}\n t->points++;return 1;')
 (src/'wrapper.c').write_bytes(wrapper.encode())
 (src/'main.c').write_bytes(r'''#include <genesis.h>
#include "expected.h"
u8 room_ready_case(const u32*,u8,const u8*,u8*,u32*,u32*,u32*,u8*);
const u8 *room_ready_patterns(void),*room_ready_hero_before(void),*room_ready_hero_after(void);
const u8 *room_dirty_tiles(void),*room_dirty_names(void);u32 room_dirty_palette(void);u8 room_dirty_sat(void);
void room_ready_expect(const u8*);
extern volatile u32 gaw_ready_state_errors;
volatile u32 gaw_ready_cases,gaw_ready_failures,gaw_ready_first_error;
volatile u16 gaw_ready_done;
static u8 body[8192],states[736];static u32 out[24],events[768],points[2166];
static void fail(u32 code){if(!gaw_ready_failures)gaw_ready_first_error=code;gaw_ready_failures++;}
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);SYS_disableInts();
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  const Case *c=cases+row;memcpy(body,c->body,8192);room_ready_expect(c->states);gaw_ready_state_errors=0;
  if(!room_ready_case(c->phase,c->refresh,rom,body,out,events,points,states))fail(row*100+1);
  for(n=0;n<24;n++)if(out[n]!=c->expected[n])fail(row*100+2);
  if(out[7]>128 || out[18]>114){fail(row*100+3);break;}
  for(n=0;n<out[7]*6;n++)if(events[n]!=c->events[n])fail(row*100+4);
  for(n=0;n<out[18]*19;n++)if(points[n]!=c->points[n])fail(row*100+5);
  if(gaw_ready_state_errors)fail(row*100+6);
  if(memcmp(body,c->after_body,8192))fail(row*100+7);
  if(memcmp(room_ready_patterns(),c->patterns,16384))fail(row*100+8);
  if(memcmp(room_ready_hero_before(),c->hero_before,475) || memcmp(room_ready_hero_after(),c->hero_after,475))fail(row*100+9);
  if(memcmp(room_dirty_tiles(),c->dirty_tiles,64) || memcmp(room_dirty_names(),c->dirty_names,96) || room_dirty_palette()!=c->dirty_palette || room_dirty_sat()!=c->dirty_sat)fail(row*100+10);
  gaw_ready_cases++;
 }
 gaw_ready_done=1;while(TRUE);return 0;
}
'''.encode())
 sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True)
 (base/'build.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-4000:]
 cart=base/'out/release/rom.bin';sy=symbols(base/'out/release/symbol.txt');results=[]
 for region in ['auto','pal']:
  state={}
  def observe(f,r):
   value=lambda n,size:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(size)),'big')
   state.update(frame=f,done=value('gaw_ready_done',2),cases=value('gaw_ready_cases',4),failures=value('gaw_ready_failures',4),first_error=value('gaw_ready_first_error',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cart,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(state.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert state['done'] and state['cases']==24 and not state['failures'],(region,state);results.append(dict(region=region,**state));print(results[-1],flush=True)
 report=dict(passed=True,cases=24,native_cases=48,results=results,module_sha256=host['module_sha256'],headers_sha256=host['headers_sha256'],source_cases_sha256=sha((folder/'cases.json').read_bytes()),test_rom_sha256=sha(cart.read_bytes()),playable_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),production_clock_wired=False,limits=['Dedicated68000 cartridge; physical IRQs disabled, continuous virtual source clock and live native IRQ/audio. Source-checked checkpoints, hero475 entry/return bytes, script/music fields, actors/history/masks and enemy patterns retained.','Other body/mirror bytes compare to host parity. Six controlled class0 destinations; native IRQ video mirrors bound; all16 contours drawn into mirror; physical renderer/pacing, boot entry, other classes or full campaign proof.'])
 (ROOT/'analysis/native_room_contours_dirty_68k_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())

if __name__=='__main__':main()
