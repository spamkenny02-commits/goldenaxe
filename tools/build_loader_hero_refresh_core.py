"""Observe global M1 and logical R at original foreground load checkpoints."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/loader-hero-refresh-v0183';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/hero-refresh-v0183/z80-hero-refresh.txt').read_text()
 anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstruct gaw_loader_entry { unsigned long long master;unsigned char ram[8192]; };\nstatic struct gaw_loader_entry gaw_loader_entries[128];static unsigned gaw_loader_entry_count;\n__declspec(dllexport) unsigned gaw_loader_entry_samples(void) { return gaw_loader_entry_count; }\n__declspec(dllexport) const unsigned char *gaw_loader_entry_events(void) { return (const unsigned char *)gaw_loader_entries; }')
 anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'if(pc==0x16d0 && gaw_loader_entry_count<128) { struct gaw_loader_entry *l=gaw_loader_entries+gaw_loader_entry_count++;l->master=gaw_elapsed;memcpy(l->ram,work_ram,8192); }'+anchor)
 anchor='gaw_fore_phase_count=gaw_actor_graphics_count=0;';assert source.count(anchor)==1;source=source.replace(anchor,'gaw_fore_phase_count=gaw_actor_graphics_count=gaw_loader_entry_count=0;')
 modified=source.encode();target=folder/'z80-loader-hero-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_loaderherorefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/loader-hero-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Graphics load M1/R observer built; original core source restored.')
if __name__=='__main__':main()
