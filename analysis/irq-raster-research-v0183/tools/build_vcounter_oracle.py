"""Build isolated wrapper around unchanged GPG vdp_hvc_r,restoring all globals."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/vcounter-oracle-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes();source=(ROOT/'analysis/irq-raster-v0183/z80-irq-raster.txt').read_text()
 wrapper='''
__declspec(dllexport) unsigned gaw_test_vcounter(unsigned line,unsigned delta,unsigned lines,unsigned overflow)
{
 unsigned saved_line=v_counter,saved_base=mcycles_vdp,saved_lines=lines_per_frame,saved_max=vc_max;
 unsigned saved_latch=hvc_latch,saved_reg=reg[1],saved_interlace=interlaced,result;
 v_counter=line;mcycles_vdp=0;lines_per_frame=lines;vc_max=overflow;
 hvc_latch=1;reg[1]&=~4;interlaced=0;
 result=(vdp_hvc_r(delta)>>8)&255;
 v_counter=saved_line;mcycles_vdp=saved_base;lines_per_frame=saved_lines;vc_max=saved_max;
 hvc_latch=saved_latch;reg[1]=saved_reg;interlaced=saved_interlace;
 return result;
}
'''
 anchor='void z80_run(unsigned int cycles)';assert source.count(anchor)==1;modified=source.replace(anchor,wrapper+'\n'+anchor).encode();target=folder/'z80-vcounter-oracle.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_vcounteroracle_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/vcounter-oracle-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('VCounter oracle wrapper built; source restored.')
if __name__=='__main__':main()
