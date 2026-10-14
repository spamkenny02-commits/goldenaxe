"""Preserve original ADSR/table/live envelope models and read-only evidence."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-envelopes-v0180';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'versions/v0180-3f155979/source'/p.name).read_bytes(),('production changed',p.name)
 for name,source in [('z80-adsr-unit.txt','audio-adsr-v0180/z80-envelope-unit.txt'),('z80-table-unit.txt','audio-table-envelope-v0180/z80-envelope-unit.txt'),('z80-live-envelopes.txt','audio-envelope-live-v0180/z80-live-envelopes.txt')]:preserve(ROOT/'analysis'/source,name)
 for name in ['audio_adsr_cost.py','audio_table_envelope_cost.py','audio_dispatch_cost.py','validate_audio_adsr_cost.py','validate_audio_table_envelope_cost.py','validate_live_envelope_cost.py','build_audio_envelope_core.py','build_live_envelope_core.py','validate_audio_prefix_cost.py','profile_paid_passage_loader_phases.py','archive_audio_envelope_research.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for root in ['audio-envelope','audio-envelope-live']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-adsr-cost.log','audio-table-envelope-cost.log','audio-envelope-live.log','audio-envelope-core-build.log','audio-table-envelope-core-build.log','audio-envelope-live-core-build.log','build-audio-envelope-core.log','build-audio-table-envelope-core.log','build-audio-envelope-live-core.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['audio_adsr_cost_report.json','audio_table_envelope_cost_report.json','live_envelope_cost_report.json','audio_envelope_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for name in ['genesis_plus_gx_envelope_libretro.dll','genesis_plus_gx_tableenvelope_libretro.dll','genesis_plus_gx_liveenvelope_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 reports=[json.loads((ROOT/'analysis'/name).read_text()) for name in ['audio_adsr_cost_report.json','audio_table_envelope_cost_report.json','live_envelope_cost_report.json']]
 assert [r['cases'] for r in reports]==[80384,26800,4245]
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert all(r['md_sha256']==digest for r in reports)
 data=(json.dumps(dict(md_sha256=digest,source_sha256=reports[0]['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Original envelope evidence archived and verified:',len(items),'files')

if __name__=='__main__':main()
