"""Freeze rejected SAT terminator prototypes without promoting a release."""
import gzip,json,sys
from pathlib import Path
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
 report=ROOT/'analysis/playable_sprite_end_v0214_report.json';r=json.loads(report.read_bytes());assert not r['release_accepted'] and len(r['cases'])==4 and all(c['frames']==10 for c in r['cases'])
 assert [c['natural_raster_differences'] for c in r['cases'][:2]]==[[],[]]
 assert all(c['natural_raster_differences']==[dict(frame=3120,box=[169,36,174,37])] for c in r['cases'][2:])
 roots=[ROOT/('validation/playable-sprite-end-v'+str(n).zfill(4)) for n in range(211,215)];roots=[p for p in roots if p.exists()];paths=set(p for d in roots for p in d.rglob('*') if p.is_file())
 for name in ['README.md','versions/index.json','versions/README.md','analysis/playable_sprite_end_wip.md','analysis/playable_sprite_end_v0214_report.json','megadrive/src/main.c','tools/validate_playable_sprite_end.py','tools/validate_playable_sprite_limit.py','tools/run_core.py','tools/archive_playable_sprite_end_wip.py','tools/archive_lossless_evidence.py','validation/v0210-symbols.txt']:
  paths.add(ROOT/name)
 for n in range(211,215):
  for folder in (ROOT/'versions').glob('v'+str(n).zfill(4)+'-*'):paths.update(p for p in folder.iterdir() if p.is_file())
  paths.update(ROOT.glob('validation/v'+str(n).zfill(4)+'-*.log'))
 stable='4678a4f4eddb4f1a76e9f174ba1381c76687f011de541f11bbfac8af3d65a554'
 for n in ['gaw-megadrive.bin','gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/n).read_bytes())==stable
 assert sha((ROOT/'validation/playable-sprite-end-v0214/candidate.bin').read_bytes())==r['md_sha256']
 assert len(list((ROOT/'versions').glob('*/*.bin')))==214
 out=ROOT/'analysis/playable-sprite-end-rejected-v0214';m=freeze(ROOT,out,paths,dict(recommended_playable_sha256=stable,candidate_sha256=r['md_sha256'],release_accepted=False,reason='PAL3120 natural raster regression despite correct final VRAM',numbered_roms_preserved=214),roots,'--cleanup' in sys.argv)
 for item in m['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 # Recover a rejected image's correct final sprite plane, not a release gate.
 from validate_playable_sprite_limit import reference
 for tag in ['old','new']:
  name='validation/playable-sprite-end-v0214/pal-leading-'+tag+'/vram_03120.bin';item=m['compressed'][name];raw=gzip.decompress((out/item['stored']).read_bytes());plane,_=reference(raw,0xf400,8)
  if tag=='old':before=plane
  else:assert plane==before
 print('Rejected prototype archive readback passed; recommended ROM remainsv0210.')
if __name__=='__main__':main()
