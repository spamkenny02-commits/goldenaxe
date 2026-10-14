"""Build read-only orchestration/reveal markers; restore working Z80 source."""
import re,subprocess,sys
from actor_reference import ROOT

EXTRA=[0x24e4,0x24e7,0x24ea,0x1c15,0x1c25,0x1c40,0x1c88,0x1caf,0x1cf8,
       0x2c63,0x2c8a,0x2ca6,0x2d3e,0x2d7b,0x2d7c,0x2d8a,0x369f,0x386e,0x3885,
       0x5b20,0x1fb6,0x1fbc,0x2002,0x04e1,0x04e4,0x04f7,0x04fd]

def main():
 folder=ROOT/'analysis/transition-timing-v0176';folder.mkdir(exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c'
 original=path.read_bytes()
 source=(ROOT/'analysis/loading-model-v0175/z80-loader-markers.txt').read_text()
 pattern=r'  if\(pc==0x16d0.*\)'
 old=re.search(pattern,source).group();markers=sorted(set(int(p,16) for p in re.findall(r'pc==0x([0-9a-f]+)',old))|set(EXTRA))
 replacement='  if('+' || '.join(f'pc==0x{p:04x}' for p in markers)+')'
 modified=re.sub(pattern,lambda _:replacement,source,count=1).encode()
 for name,data in [('z80-before-transition-markers.txt',original),('z80-transition-markers.txt',modified)]:
  target=folder/name
  if target.exists():assert target.read_bytes()==data
  else:
   with target.open('xb') as handle:handle.write(data)
 try:
  path.write_bytes(modified)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_transition_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/transition-core-build.log').write_text(result.stdout+result.stderr)
  assert result.returncode==0,(result.returncode,result.stderr)
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('Read-only transition timing core built;',len(markers),'markers; working Z80 source restored.')

if __name__=='__main__':main()
