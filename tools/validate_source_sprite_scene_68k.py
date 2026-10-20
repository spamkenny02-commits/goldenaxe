"""Run native68000 SAT production against the original Z80 RAM results."""
import contextlib,io,json,os,re,subprocess
from pathlib import Path
from run_core import run
from validate_source_sprite_scene import ROOT,sha,vectors
MAIN=r'''
#include <genesis.h>
#include "source_sprite_scene.h"
extern const u8 scene_inputs[][8192],scene_expected[][7936],scene_bank[16384];
static u8 ram[8192];
volatile u32 gaw_checks,gaw_failures;volatile u16 gaw_done;
int main(bool reset) {
 u16 row,n;SourceSpriteSceneOutput out;(void)reset;SYS_disableInts();VDP_setEnable(FALSE);
 for(row=0;row<SCENE_CASES;row++) {
  memcpy(ram,scene_inputs[row],8192);
  if(!source_sprite_scene(ram,scene_bank,&out)) gaw_failures++;
  else {
   for(n=2;n<7936;n++) if(ram[n]!=scene_expected[row][n]) gaw_failures++;
   if(out.bank!=12 || out.y_end!=((u16)ram[0x24]|((u16)ram[0x25]<<8)) ||
      out.xy_end!=((u16)ram[0x26]|((u16)ram[0x27]<<8)) || out.count>64) gaw_failures++;
  }
  gaw_checks++;
 }
 gaw_done=1;while(TRUE) __asm__ volatile("nop");return 0;
}
'''
def main():
 rom,rows=vectors();source=ROOT/'validation/source-sprite-scene';records={}
 for region in ['ntsc','pal']:
  raw=(source/(region+'-records.bin')).read_bytes();stride=7938;assert len(raw)==len(rows)*stride
  decoded={int.from_bytes(raw[n:n+2],'little'):raw[n+2:n+stride] for n in range(0,len(raw),stride)}
  assert len(decoded)==len(rows)
  if records:assert records==decoded
  records=decoded
 folder=ROOT/'validation/source-sprite-scene-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
 (src/'inputs.bin').write_bytes(b''.join(raw for _,raw in rows));(src/'expected.bin').write_bytes(b''.join(records[n] for n in range(len(rows))));(src/'bank.bin').write_bytes(rom[0x30000:0x34000])
 asm='.section .rodata\n.align 2\n'
 for name in ['inputs','expected','bank']:asm+='.global scene_'+name+'\nscene_'+name+':\n.incbin "src/'+name+'.bin"\n.align 2\n'
 (src/'assets.s').write_bytes(asm.encode());(src/'main.c').write_bytes(('#define SCENE_CASES '+str(len(rows))+'\n'+MAIN).encode())
 (src/'source_sprite_scene.c').write_bytes(b'#include "../../../megadrive/src/source_sprite_scene.c"\n');(src/'source_sprite_scene.h').write_bytes(b'#include "../../../megadrive/src/source_sprite_scene.h"\n')
 sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];temp=folder/'compiler-tmp';temp.mkdir(exist_ok=True)
 for key in ['TMPDIR','TMP','TEMP']:env[key]=temp.as_posix()
 path=sdk.as_posix();unix='/'+path[0].lower()+path[2:];built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
 symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))};results=[]
 for region in ['ntsc','pal']:
  observed={}
  def observe(frame,ram):
   def value(name,width):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+n)&65535)^1] for n in range(width)),'big')
   observed.update(frame=frame,done=value('gaw_done',2),checks=value('gaw_checks',4),failures=value('gaw_failures',4))
  with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',2000,folder/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(observed.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert observed['done'] and observed['checks']==len(rows) and not observed['failures'],observed
  results.append(dict(region=region,**observed));print(region,observed,flush=True)
 report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),source_report_sha256=sha((ROOT/'analysis/source_sprite_scene_report.json').read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_sprite_scene.c','source_sprite_scene.h']},results=results,compared_ram_bytes_per_case=7934,limits=['OriginalZ80 expected records from both regions must match. Native68000 source data/ROM bank pointer translation, all captured/controlled RAM results checked. No IRQ interleaving/source cycle accounting, live actor evolution, whole-game or render deadline proof.'])
 (ROOT/'analysis/source_sprite_scene_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
