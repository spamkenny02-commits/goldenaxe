"""Archive refresh-domain fixtures losslessly before generated-file cleanup."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 folder=ROOT/'validation/refresh-domain';out=ROOT/'analysis/refresh-domain-v0275';report=json.loads((ROOT/'analysis/refresh_domain_v0275_report.json').read_bytes());assert report['passed'] and report['actors_sha256']==sha((ROOT/'megadrive/src/actors.c').read_bytes())
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))];before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert before['gaw-megadrive.bin']==report['md_sha256']
 for case in report['cases']:
  capture=json.loads((folder/f"game-{case['region']}-{case['input']['name']}"/'capture.json').read_bytes());assert capture['rom_sha256']==report['md_sha256'] and capture['frames']==case['frame']
 paths=[p for p in folder.rglob('*') if p.is_file()]+[ROOT/'megadrive/src/actors.c']
 paths += [ROOT/'tools'/n for n in ['validate_refresh_domain.py','validate_refresh_domain_game.py','archive_refresh_domain_v0275.py']]
 paths += [ROOT/'analysis'/n for n in ['refresh_domain_rules_report.json','refresh_domain_v0275_report.json','refresh_domain_v0275.md','refresh_domain_worklog_prefix.json']]
 m=freeze(ROOT,out,paths,dict(release=275,protected_sha256=before,verified_playable_cases=len(report['cases']),purpose='Direct-R domain correction, controlled source/native fixtures'),[folder],cleanup=True)
 # The explicitly generated SMS test cartridge is also recoverable. Original
 # SMS input and numbered playable MD ROMs are outside this checked directory.
 fixture=(folder/'chooser.sms').resolve();assert fixture.is_relative_to((ROOT/'validation/refresh-domain').resolve());name=fixture.relative_to(ROOT).as_posix();i=m['compressed'][name];raw=fixture.read_bytes();assert sha(raw)==i['raw_sha256'] and gzip.decompress((out/i['stored']).read_bytes())==raw;fixture.unlink();m['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 for i in m['compressed'].values():
  raw=(out/i['stored']).read_bytes();assert sha(raw)==i['stored_sha256'];assert sha(gzip.decompress(raw))==i['raw_sha256']
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(x['bytes'] for x in m['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file());print(json.dumps(dict(full_readback=True,protected_numbered_roms=len(protected)-3,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored),indent=2))
if __name__=='__main__':main()
