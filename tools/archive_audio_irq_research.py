"""Preserve original IRQ traces,models and read-only instrumentation."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-irq-v0180';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for name in ['z80-before-audio.txt','z80-audio-irq.txt']:preserve(folder/name,name)
 for name in ['build_audio_irq_timing_core.py','profile_audio_irq_matrix.py','profile_paid_passage_loader_phases.py','audio_irq_wrapper_cost.py','validate_audio_irq_cost.py','archive_audio_irq_research.py','build_timing_core.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for p in sorted((ROOT/'validation/audio-irq').glob('*/*.json')):preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-irq-matrix.log','audio-irq-cost.log','audio-irq-core-build.log','build-audio-irq-core.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 preserve(ROOT/'analysis/audio_irq_cost_report.json','audio_irq_cost_report.json')
 preserve(ROOT/'analysis/audio_irq_milestone.md','audio_irq_milestone.md')
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_audioirq_libretro.dll','genesis_plus_gx_audioirq_libretro.dll')
 report=json.loads((ROOT/'analysis/audio_irq_cost_report.json').read_text())
 assert report['cases']==24 and report['wrapper_and_state_comparisons']==4050 and report['loading_IRQ_budget_comparisons']==24
 assert all(r['loading_IRQ_unexplained_master_cycles']==0 for r in report['rows'])
 data=(json.dumps(dict(md_sha256=report['md_sha256'],source_sha256=report['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Original IRQ evidence preserved and verified:',len(items),'files')

if __name__=='__main__':main()
