"""Read-only SMS PC/cycle observations for the two screen-spell loops."""
import re,subprocess,sys
from run_core import ROOT
def main():
    folder=ROOT/'analysis/screen-spell-timing-source';folder.mkdir(exist_ok=True)
    path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';before=path.read_bytes();source=before.decode().replace('\r\n','\n')
    pcs=[0x0938,0x6afb,0x6b0c,0x6b33,0x6b94,0x6b9b,0x6b9e,0x6ba1,0x6ba7,0x6c2e,0x6c3f,0x6c65,0x6cd2,0x6cd5,0x6ce2,0x6ce5,0x22c3,0x22c6,0x22e1,0xb95,0xbb3,0x6bf0,0x6bf3,0x1deb]
    start=source.index('static void gaw_timing_observe(unsigned pc)');a=source.index('  if(',start);b=source.index('\n  {',a)
    declarations='static unsigned char gaw_screen_scenes[256][8192];\nstatic unsigned gaw_screen_scene_count;\n__declspec(dllexport) const unsigned char *gaw_screen_scene_data(void) {return &gaw_screen_scenes[0][0];}\n__declspec(dllexport) unsigned gaw_screen_scene_size(void) {return gaw_screen_scene_count;}\n'
    source=source[:start]+declarations+source[start:];a+=len(declarations);b+=len(declarations)
    changed=(source[:a]+'  if('+' || '.join('pc==0x%04x'%x for x in pcs)+')'+source[b:]).encode()
    changed=changed.replace(b'static void gaw_timing_observe(unsigned pc)\n{',b'static void gaw_timing_observe(unsigned pc)\n{\n  if(pc==0x0938 && work_ram[0x90] && gaw_screen_scene_count<256) memcpy(gaw_screen_scenes[gaw_screen_scene_count++],work_ram,8192);')
    (folder/'z80-original.txt').write_bytes(before);(folder/'z80-screen-spell-markers.txt').write_bytes(changed)
    try:
        path.write_bytes(changed)
        result=subprocess.run([sys.executable,'tools/build_timing_core.py','--target','genesis_plus_gx_screen_spell_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
        (ROOT/'validation/screen-spell-timing-core-build.log').write_bytes((result.stdout+result.stderr).encode());assert result.returncode==0,result.stderr
    finally:path.write_bytes(before)
    assert path.read_bytes()==before
    print('Separate read-only screen-spell timing core built; working source restored.')
if __name__=='__main__':main()
