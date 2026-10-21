"""Preserve playable v0210 evidence before removing generated captures."""
import gzip,json,sys
from pathlib import Path
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
 report=ROOT/'analysis/playable_sprite_limit_v0210_report.json';r=json.loads(report.read_bytes());inventory=ROOT/'validation/inventory_restore_report.json';i=json.loads(inventory.read_bytes());assert r['md_sha256']==i['md_sha256']==sha((ROOT/'gaw-megadrive.bin').read_bytes())
 assert len(r['cases'])==2 and all(c['overflow_frames']==12 and c['corrected_sprite_pixels']==7495 for c in r['cases']);assert len(i['cases'])==6 and all(not c['early_native_static_pattern_changes_from_before_menu'] for c in i['cases'])
 roots=[ROOT/('validation/playable-sprite-limit-v'+n) for n in ['0208','0209','0210']]
 roots.extend(ROOT/('validation/inventory-restore-'+place+'-'+region+'-'+kind) for place in ['exterior','first_house','second_house'] for region in ['auto','pal'] for kind in ['md','sms'])
 roots=[p for p in roots if p.exists()];paths=set(p for folder in roots for p in folder.rglob('*') if p.is_file())
 for name in ['README.md','build.ps1','tools/update_readme.py','tools/version_rom.py','tools/validate_playable_sprite_limit.py','tools/validate_inventory_restore.py','tools/validate_actor_tick.py','tools/run_core.py','tools/archive_playable_sprite_limit.py','tools/archive_lossless_evidence.py','analysis/world_next.md','analysis/playable_sprite_limit_v0210.md','analysis/playable_sprite_limit_v0210_report.json','validation/inventory_restore_report.json','validation/playable-sprite-limit-world-prefix.json','megadrive/src/main.c','megadrive/src/actors.c','megadrive/out/release/symbol.txt','megadrive/out/release/rom.bin','gaw-megadrive.bin','versions/index.json','versions/README.md']:
  paths.add(ROOT/name)
 paths.update(ROOT.glob('validation/v02*-*test.log'));paths.update(ROOT.glob('validation/v02*-build.log'))
 for folder in (ROOT/'versions').glob('v02[01][089]-*'):paths.update(p for p in folder.iterdir() if p.is_file())
 paths.update(p for folder in (ROOT/'versions').glob('v0210-*') for p in folder.iterdir() if p.is_file())
 prefix=json.loads((ROOT/'validation/playable-sprite-limit-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 roms=list((ROOT/'versions').glob('*/*.bin'));assert len(roms)==210
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 out=ROOT/'analysis/playable-sprite-limit-v0210';m=freeze(ROOT,out,paths,dict(playable_sha256=r['md_sha256'],previous_playable_sha256=r['baseline_sha256'],numbered_roms_preserved=210,playable_world_sms_row_limit_integrated=True,full_game_validated=False,ordering_phase_validated=False),roots,'--cleanup' in sys.argv)
 for item in m['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 # Recheck physical row-limit evidence from the archive, after deletion.
 from validate_playable_sprite_limit import ordered_reference,reference
 for region in ['auto','pal']:
  for f in range(3129,3141):
   def recover(kind):
    name='validation/playable-sprite-limit-v0210/'+region+'-'+kind+'-'+str(f)+'-vram.bin';item=m['compressed'][name];return gzip.decompress((out/item['stored']).read_bytes())
   a,b=recover('old'),recover('new');expected,_=reference(ordered_reference(a,b,0xf400),0xf400,8);actual,_=reference(b,0xf400,16);assert expected==actual
 print('Independent release archive readback and24 physical planes recovered.')
if __name__=='__main__':main()
