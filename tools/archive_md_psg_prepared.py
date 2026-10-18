"""Freeze prepared bursts/beam wait proof and metadata-only research baseline."""
import gzip
import hashlib
import json
import subprocess
import sys
from actor_reference import ROOT

REPORTS=['md_psg_replay_beam_report.json','md_psg_beam_sweep_report.json','md_psg_plan_report.json','md_psg_replay_compat_report.json']
FOLDERS=['md-psg-replay-beam','md-psg-beam-sweep','md-psg-plan','md-psg-replay-compat','md-psg-replay-planned']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/md-psg-prepared-v0203';assert not out.exists(),'Immutable archive exists'
    reports={n:json.loads((ROOT/'analysis'/n).read_text()) for n in REPORTS}
    for report in reports.values():
        for name,h in report.get('helpers',{}).items():assert sha((ROOT/'megadrive/src'/(name+'.c')).read_bytes())==h
        for key in ['sources','replay_sources']:
            for name,h in report.get(key,{}).items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==h
    beam=reports[REPORTS[0]];assert beam['planned'] and beam['beam']
    for r in beam['results']:
        assert r['done'] and not r['failures'] and r['cases']==48 and r['extra_cases']==33 and r['bytes']==2976 and r['plain_core_identical']
        assert all(0<=e<3420 for row in r['rows'] for e in row['errors_master'])
        assert r['poll_gap_master'][1]<10260 and r['seed_gap_master'][1]<10260
    sweep=reports[REPORTS[1]]
    for r in sweep['results']:
        assert r['done'] and not r['failures'] and r['cases']==10260 and r['bytes']==85500 and r['plain_core_identical']
        raw=(ROOT/'validation/md-psg-beam-sweep'/(r['region']+'-rows.json')).read_bytes();assert sha(raw)==r['rows_sha256']
        rows=json.loads(raw);assert {(row['kind'],row['phase']) for row in rows}=={(k,p) for k in range(3) for p in range(3420)}
        assert all(0<=e<3420 for row in rows for e in row['errors_master'])
    plan=reports[REPORTS[2]];assert plan['host']['cases']==21024 and plan['host']['beam_cases']==12650 and not plan['host']['failures']
    for r in plan['results']:assert r['done'] and r['cases']==2024 and r['beam_cases']==12650 and not r['failures']
    compat=reports[REPORTS[3]];assert compat['compat'] and not compat['planned']
    for r in compat['results']:assert r['done'] and not r['failures'] and r['cases']==48 and r['bytes']==2976 and r['plain_core_identical']
    for report_name,folder_name in zip(REPORTS,FOLDERS):
        r=reports[report_name];folder=ROOT/'validation'/folder_name
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        for reg in r['results']:
            if 'events_sha256' in reg:assert sha((folder/(reg['region']+'-events.json')).read_bytes())==reg['events_sha256']
    intermediate_name='md_psg_replay_planned_report.json';intermediate=json.loads((ROOT/'analysis'/intermediate_name).read_text());folder=ROOT/'validation/md-psg-replay-planned'
    assert sha((folder/'out/release/rom.bin').read_bytes())==intermediate['kernel_sha256']
    for name,h in intermediate['helpers'].items():
        path=folder/'retained-source_md_psg_plan.c.snapshot' if name=='source_md_psg_plan' else ROOT/'megadrive/src'/(name+'.c')
        assert sha(path.read_bytes())==h
    for name,h in intermediate['replay_sources'].items():
        path=folder/'src/source_md_psg_replay.s' if name.endswith('.s') else folder/('retained-'+name+'.snapshot')
        assert sha(path.read_bytes())==h
    baseline=ROOT/'analysis/md-psg-replay-v0203/manifest.json';observer=ROOT/'analysis/md-io-clock-v0203/manifest.json'
    io=json.loads(observer.read_text());assert io['compressed']['emulator/genesis_plus_gx_io_libretro.dll']['raw_sha256']==beam['observer_core_sha256']
    playable=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert playable=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    paths={ROOT/'README.md',ROOT/'analysis/md_psg_prepared_milestone.md'}
    paths.update(ROOT/'analysis'/n for n in REPORTS+[intermediate_name])
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.inc','.s'])
    paths.update(ROOT/'tools'/name for name in ['validate_md_psg_replay.py','validate_md_psg_beam_sweep.py','validate_md_psg_plan.py','archive_md_psg_prepared.py','validate_queued_loading.py','validate_native_room_finish.py','validate_reader_timing.py'])
    for name in FOLDERS:paths.update(p for p in (ROOT/'validation'/name).rglob('*') if p.is_file())
    paths.update(ROOT/'validation'/n for n in ['beam-playable-build.log','beam-replay-run.log','beam-sweep-run.log','planned-replay-run.log','replay-compat-run.log'])
    files={};compressed={};candidates=[]
    for p in sorted(paths):
        raw=p.read_bytes();h=sha(raw);name=p.relative_to(ROOT).as_posix()
        if p.is_relative_to(ROOT/'validation') or len(raw)>65536:
            blob='objects/'+h+'.gz';dest=out/blob;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            assert gzip.decompress(dest.read_bytes())==raw
            compressed[name]=dict(stored=blob,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(dest.read_bytes()))
            in_folder=any(p.is_relative_to(ROOT/'validation'/n) for n in FOLDERS)
            if in_folder and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name.endswith(('-clock.json','-events.json','-rows.json')) or p.name in ['expected.h','psg.h','beam_ref.h']):candidates.append(p)
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);files[name]=h
    data=dict(playable_sha256=playable,producer_consumer_overlap=False,production_irq_scheduler=False,baseline_manifest_sha256=sha(baseline.read_bytes()),observer_manifest_sha256=sha(observer.read_bytes()),
        intermediate_report=intermediate_name,intermediate_sources_retained=True,files=files,compressed=compressed,removed_verified_generated=[])
    manifest=out/'manifest.json';manifest.write_text(json.dumps(data,indent=2)+'\n')
    if '--cleanup' in sys.argv:
        for p in candidates:
            target=p.resolve();assert any(target.is_relative_to((ROOT/'validation'/n).resolve()) for n in FOLDERS)
            name=target.relative_to(ROOT).as_posix();assert not subprocess.check_output(['git','ls-files','--',name],cwd=ROOT)
            item=compressed[name];raw=target.read_bytes();assert sha(raw)==item['raw_sha256'] and gzip.decompress((out/item['stored']).read_bytes())==raw
            data['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));target.unlink()
        manifest.write_text(json.dumps(data,indent=2)+'\n')
    print(len(files),'snapshots;',len(compressed),'compressed references;',sum(v['bytes'] for v in data['removed_verified_generated']),'generated bytes removed')


if __name__=='__main__':main()
