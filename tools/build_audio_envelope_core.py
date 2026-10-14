"""Add returned-A observation to the original helper snapshot core."""
import subprocess,sys
from actor_reference import ROOT

def main(table=False):
 tag='audio-table-envelope' if table else 'audio-adsr'
 folder=ROOT/f'analysis/{tag}-v0180';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/audio-prefix-v0180/z80-prefix-snapshots.txt').read_text()
 anchor='static unsigned gaw_prefix_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\nstatic unsigned gaw_envelope_a;\n__declspec(dllexport) unsigned gaw_envelope_return_a(void) { return gaw_envelope_a; }')
 if table:
  source=source.replace('static unsigned gaw_envelope_a;','static unsigned gaw_envelope_a,gaw_envelope_active,gaw_envelope_unwind,gaw_envelope_de;\n__declspec(dllexport) unsigned gaw_envelope_return_de(void) { return gaw_envelope_de; }\n__declspec(dllexport) unsigned gaw_envelope_did_unwind(void) { return gaw_envelope_unwind; }')
  source=source.replace('if(pc==0x3000) {','if(pc==0x3000) { gaw_envelope_active=1;')
  source=source.replace('if(pc==0x3003) {','if((pc==0x3003 || pc==0x3053) && gaw_envelope_active) { gaw_envelope_active=0;gaw_envelope_unwind=(pc==0x3053);gaw_envelope_de=DED;')
 anchor='gaw_prefix_count++;';assert source.count(anchor)==1
 modified=source.replace(anchor,'gaw_envelope_a=A;'+anchor).encode()
 target=folder/'z80-envelope-unit.txt'
 if target.exists():assert target.read_bytes()==modified
 else:
  with target.open('xb') as f:f.write(modified)
 try:
  path.write_bytes(modified)
  target_dll='genesis_plus_gx_tableenvelope_libretro.dll' if table else 'genesis_plus_gx_envelope_libretro.dll'
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target',target_dll],cwd=ROOT,capture_output=True,text=True)
  (ROOT/('validation/audio-table-envelope-core-build.log' if table else 'validation/audio-envelope-core-build.log')).write_text(result.stdout+result.stderr)
  assert result.returncode==0,result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only envelope unit core built;working emulator source restored.')

if __name__=='__main__':main('--table' in sys.argv)
