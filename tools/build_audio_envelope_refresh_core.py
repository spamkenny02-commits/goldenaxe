"""Extend read-only prefix M1/R core with returned A/DE andunwind observations."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-envelope-refresh-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-prefix-refresh-v0183/z80-audio-prefix-refresh.txt').read_text();anchor='static unsigned gaw_prefix_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'''
static unsigned gaw_envelope_a,gaw_envelope_active,gaw_envelope_unwind,gaw_envelope_de;
__declspec(dllexport) unsigned gaw_envelope_return_a(void) { return gaw_envelope_a; }
__declspec(dllexport) unsigned gaw_envelope_return_de(void) { return gaw_envelope_de; }
__declspec(dllexport) unsigned gaw_envelope_did_unwind(void) { return gaw_envelope_unwind; }
''')
 source=source.replace('if(pc==0x3000) {','if(pc==0x3000) { gaw_envelope_active=1;')
 source=source.replace('if(pc==0x3003) {','if((pc==0x3003 || pc==0x3053) && gaw_envelope_active) { gaw_envelope_active=0;gaw_envelope_unwind=(pc==0x3053);gaw_envelope_de=DED;')
 anchor='gaw_prefix_count++;';assert source.count(anchor)==1;modified=source.replace(anchor,'gaw_envelope_a=A;'+anchor).encode();target=folder/'z80-envelope-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_enveloperefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/audio-envelope-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Envelope M1/R/unwind observer built;original source restored.')
if __name__=='__main__':main()
