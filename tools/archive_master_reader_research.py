"""Preserve successful semantic and rejected CPU experiments; clean verified copies."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from actor_reference import ROOT

REPORTS=['master_reader_timing_68k_report.json','fast_reader_timing_68k_report.json','reader_timing_68k_report.json',
 'master_timed_reader_failures_report.json','fast_timed_reader_failures_report.json','timed_reader_failures_report.json',
 'timed_irq_boundaries_report.json',*['native_planned_loading_budget_bare_precise_physical_video_'+s+'_report.json' for s in ['fast_timed_audio','master_timed_audio']]]
TRIALS=['master-reader-inline-baseline','master-reader-noinline-baseline','master-single-scale-clock-baseline',
 'packed-clock-long-baseline','packed-clock-word-copy-baseline','packed-clock-word-aligned-baseline','clock-forced-inline-baseline']
FOLDERS=['master-reader-timing','fast-reader-timing','master-timed-reader-failures','fast-timed-reader-failures','timed-reader-failures','timed-irq-boundaries',
 *['native-planned-loading-budget-bare-precise-physical-video-'+s for s in ['master-timed-audio','fast-timed-audio']],*TRIALS,
 *['reader-timing/kernel-'+str(n) for n in range(8)]]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def archived(folder,name):
    m=json.loads((folder/'manifest.json').read_text())
    if name in m['files']:
        raw=(folder/name).read_bytes();assert sha(raw)==m['files'][name]
    else:
        item=m['compressed'][name];stored=(folder/item['stored']).read_bytes();assert sha(stored)==item['stored_sha256']
        raw=gzip.decompress(stored);assert sha(raw)==item['raw_sha256']
    return raw


def main():
    out=ROOT/'analysis/master-reader-research-v0203';assert not out.exists(),'Immutable archive already exists'
    reports={n:json.loads((ROOT/'analysis'/n).read_text()) for n in REPORTS}
    for n,r in reports.items():
        for field in ['sources','helpers']:
            for module,h in r.get(field,{}).items():
                p=ROOT/'megadrive/src'/(module if Path(module).suffix else module+'.c');assert sha(p.read_bytes())==h,(n,module)
    for n in REPORTS[:3]:
        r=reports[n];assert sum(x['cases'] for x in r['results'])==51288 and sum(x['writes'] for x in r['results'])==178400
        assert all(x['done'] and not x['failures'] for x in r['results'])
    assert reports['master_reader_timing_68k_report.json']['fused_master']
    assert reports['timed_irq_boundaries_report.json']['adapter_calls']==208
    for n in REPORTS[3:6]:
        r=reports[n];assert (r['accepted'],r['rejected'],r['rejections_after_published_writes'])==(2911,89,27)
    previous=ROOT/'analysis/timed-irq-v0203';name='analysis/native_planned_loading_budget_bare_precise_physical_video_fast_timed_audio_report.json'
    baseline=json.loads(archived(previous,name));current=reports[Path(name).name]
    for old,new in zip(baseline['results'],current['results']):
        assert [r['measured_master'] for r in old['rows']]==[r['measured_master'] for r in new['rows']]
    assert (ROOT/'megadrive/src/source_clock.h').read_bytes()==subprocess.check_output(['git','show','982954c:megadrive/src/source_clock.h'],cwd=ROOT)
    for n in REPORTS[-2:]:
        r=reports[n];assert not r['audio_deadline_pacing'] and r['absolute_source_psg_dates']
        assert sum(row['psg_writes'] for reg in r['results'] for row in reg['rows'])==1488
        assert all(row['source_psg_dates_verified'] for reg in r['results'] for row in reg['rows'])
        variant='master-timed-audio' if r['clock_audio_fused_master'] else 'fast-timed-audio'
        folder=ROOT/'validation'/('native-planned-loading-budget-bare-precise-physical-video-'+variant)
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        for source,h in r['generated_source_sha256'].items():assert sha((folder/'src'/source).read_bytes())==h
    refs={}
    old=ROOT/'analysis/reader-timing-v0203'
    for name in ['validation/reader-timing/events.json','validation/native-audio-reader/cases.json','validation/native-audio-reader/extension-cases.json']:
        raw=(ROOT/name).read_bytes();assert archived(old,name)==raw;refs[name]=dict(manifest='analysis/reader-timing-v0203/manifest.json',raw_sha256=sha(raw))
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    paths={ROOT/'README.md',ROOT/'analysis/master_reader_research.md'}
    paths.update(ROOT/'analysis'/n for n in REPORTS)
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.inc'])
    paths.update(ROOT/'tools'/n for n in ['archive_master_reader_research.py','profile_native_loading_budget.py','validate_reader_timing_68k.py','validate_timed_reader_failures.py','validate_timed_irq_boundaries.py'])
    for folder in FOLDERS:paths.update(p for p in (ROOT/'validation'/folder).rglob('*') if p.is_file())
    for pattern in ['master-*.log','*clock*profile*.log','*relative-profile*.log','fused-default*68k-run.log','clock-gate-disassembly.*','master-timed-disassembly.txt']:
        paths.update((ROOT/'validation').glob(pattern))
    files={};compressed={};candidates=[]
    for p in sorted(paths):
        raw=p.read_bytes();h=sha(raw);name=p.relative_to(ROOT).as_posix()
        if p.is_relative_to(ROOT/'validation') or len(raw)>65536:
            blob='objects/'+h+'.gz';dest=out/blob;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            assert gzip.decompress(dest.read_bytes())==raw
            compressed[name]=dict(stored=blob,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(dest.read_bytes()))
            if p.is_relative_to(ROOT/'validation') and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name=='expected.h'):candidates.append(p)
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);assert dest.read_bytes()==raw;files[name]=h
    data=dict(playable_sha256=digest,production_master_reader=False,files=files,compressed=compressed,
        immutable_vector_references=refs,previous_milestone_manifest_sha256=sha((previous/'manifest.json').read_bytes()),removed_verified_generated=[])
    # Persist the complete restore map before deleting any generated copy.
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
