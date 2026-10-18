"""Freeze native FIFO producer connection, source vectors and cost proofs."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from actor_reference import ROOT

REPORTS=['psg_stream_report.json','psg_queue_report.json','queued_loading_report.json','queued_irq_faults_report.json',
 'native_planned_loading_budget_bare_precise_physical_video_queued_audio_report.json']
FOLDERS=['psg-stream','psg-queue','queued-loading','queued-irq-faults','native-planned-loading-budget-bare-precise-physical-video-queued-audio']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/queued-audio-v0203';assert not out.exists(),'Immutable archive exists'
    reports={n:json.loads((ROOT/'analysis'/n).read_text()) for n in REPORTS}
    for n,r in reports.items():
        for module,h in r.get('helpers',{}).items():
            p=ROOT/'megadrive/src'/(module if Path(module).suffix else module+'.c');assert sha(p.read_bytes())==h,(n,module)
    stream=reports['psg_stream_report.json'];assert stream['host']['checks']==980029 and stream['host']['produced']==90000 and not stream['host']['failures']
    for reg in stream['results']:assert reg['done'] and not reg['failures'] and reg['irq_sent']==reg['irq_consumed']==12000 and not reg['irq_failures']
    for n,h in stream['sources'].items():assert sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes())==h
    for n,h in reports['psg_queue_report.json']['sources'].items():
        p=ROOT/('megadrive/src/'+n if n.startswith('source_psg_queue') else 'validation/psg-queue/src/'+n);assert sha(p.read_bytes())==h
    loading=reports['queued_loading_report.json'];assert len(loading['host_cases'])==96
    for reg in loading['results']:assert reg['done'] and reg['cases']==96 and not reg['failures'] and reg['bytes']==5952
    faults=reports['queued_irq_faults_report.json'];assert len(faults['cases'])==11
    for reg in faults['results']:assert reg['done'] and reg['cases']==11 and not reg['failures']
    budget=reports[REPORTS[-1]];assert budget['queued_audio'] and budget['queue_output_deferred_to_end'] and not budget['audio_deadline_pacing'] and budget['queue_capacity']==512
    assert sum(row['queue_published'] for reg in budget['results'] for row in reg['rows'])==1488
    assert all(row['source_psg_dates_verified'] and row['remaining_source_master']>0 and not row['queue_waits'] for reg in budget['results'] for row in reg['rows'])
    folder=ROOT/'validation'/FOLDERS[-1];assert sha((folder/'out/release/rom.bin').read_bytes())==budget['kernel_sha256']
    for name,h in budget['generated_source_sha256'].items():assert sha((folder/'src'/name).read_bytes())==h
    refs={}
    for name in ['analysis/loading_psg_deadlines_report.json','validation/loading-psg-deadlines/inputs.json']:
        path=ROOT/name if name.startswith('analysis/') else ROOT/'analysis/loading-psg-v0203'/name
        raw=path.read_bytes();refs[name]=sha(raw)
        old=json.loads((ROOT/'analysis/loading-psg-v0203/manifest.json').read_text())
        if name in old['files']:assert old['files'][name]==sha(raw)
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    paths={ROOT/'README.md',ROOT/'analysis/queued_audio_milestone.md',ROOT/'validation/native-planned-room-finish/cases.json'}
    paths.update(ROOT/'analysis'/n for n in REPORTS)
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.inc'])
    paths.update(ROOT/'tools'/n for n in ['validate_psg_stream.py','validate_queued_loading.py','validate_queued_irq_faults.py','validate_psg_queue.py','profile_native_loading_budget.py','archive_queued_audio.py'])
    for folder in FOLDERS:paths.update(p for p in (ROOT/'validation'/folder).rglob('*') if p.is_file())
    for n in ['queued-audio-budget-run.log','queued-audio-game-build.log','queued-stream-legacy-queue-run.log']:paths.add(ROOT/'validation'/n)
    files={};compressed={};candidates=[]
    for p in sorted(paths):
        raw=p.read_bytes();h=sha(raw);name=p.relative_to(ROOT).as_posix()
        if p.is_relative_to(ROOT/'validation') or len(raw)>65536:
            blob='objects/'+h+'.gz';dest=out/blob;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            assert gzip.decompress(dest.read_bytes())==raw
            compressed[name]=dict(stored=blob,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(dest.read_bytes()))
            if p.is_relative_to(ROOT/'validation') and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name in ['expected.h','psg.h']):candidates.append(p)
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);assert dest.read_bytes()==raw;files[name]=h
    data=dict(playable_sha256=digest,production_queue_wired=False,files=files,compressed=compressed,source_oracle_references=refs,
        baseline_manifest_sha256=sha((ROOT/'analysis/native-copy-pointers-v0203/manifest.json').read_bytes()),removed_verified_generated=[])
    manifest=out/'manifest.json';manifest.write_text(json.dumps(data,indent=2)+'\n')
    if '--cleanup' in sys.argv:
        for p in candidates:
            target=p.resolve();assert target.is_relative_to((ROOT/'validation').resolve())
            name=target.relative_to(ROOT).as_posix();assert not subprocess.check_output(['git','ls-files','--',name],cwd=ROOT)
            item=compressed[name];raw=target.read_bytes();assert sha(raw)==item['raw_sha256'] and gzip.decompress((out/item['stored']).read_bytes())==raw
            data['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));target.unlink()
        manifest.write_text(json.dumps(data,indent=2)+'\n')
    print(len(files),'snapshots;',len(compressed),'compressed references;',len({v['stored'] for v in compressed.values()}),'blobs;',sum(v['bytes'] for v in data['removed_verified_generated']),'generated bytes removed')


if __name__=='__main__':main()
