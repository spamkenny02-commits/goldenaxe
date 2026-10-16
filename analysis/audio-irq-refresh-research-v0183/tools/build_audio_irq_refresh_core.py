"""Read-only vector/audioIRQ M1/R observations alongside full-reader captures."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-irq-refresh-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-reader-refresh-live-v0183/z80-live-reader-refresh.txt').read_text();anchor='static unsigned gaw_audio_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'''
static unsigned long long gaw_audio_M1[32768][5],gaw_vector_M1,gaw_vector_R,gaw_vector_clock;
__declspec(dllexport) const unsigned char *gaw_audio_irq_m1_events(void) { return (const unsigned char *)gaw_audio_M1; }
''')
 anchor='e=gaw_audio_events[gaw_audio_count++];';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_audio_M1[gaw_audio_count][0]=gaw_M1_fetches;gaw_audio_M1[gaw_audio_count][1]=(R&127)|R2;gaw_audio_M1[gaw_audio_count][2]=gaw_vector_M1;gaw_audio_M1[gaw_audio_count][3]=gaw_vector_R;gaw_audio_M1[gaw_audio_count][4]=gaw_vector_clock;'+anchor)
 anchor='static void gaw_timing_observe(unsigned pc)\n{';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\n if(pc==0x38) { gaw_vector_M1=gaw_M1_fetches;gaw_vector_R=(R&127)|R2;gaw_vector_clock=gaw_elapsed; }')
 modified=source.encode();target=folder/'z80-audio-irq-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_audioirqrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-irq-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('AudioIRQ/vector M1/R observer built;original source restored.')
if __name__=='__main__':main()
