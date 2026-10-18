"""Build a separate read-only native instruction-cost observer; restore source."""
import hashlib
import subprocess
import sys
from actor_reference import ROOT

OBSERVER=r'''
#include <string.h>
/* GAW_COST: physical master deltas attributed to the preceding instruction.
 * Host-only buffers; never changes a CPU register, memory or emulated cycle. */
#define GAW_COST_BINS 4097
static unsigned long long gaw_cost_master[24][GAW_COST_BINS];
static unsigned gaw_cost_instructions[24][GAW_COST_BINS];
static unsigned gaw_cost_start,gaw_cost_stop,gaw_cost_period,gaw_cost_case,gaw_cost_active,gaw_cost_valid,gaw_cost_pc,gaw_cost_bad;
static long long gaw_cost_last;
__declspec(dllexport) void gaw_cost_config(unsigned start,unsigned stop,unsigned period) {
 memset(gaw_cost_master,0,sizeof(gaw_cost_master));memset(gaw_cost_instructions,0,sizeof(gaw_cost_instructions));
 gaw_cost_start=start;gaw_cost_stop=stop;gaw_cost_period=period;gaw_cost_case=~0U;
 gaw_cost_active=gaw_cost_valid=gaw_cost_bad=0;gaw_cost_last=0;
}
__declspec(dllexport) void gaw_cost_next_frame(void) {gaw_cost_last-=gaw_cost_period;}
__declspec(dllexport) unsigned gaw_cost_cases(void) {return gaw_cost_case+1;}
__declspec(dllexport) unsigned gaw_cost_errors(void) {return gaw_cost_bad;}
__declspec(dllexport) const unsigned long long *gaw_cost_master_data(void) {return &gaw_cost_master[0][0];}
__declspec(dllexport) const unsigned *gaw_cost_instruction_data(void) {return &gaw_cost_instructions[0][0];}
static void gaw_cost_observe(unsigned pc) {
 if(gaw_cost_active && gaw_cost_valid) {
  long long delta=(long long)m68k.cycles-gaw_cost_last;
  unsigned bin=gaw_cost_pc<0x40000?(gaw_cost_pc>>6):4096;
  if(delta<0 || delta>gaw_cost_period) gaw_cost_bad++;
  else {gaw_cost_master[gaw_cost_case][bin]+=(unsigned long long)delta;gaw_cost_instructions[gaw_cost_case][bin]++;}
 }
 if(pc==gaw_cost_start) {
  if(gaw_cost_active) gaw_cost_bad++;
  gaw_cost_case++;gaw_cost_active=gaw_cost_case<24;
  if(!gaw_cost_active) gaw_cost_bad++;
 }
 if(pc==gaw_cost_stop) gaw_cost_active=0;
 gaw_cost_pc=pc;gaw_cost_last=m68k.cycles;gaw_cost_valid=gaw_cost_active;
}
'''


def main():
    folder=ROOT/'validation/md-instruction-cost';folder.mkdir(exist_ok=True)
    source=ROOT.parents[1]/'work/genesis-plus-gx/core/m68k/m68kcpu.c';original=source.read_bytes();text=original.decode()
    anchor='static void gaw_md_observe(unsigned pc) {';assert text.count(anchor)==1
    modified=text.replace(anchor,OBSERVER+'\n'+anchor+'\n gaw_cost_observe(pc);').encode()
    (folder/'m68kcpu-observer.txt').write_bytes(modified)
    (folder/'m68kcpu-original.sha256').write_text(hashlib.sha256(original).hexdigest()+'\n')
    try:
        source.write_bytes(modified)
        result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_cost_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
        (folder/'core-build.log').write_text(result.stdout+result.stderr);assert not result.returncode,result.stdout+result.stderr
    finally:source.write_bytes(original)
    assert source.read_bytes()==original
    print('Read-only cost core built; original emulator source restored.')


if __name__=='__main__':main()
