"""Keep rejected cooperative schedulers byte-exact before removing opt-in hooks."""
import gzip
import hashlib
import json
import subprocess
import sys
from actor_reference import ROOT

FOLDERS=['md-loading-audio-cooperative-per-instruction','md-loading-audio-cooperative-coarse-checkpoints','md-loading-audio-cooperative-single-cache','md-loading-audio-cooperative-profile','md-loading-audio-cooperative-bare','md-loading-audio-cooperative-direct','md-psg-plan']
REPORTS=['md_loading_audio_cooperative_bare_report.json','md_loading_audio_cooperative_direct_report.json','md_loading_audio_cooperative_profile_report.json','md_psg_plan_report.json']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/md-cooperative-research-v0203';assert not out.exists()
    paths=set();reports={n:json.loads((ROOT/'analysis'/n).read_text()) for n in REPORTS}
    candidates={p.name:[p] for p in (ROOT/'megadrive/src').iterdir() if p.is_file()}
    for folder_name in FOLDERS:
        folder=ROOT/'validation'/folder_name
        for p in folder.rglob('*'):
            if not p.is_file():continue
            paths.add(p)
            if p.parent.name=='retained-sources':candidates.setdefault(p.name,[]).append(p)
        if (folder/'retained-report.json').exists():reports[folder_name]=json.loads((folder/'retained-report.json').read_text())
    for name,r in reports.items():
        for key in ['sources','assembly_sources']:
            for n,h in r.get(key,{}).items():
                filename=n if '.' in n else n+'.c'
                assert any(sha(p.read_bytes())==h for p in candidates.get(filename,[])),(name,n)
    for report_name,folder_name in zip(REPORTS,FOLDERS[4:6]+[FOLDERS[3],FOLDERS[6]]):
        r=reports[report_name];folder=ROOT/'validation'/folder_name
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        for row in r['results']:
            assert row['done'] and not row['failures']
            if 'events_sha256' in row:
                assert row['plain_core_identical'] and row['cases']==48 and row['bytes']==2976 and row['errors_master'][1]>3420
                assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
    for r in reports[REPORTS[3]]['results']:assert r['beam_cases']==16950 and r['cases']==2024
    paths.update(ROOT/'analysis'/n for n in REPORTS)
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.s','.inc'])
    paths.update(ROOT/'tools'/n for n in ['archive_md_cooperative_research.py','validate_md_loading_audio.py','validate_md_psg_plan.py','validate_queued_loading.py','validate_native_room_finish.py','validate_reader_timing.py'])
    paths.update(p for p in (ROOT/'validation').iterdir() if p.is_file() and (p.name.startswith('md-loading-audio-cooperative') or p.name=='cooperative-plan-run.log'))
    files={};compressed={};remove=[]
    for p in sorted(paths):
        raw=p.read_bytes();h=sha(raw);name=p.relative_to(ROOT).as_posix()
        if p.is_relative_to(ROOT/'validation') or len(raw)>65536:
            stored='objects/'+h+'.gz';dest=out/stored;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            encoded=dest.read_bytes();assert gzip.decompress(encoded)==raw
            compressed[name]=dict(stored=stored,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(encoded))
            if any(p.is_relative_to(ROOT/'validation'/n) for n in FOLDERS) and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name.endswith('-events.json') or p.name=='expected.h'):remove.append(p)
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);files[name]=h
    manifest=dict(cooperative_scheduler_accepted=False,production_integration=False,files=files,compressed=compressed,removed_verified_generated=[])
    target=out/'manifest.json';target.write_text(json.dumps(manifest,indent=2)+'\n')
    for name,h in files.items():assert sha((out/name).read_bytes())==h
    for v in compressed.values():
        encoded=(out/v['stored']).read_bytes();assert sha(encoded)==v['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==v['raw_sha256'] and len(raw)==v['raw_bytes']
    if '--cleanup' in sys.argv:
        for p in remove:
            resolved=p.resolve();assert any(resolved.is_relative_to((ROOT/'validation'/n).resolve()) for n in FOLDERS)
            name=resolved.relative_to(ROOT).as_posix();assert not subprocess.check_output(['git','ls-files','--',name],cwd=ROOT)
            v=compressed[name];raw=resolved.read_bytes();assert sha(raw)==v['raw_sha256'] and gzip.decompress((out/v['stored']).read_bytes())==raw
            manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));resolved.unlink()
        target.write_text(json.dumps(manifest,indent=2)+'\n')
    print(len(files),'source snapshots;',len(compressed),'compressed references;',sum(x['bytes'] for x in manifest['removed_verified_generated']),'generated bytes removed')


if __name__=='__main__':main()
