"""Add read-only map phase checkpoints to the graphics phase core."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/world-map-phase-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/graphics-load-phase-research-v0183/z80-graphics-load-phase.txt').read_text();anchor=' && pc!=0x24b9) return;';assert source.count(anchor)==1
 source=source.replace(anchor,' && pc!=0x24b9 && pc!=0x192a && pc!=0x192d && pc!=0x24bc) return;')
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstatic unsigned char gaw_map_extra[32768][8];\n__declspec(dllexport) const unsigned char *gaw_map_extra_events(void) { return (const unsigned char *)gaw_map_extra; }')
 anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'memcpy(gaw_map_extra[gaw_fore_phase_count],work_ram+0x10f8,8);'+anchor)
 modified=source.encode();target=folder/'z80-world-map-phase-extra.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_worldmapphaseextra_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/world-map-phase-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('World map observer built; original core source restored.')
if __name__=='__main__':main()
