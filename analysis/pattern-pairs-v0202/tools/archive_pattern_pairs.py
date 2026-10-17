"""Freeze the paced v0202 converter,source audit and targeted regression evidence."""
import hashlib,json,subprocess
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/pattern-pairs-v0202';paths=set();audit=json.loads((ROOT/'validation/pattern_pairs_patch_audit.json').read_text());refs=[]
 paths.update(audit['source_files'])
 paths.update(['analysis/pattern_pairs_assets_report.json','analysis/pattern_pairs_milestone.md','validation/pattern_pairs_patch_audit.json','tools/archive_pattern_pairs.py','tools/validate_menu_transitions.py','tools/profile_menu_transitions.py','tools/validate_inventory_restore.py','tools/validate_start_menu_sfx.py','tools/validate_intro.py','tools/profile_standard_door_music.py','tools/validate_standard_door_transitions.py','analysis/standard_door_music_report.json','validation/menu_transition_profile.json','megadrive/out/release/symbol.txt'])
 paths.update(r['file'] for r in audit['reports'])
 for name in ['src/main.c','src/wrapper.c','out/release/rom.bin','out/release/symbol.txt','build.log']:paths.add('validation/pattern-pairs/'+name)
 for name in ['validation/build-pattern-pairs.log','validation/build-pattern-pairs-pal.log','validation/build-pattern-pairs-paced.log','validation/build-pattern-pairs-title.log']:paths.add(name)
 release=next(r for r in json.loads((ROOT/'versions/index.json').read_text()) if r['version']==202)
 assert release['sha256']==audit['md_sha256']
 refs.append(dict(file='versions/'+release['rom'],sha256=release['sha256']))
 manifest=[]
 def preserve(name,raw):
  target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==raw,('Immutable archive differs',name)
  else:target.write_bytes(raw)
  manifest.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 for name in sorted(paths):preserve(name,(ROOT/name).read_bytes())
 for name in ['megadrive/src/main.c','megadrive/src/intro.inc']:
  raw=subprocess.run(['git','show',audit['baseline_commit']+':'+name],cwd=ROOT,capture_output=True,check=True).stdout;preserve('baseline/'+name,raw)
 raw=(json.dumps(dict(md_sha256=audit['md_sha256'],baseline_commit=audit['baseline_commit'],files=manifest,external_immutable_references=refs),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==raw
 else:target.write_bytes(raw)
 print('Archived',len(manifest),'source/proof files; test kernel binary retained locally,playable ROM in numbered versions.')
if __name__=='__main__':main()
