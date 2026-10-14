"""Preserve v0178 source,symbols,actual music profiles and aligned PSG tables."""
import hashlib,json
from actor_reference import ROOT

def main():
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['sha256']==digest)
 assert entry['version']==178 and entry['validation']=='targeted_checks_passed'
 folder=(ROOT/'versions'/entry['rom']).parent;items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable snapshot differs',name)
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for path in sorted((ROOT/'megadrive/src').iterdir()):
  if path.is_file():preserve(path,'source/'+path.name)
 for name in ['main.c','actors.c','paid_passage.inc','sound.inc']:preserve(ROOT/'megadrive/src'/name,name)
 preserve(ROOT/'megadrive/out/release/symbol.txt','symbol.txt')
 for name in ['validate_paid_exit_music.py','validate_music_fade_dispatch.py','profile_paid_passage_loader_phases.py',
              'validate_paid_passage_native_loading_clock.py','paid_passage_clock_harness.c','build_paid_passage_clock_harness.ps1',
              'validate_paid_passage_gameplay.py','audit_paid_exit_music_patch.py','archive_paid_exit_music_milestone.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for path in sorted((ROOT/'validation/paid-exit-music').glob('*/*.json')):preserve(path,str(path.relative_to(ROOT)))
 for path in sorted((ROOT/'validation').glob('music-fade-*/*.bin')):preserve(path,str(path.relative_to(ROOT)))
 for name in ['build-v0178.log','build-paid-clock-v0178.log','paid-exit-music-v0178.log',
              'music-fade-dispatch-v0178.log','paid-clock-v0178.log','paid-gameplay-v0178.log']:
  preserve(ROOT/'validation'/name,'logs/'+name)
 preserve(ROOT/'analysis/paid_exit_music_milestone.md','paid_exit_music_milestone.md')
 preserve(ROOT/'analysis/paid_exit_music_baseline_report.json','reference/v0177-music-baseline.json')
 for report in entry['reports']:preserve(folder/report['file'],report['file'])
 research=ROOT/'analysis/hero-init-v0177/manifest.json'
 data=(json.dumps(dict(version=178,md_sha256=digest,hero_research_manifest_sha256=hashlib.sha256(research.read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode()
 target=folder/'source_evidence_manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('v0178 source and evidence preserved:',len(items),'files')

if __name__=='__main__':main()
