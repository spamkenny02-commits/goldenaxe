"""Preserve original8679 model and v0183 borrowed-noise rest correction."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-noise-note-v0183';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():preserve(p,'source-v0183/'+p.name)
 preserve(ROOT/'analysis/audio-ownership-v0182/source-v0182/sound.inc','source-v0182/sound.inc')
 for name in ['audio_noise_note_cost.py','validate_audio_noise_note.py','validate_audio_prefix_cost.py','audio_noise_note_harness.c','build_audio_noise_note_harness.ps1','audit_noise_note_patch.py','archive_noise_note_milestone.py']:preserve(ROOT/'tools'/name,'tools/'+name)
 preserve(ROOT/'analysis/audio-prefix-v0180/z80-prefix-snapshots.txt','z80-prefix-snapshots.txt')
 for name in ['noise_note_baseline_report.json','noise_note_report.json','noise_note_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for root in ['audio-noise-note','music-fade-dispatch']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json','.inc']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['noise-note-baseline.log','noise-note-fixed.log','build-noise-note-baseline.log','build-noise-note-fixed.log','build-v0183.log','music-v0183.log','sfx-v0183.log','music-fade-v0183.log','noise_note_patch_report.json','music_report.json','sfx_report.json','music_fade_dispatch_report.json']:preserve(ROOT/'validation'/name,'validation/'+name)
 for name in ['genesis_plus_gx_prefix_libretro.dll','genesis_plus_gx_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 for p in sorted((ROOT.parents[1]/'work/audio-noise-note-harness/src').iterdir()):
  if p.is_file():preserve(p,'native-harness/src/'+p.name)
 for name in ['rom.bin','symbol.txt']:preserve(ROOT.parents[1]/'work/audio-noise-note-harness/out/release'/name,'native-harness/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 assert digest.startswith('ec1677f7')
 baseline=json.loads((ROOT/'analysis/noise_note_baseline_report.json').read_text());fixed=json.loads((ROOT/'analysis/noise_note_report.json').read_text())
 assert baseline['md_sha256']=='f41db51b8cb8356125c6b48f967a26bc775e63330cb87fb8f942b4e063fd848d'
 assert baseline['cases']==fixed['cases']==18432 and sum(r['mismatches'] for r in baseline['rows'])==144
 assert fixed['all_cases_exact'] and fixed['md_sha256']==digest
 data=(json.dumps(dict(md_sha256=digest,source_sha256=fixed['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Noise helper and correction evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
