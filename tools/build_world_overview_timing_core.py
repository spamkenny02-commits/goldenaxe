"""Read-only original overview room and pixel routine timing."""
import re,subprocess,sys
from run_core import ROOT
def main():
    folder=ROOT/'analysis/world-overview-timing-source';folder.mkdir(exist_ok=True)
    path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';before=path.read_bytes();source=before.decode().replace('\r\n','\n')
    pcs=[0x31e7,0x31f7,0x3202,0x3217,0x3220,0x3223,0x322c,0x322f,0x323b,0x3250,0x3265,0x326a,0x3286,0x190b,0x192a,0x192d,0x1938,0x0b95,0x0bb3]
    start=source.index('static void gaw_timing_observe(unsigned pc)');a=source.index('  if(',start);b=source.index('\n  {',a)
    declarations='static unsigned char gaw_screen_scenes[256][8192];\nstatic unsigned gaw_screen_scene_count;\n__declspec(dllexport) const unsigned char *gaw_screen_scene_data(void) {return &gaw_screen_scenes[0][0];}\n__declspec(dllexport) unsigned gaw_screen_scene_size(void) {return gaw_screen_scene_count;}\n'
    source=source[:start]+declarations+source[start:];a+=len(declarations);b+=len(declarations)
    changed=(source[:a]+'  if('+' || '.join('pc==0x%04x'%x for x in pcs)+')'+source[b:]).encode()
    changed=changed.replace(b'static void gaw_timing_observe(unsigned pc)\n{',b'static void gaw_timing_observe(unsigned pc)\n{\n  if(pc==0x3223 && gaw_screen_scene_count<256) memcpy(gaw_screen_scenes[gaw_screen_scene_count++],work_ram,8192);')
    (folder/'z80-original.txt').write_bytes(before);(folder/'z80-world-overview-markers.txt').write_bytes(changed)
    try:
        path.write_bytes(changed)
        result=subprocess.run([sys.executable,'tools/build_timing_core.py','--target','genesis_plus_gx_overview_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
        (ROOT/'validation/world-overview-timing-core-build.log').write_bytes((result.stdout+result.stderr).encode());assert result.returncode==0,result.stderr
    finally:path.write_bytes(before)
    assert path.read_bytes()==before
    print('Separate read-only world-overview timing core built; working source restored.')
if __name__=='__main__':main()
