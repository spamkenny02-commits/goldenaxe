"""Read-only HUD phase checkpoints and16-byte caller context."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/map-hud-phase-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/world-map-phase-research-v0183/z80-world-map-phase-extra.txt').read_text();anchor=' && pc!=0x24bc) return;';assert source.count(anchor)==1
 source=source.replace(anchor,' && pc!=0x24bc && pc!=0x1de5 && pc!=0x1de8 && pc!=0xb95 && pc!=0x22a3 && pc!=0x1deb && pc!=0x24bf) return;')
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstatic unsigned char gaw_hud_context[32768][16];\n__declspec(dllexport) const unsigned char *gaw_hud_context_events(void) { return (const unsigned char *)gaw_hud_context; }')
 anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'{ unsigned char *h=gaw_hud_context[gaw_fore_phase_count];h[0]=work_ram[0x318];memcpy(h+1,work_ram+0xda,4);memcpy(h+5,work_ram+0xcf,9);h[14]=work_ram[0xbf];h[15]=work_ram[0xf1]; }'+anchor)
 modified=source.encode();target=folder/'z80-map-hud-phase.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_maphudphase_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/map-hud-phase-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Map/HUD observer built; original core source restored.')
if __name__=='__main__':main()
