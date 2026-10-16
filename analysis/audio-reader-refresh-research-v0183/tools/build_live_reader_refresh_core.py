"""Read-only live8000 M1/R spans alongside the retained824-byte state records."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-reader-refresh-live-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-reader-complete-live-v0183/z80-live-reader.txt').read_text();anchor='#define R Z80.r';assert source.count(anchor)==1
 source=source.replace(anchor,'static unsigned long long gaw_M1_fetches;\n'+anchor);assert source.count('R++;')==5;source=source.replace('R++;','R++;gaw_M1_fetches++;')
 anchor='R += (cycles / cyclesum) * opcodes;';assert source.count(anchor)==1;source=source.replace(anchor,anchor+'gaw_M1_fetches += (cycles / cyclesum) * opcodes;')
 anchor='static unsigned gaw_live_envelope_count,gaw_live_envelope_active;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'''
static unsigned gaw_live_M1[8192][3];
static unsigned long long gaw_live_M1_start;
__declspec(dllexport) const unsigned char *gaw_live_envelope_m1_events(void) { return (const unsigned char *)gaw_live_M1; }
''')
 anchor='gaw_live_envelope_start=gaw_elapsed;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'gaw_live_M1_start=gaw_M1_fetches;gaw_live_M1[gaw_live_envelope_count][1]=(R&127)|R2;')
 anchor='gaw_live_envelope_count++;';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_live_M1[gaw_live_envelope_count][0]=gaw_M1_fetches-gaw_live_M1_start;gaw_live_M1[gaw_live_envelope_count][2]=(R&127)|R2;'+anchor)
 modified=source.encode();target=folder/'z80-live-reader-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_livereaderrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-live-reader-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Live reader M1/R observer built;original source restored.')
if __name__=='__main__':main()
