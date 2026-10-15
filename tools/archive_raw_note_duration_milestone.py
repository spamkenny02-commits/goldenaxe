"""Immutable v0181 reader source and original/compiled-native audio evidence."""
import hashlib,json
from actor_reference import ROOT

def main():
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['sha256']==digest)
 assert entry['version']==181 and entry['validation']=='targeted_checks_passed'
 folder=(ROOT/'versions'/entry['rom']).parent;items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in sorted((ROOT/'megadrive/src').iterdir()):
  if p.is_file():preserve(p,'source/'+p.name)
 preserve(ROOT/'megadrive/out/release/symbol.txt','symbol.txt')
 for name in ['validate_raw_note_duration.py','raw_note_duration_harness.c','build_raw_note_duration_harness.ps1','archive_raw_note_baseline.py','audit_raw_note_duration_patch.py','archive_raw_note_duration_milestone.py','validate_audio_prefix_cost.py','validate_music.py','validate_sfx.py','validate_music_fade_dispatch.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for p in sorted((ROOT/'validation/raw-note-duration').glob('*.bin')):preserve(p,str(p.relative_to(ROOT)))
 preserve(ROOT/'validation/raw-note-duration/cases.inc','validation/raw-note-duration/cases.inc')
 preserve(ROOT/'validation/raw-note-duration/raw-note/source.sms','validation/raw-note-duration/source-fixture.sms')
 preserve(ROOT.parents[1]/'work/raw-note-duration-harness/out/release/rom.bin','evidence/native-harness.bin')
 for p in sorted((ROOT/'validation').glob('music-fade-*/*.bin')):preserve(p,str(p.relative_to(ROOT)))
 for p in sorted((ROOT/'validation').glob('*v0181.log')):preserve(p,'logs/'+p.name)
 preserve(ROOT/'analysis/raw_note_duration_milestone.md','raw_note_duration_milestone.md')
 preserve(ROOT/'analysis/raw-note-duration-v0180/analysis/raw_note_duration_baseline_report.json','reference/v0180-baseline.json')
 for report in entry['reports']:preserve(folder/report['file'],report['file'])
 baseline=ROOT/'analysis/raw-note-duration-v0180/manifest.json'
 data=(json.dumps(dict(version=181,md_sha256=digest,baseline_manifest_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'source_evidence_manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('v0181 source and selected audio evidence archived and verified:',len(items),'files')

if __name__=='__main__':main()
