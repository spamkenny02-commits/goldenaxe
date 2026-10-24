"""Execute continuous16D0->18E1 source-checked vectors on native68000."""
import contextlib,io,json,os,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
from validate_native_room_graphics import MODULES,WRAPPER

def main():
 folder=ROOT/'validation/native-room-graphics';cases=json.loads((folder/'cases.json').read_bytes());host=json.loads((ROOT/'analysis/native_room_graphics_report.json').read_bytes());assert host['passed'] and len(cases)==24
 for n,h in host['module_sha256'].items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 base=folder/'kernel';src=base/'src';src.mkdir(parents=True,exist_ok=True);rom=(ROOT/'input/original.sms').read_bytes()
 array=lambda values:'{'+','.join(str(v)+'UL' for v in values)+'}'
 lines=['static const u8 rom[]='+array(rom)+';',
 'typedef struct {u32 phase[12];u16 room;u8 refresh,hud[16],ram[336],audio[400],history[16],masks[256];u32 expected[50],events[384],points[608];u8 states[23552],after_history[16],after_masks[256],actors[768],patterns[16384];} Case;',
 'static const Case cases[]={']
 for c in cases:
  fields=[array(c['phase']),str(c['room']),str(c['refresh']),array(c['hud']),array(c['ram']),array(c['audio']),array(c['history']),array(c['masks']),array(c['expected']),array(c['events']+[0]*(384-len(c['events']))),array(c['points']+[0]*(608-len(c['points']))),array(c['states']+[0]*(23552-len(c['states']))),array(c['after_history']),array(c['after_masks']),array(c['actors']),array(c['patterns'])]
  lines.append('{'+','.join(fields)+'},')
 lines.append('};');(src/'expected.h').write_bytes(('\n'.join(lines)+'\n').encode())
 for n in MODULES:(src/(n+'.c')).write_bytes(('#include "../../../../megadrive/src/'+n+'.c"\n').encode())
 # Compare every736-byte checkpoint against ROM immediately. Retaining32
 # states in MD RAM starves SGDK startup allocations before main is entered.
 wrapper=WRAPPER.replace('#include "source_room_load.h"','#include "../../../../megadrive/src/source_room_load.h"\nstatic const u8 *expected_states;\nvolatile u32 gaw_graphics_state_errors;\nvoid room_load_expect_states(const u8 *p){expected_states=p;}')
 wrapper=wrapper.replace('state=p->states+p->points*736;','state=p->states;')
 wrapper=wrapper.replace('p->snapshots[p->points*19+18]=pc;', 'for(n=0;n<736;n++){if(state[n]!=expected_states[p->points*736+n])gaw_graphics_state_errors++;}\n p->snapshots[p->points*19+18]=pc;')
 (src/'wrapper.c').write_bytes(wrapper.encode())
 (src/'main.c').write_bytes(r'''#include <genesis.h>
#include "expected.h"
u8 room_load_case(const u32*,u8,u8*,u8*,const u8*,const u8*,u16,const u8*,const u8*,const u8*,const u8*,const u8*,const u8*,const u8*,u8*,u8*,u8*,u32*,u32*,u32*,u8*);
const u8 *room_load_patterns(void);
void room_load_expect_states(const u8*);
extern volatile u32 gaw_graphics_state_errors;
volatile u32 gaw_graphics_cases,gaw_graphics_failures,gaw_graphics_first_error;
volatile u16 gaw_graphics_done;
static u8 ram[336],audio[400],history[16],masks[256],actors[768],states[736];
static u32 out[50],events[384],points[608];
static void fail(u32 code){if(!gaw_graphics_failures)gaw_graphics_first_error=code;gaw_graphics_failures++;}
int main(bool hard_reset)
{
 u16 row,n;const u8 *pixels;
 VDP_setEnable(FALSE);SYS_disableInts();
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  const Case *c=cases+row;
  memcpy(ram,c->ram,336);memcpy(audio,c->audio,400);memcpy(history,c->history,16);memcpy(masks,c->masks,256);
  room_load_expect_states(c->states);gaw_graphics_state_errors=0;
  if(!room_load_case(c->phase,c->refresh,ram,audio,rom,rom+0x18000,c->room,rom+(8+(c->room>>7))*16384UL,rom+0x3c010,rom+0x8000,rom+0x2c000,rom+0x10000,c->hud,rom,history,masks,actors,out,events,points,states))fail(row*100+1);
  for(n=0;n<50;n++)if(out[n]!=c->expected[n])fail(row*100+2);
  if(out[7]>64 || out[49]>32){fail(row*100+3);break;}
  for(n=0;n<out[7]*6;n++)if(events[n]!=c->events[n])fail(row*100+4);
  for(n=0;n<out[49]*19;n++)if(points[n]!=c->points[n])fail(row*100+5);
  if(gaw_graphics_state_errors)fail(row*100+6);
  if(memcmp(history,c->after_history,16) || memcmp(masks,c->after_masks,256) || memcmp(actors,c->actors,768))fail(row*100+7);
  pixels=room_load_patterns();for(n=0;n<16384;n++)if(pixels[n]!=c->patterns[n])fail(row*100+8);
  gaw_graphics_cases++;
 }
 gaw_graphics_done=1;while(TRUE);return 0;
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
   state.update(frame=f,done=value('gaw_graphics_done',2),cases=value('gaw_graphics_cases',4),failures=value('gaw_graphics_failures',4),first_error=value('gaw_graphics_first_error',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cart,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(state.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert state['done'] and state['cases']==24 and not state['failures'],(region,state)
  results.append(dict(region=region,**state));print(results[-1],flush=True)
 report=dict(passed=True,cases=24,native_cases=48,results=results,module_sha256=host['module_sha256'],headers_sha256=host['headers_sha256'],source_cases_sha256=sha((folder/'cases.json').read_bytes()),test_rom_sha256=sha(cart.read_bytes()),playable_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),production_clock_wired=False,limits=['Dedicated68000 cartridge, physical IRQs disabled; same continuous virtual source clock and live native IRQ/audio. All source-checked checkpoints, events, history/masks, actors and written VRAM ranges retained.','Other mirror bytes and scratch hashes compare to host parity. Six controlled destinations only; no physical video pacing, global boot clock, hero/tail or full campaign proof.'])
 (ROOT/'analysis/native_room_graphics_68k_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())

if __name__=='__main__':main()
