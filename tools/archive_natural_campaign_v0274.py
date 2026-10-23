"""Freeze campaign captures and verify full recovery before generated cleanup."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 roots=[p for parent in ['natural-dungeon-route','natural-dungeon-combat'] for p in (ROOT/'validation'/parent).glob('*v0274*') if p.is_dir()]
 assert roots and all(p.resolve().is_relative_to(ROOT/'validation') for p in roots)
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))];before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected}
 paths=[p for folder in roots for p in folder.rglob('*') if p.is_file()]
 paths += [ROOT/'tools'/n for n in ['natural_dungeon_combat.py','natural_dungeon_route.py','run_core.py','replay_natural_campaign.py','summarize_natural_campaign_v0274.py','archive_natural_campaign_v0274.py']]
 paths += [ROOT/'analysis'/n for n in ['natural_campaign_v0274.md','natural_campaign_v0274_report.json','natural_campaign_worklog_prefix.json']]
 out=ROOT/'analysis/natural-campaign-v0274';m=freeze(ROOT,out,paths,dict(release=274,purpose='Natural first dungeon, second dungeon key and failed later controller trials',protected_sha256=before,cleanup_roots=[p.relative_to(ROOT).as_posix() for p in roots]),roots,cleanup=True)
 for item in m['compressed'].values():
  raw=(out/item['stored']).read_bytes();assert sha(raw)==item['stored_sha256'];assert sha(gzip.decompress(raw))==item['raw_sha256']
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 report=ROOT/'analysis/natural_campaign_v0274_report.json';saved=report.read_bytes()
 import summarize_natural_campaign_v0274
 summarize_natural_campaign_v0274.main();assert report.read_bytes()==saved
 removed=sum(i['bytes'] for i in m['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file());print(json.dumps(dict(removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored,protected_numbered_roms=len(protected)-3,full_archive_readback=True,summary_identical_after_cleanup=True),indent=2))
if __name__=='__main__':main()
