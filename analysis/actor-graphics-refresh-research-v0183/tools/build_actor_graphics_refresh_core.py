"""Observe global M1 and logical R at original foreground load checkpoints."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/actor-graphics-refresh-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/actor-prefix-refresh-v0183/z80-actor-prefix-refresh.txt').read_text()
 anchor=' && pc!=0x1853) return;';assert source.count(anchor)==1
 source=source.replace(anchor,' && pc!=0x1853 && pc!=0x18ac && pc!=0x18af && pc!=0x18b7 && pc!=0x18e1) return;')
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstruct gaw_actor_graphics { unsigned long long master;unsigned allocated,pad;unsigned char patterns[8192]; };\nstatic struct gaw_actor_graphics gaw_actor_graphics_records[128];static unsigned gaw_actor_graphics_count;\n__declspec(dllexport) unsigned gaw_actor_graphics_samples(void) { return gaw_actor_graphics_count; }\n__declspec(dllexport) const unsigned char *gaw_actor_graphics_events(void) { return (const unsigned char *)gaw_actor_graphics_records; }')
 anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'if(pc==0x18e1 && gaw_actor_graphics_count<128) { struct gaw_actor_graphics *g=gaw_actor_graphics_records+gaw_actor_graphics_count++;g->master=gaw_elapsed;g->allocated=work_ram[0x67];memcpy(g->patterns,vram+0x2000,8192); }'+anchor)
 anchor='gaw_fore_phase_count=0;';assert source.count(anchor)==1;source=source.replace(anchor,'gaw_fore_phase_count=gaw_actor_graphics_count=0;')
 modified=source.encode();target=folder/'z80-actor-graphics-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_actorgraphicsrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/actor-graphics-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics load M1/R observer built; original core source restored.')
if __name__=='__main__':main()
