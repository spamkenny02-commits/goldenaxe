"""Add read-only source graphics buffer hashes to the audited observer."""
import subprocess
import sys
from actor_reference import ROOT

def main():
    folder=ROOT/'analysis/graphics-data-observer-v0198';folder.mkdir(exist_ok=True)
    path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
    source=(ROOT/'analysis/graphics-load-refresh-v0183/z80-graphics-load-refresh.txt').read_text()
    anchor='static unsigned gaw_fore_phase_count;';assert source.count(anchor)==1
    source=source.replace(anchor,anchor+'''
static unsigned gaw_graphics_hashes[32768][5];
__declspec(dllexport) const unsigned *gaw_graphics_hash_events(void) { return &gaw_graphics_hashes[0][0]; }
static unsigned gaw_graphics_hash(const unsigned char *bytes,unsigned count,unsigned value)
{
 unsigned n;for(n=0;n<count;n++) value=(value^bytes[n])*16777619U;return value;
}
''')
    anchor='e=gaw_fore_phases+gaw_fore_phase_count++;';assert source.count(anchor)==1
    source=source.replace(anchor,'''
 {
 unsigned *h=gaw_graphics_hashes[gaw_fore_phase_count];
 h[0]=gaw_graphics_hash(vram,6176,2166136261U);
 h[1]=gaw_graphics_hash(work_ram+0x900,912,2166136261U);
 h[1]=gaw_graphics_hash(work_ram+0xd00,56,h[1]);
 h[2]=gaw_graphics_hash(work_ram+0x80,16,2166136261U);
 h[3]=gaw_graphics_hash(work_ram+0x1100,512,2166136261U);
 h[4]=gaw_graphics_hash(sram.sram+((work_ram[0x1ffc]&4)<<12)+0x1000,512,2166136261U);
 }
'''+anchor)
    modified=source.encode();target=folder/'z80-graphics-data.txt'
    if target.exists():assert target.read_bytes()==modified
    else:target.write_bytes(modified)
    try:
        path.write_bytes(modified)
        result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_graphicsdata_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
        (ROOT/'validation/graphics-data-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr[-2000:]
    finally:path.write_bytes(original)
    assert path.read_bytes()==original
    print('Read-only graphics data observer built; original core source restored.')

if __name__=='__main__':main()
