"""Preserve v0176 source,compiled symbols,tests and original source-clock evidence."""
import hashlib,json
from actor_reference import ROOT

def main():
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['sha256']==digest)
 assert entry['version']==176 and entry['validation']=='targeted_checks_passed'
 folder=(ROOT/'versions'/entry['rom']).parent;items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable snapshot differs',name)
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for path in sorted((ROOT/'megadrive/src').iterdir()):
  if path.is_file():preserve(path,'source/'+path.name)
 for name in ['main.c','actors.c','paid_passage.inc']:
  preserve(ROOT/'megadrive/src'/name,name)
 preserve(ROOT/'megadrive/out/release/symbol.txt','symbol.txt')
 for name in ['profile_paid_passage_loader_phases.py','validate_paid_passage_source_loading_clock.py',
              'validate_paid_passage_native_loading_clock.py','paid_passage_clock_harness.c',
              'build_paid_passage_clock_harness.ps1','audit_paid_passage_clock_patch.py',
              'validate_paid_passage.py','validate_paid_passage_gameplay.py',
              'reveal_loading_cost.py','validate_reveal_loading_cost.py',
              'archive_paid_passage_clock_milestone.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for name in ['paid_passage_source_loading_clock_report.json','reveal_loading_cost_report.json']:
  preserve(ROOT/'analysis'/name,'reference/'+name)
 for path in sorted((ROOT/'validation/paid-passage-clocks').glob('*/*-cycle-events.json')):
  preserve(path,'reference/'+str(path.relative_to(ROOT/'validation')).replace('\\','/'))
 for name in ['build-v0176.log','build-paid-passage-clock-harness.log',
              'paid-passage-source-loading-clock.log','paid-passage-native-loading-clock.log',
              'paid-passage-v0176.log','paid-passage-gameplay-v0176.log','reveal-loading-cost.log']:
  preserve(ROOT/'validation'/name,'logs/'+name)
 preserve(ROOT/'analysis/paid_passage_clock_milestone.md','paid_passage_clock_milestone.md')
 for report in entry['reports']:preserve(folder/report['file'],report['file'])
 data=(json.dumps(dict(md_sha256=digest,version=176,files=items),indent=2)+'\n').encode()
 target=folder/'source_evidence_manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('v0176 sources and evidence preserved:',len(items),'files')

if __name__=='__main__':main()
