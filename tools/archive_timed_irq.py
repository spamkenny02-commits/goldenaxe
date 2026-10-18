"""Freeze timed IRQ/fast-reader proofs; optionally remove verified generated copies."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from actor_reference import ROOT

REPORTS=[
 'fast_reader_timing_68k_report.json','fast_timed_reader_failures_report.json',
 'timed_irq_boundaries_report.json','native_irq_context_boundaries_report.json','native_source_wait_report.json',
 *['native_planned_loading_budget_bare_precise_physical_video_'+s+'_report.json' for s in
   ['timed_audio','fast_timed_audio','audio_readiness_fast_timed_audio']]]
FOLDERS=[
 'fast-reader-timing','fast-timed-reader-failures','timed-irq-boundaries',
 'timed-irq-stage-read-baseline',
 *['native-planned-loading-budget-bare-precise-physical-video-'+s for s in
   ['timed-audio','fast-timed-audio','audio-readiness-fast-timed-audio']]]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/timed-irq-v0203';assert not out.exists(),'Immutable archive already exists'
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes())
    assert digest=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    for name in ['main.c','sound.inc']:
        assert (ROOT/'megadrive/src'/name).read_bytes()==subprocess.check_output(['git','show','e6a9db3:megadrive/src/'+name],cwd=ROOT)
    reports={n:json.loads((ROOT/'analysis'/n).read_text()) for n in REPORTS}
    for n,r in reports.items():
        for field in ['sources','helpers','helper_sha256']:
            for module,h in r.get(field,{}).items():
                p=ROOT/'megadrive/src'/(module if Path(module).suffix else module+'.c')
                assert sha(p.read_bytes())==h,(n,module)
    compiled=reports['fast_reader_timing_68k_report.json'];assert compiled['fast']
    assert sum(x['cases'] for x in compiled['results'])==51288
    assert sum(x['writes'] for x in compiled['results'])==178400
    assert all(x['done'] and not x['failures'] for x in compiled['results'])
    failed=reports['fast_timed_reader_failures_report.json'];assert (failed['accepted'],failed['rejected'],failed['rejections_after_published_writes'])==(2911,89,27)
    assert reports['timed_irq_boundaries_report.json']['adapter_calls']==156
    for n,r in reports.items():
        if 'loading_budget' not in n:continue
        assert not r['audio_deadline_pacing'] and r['absolute_source_psg_dates'] and r['physical_video']
        assert sum(len(reg['rows']) for reg in r['results'])==24
        assert all(row['source_psg_dates_verified'] for reg in r['results'] for row in reg['rows'])
        assert sum(row['psg_writes'] for reg in r['results'] for row in reg['rows'])==1488
        folder='native-planned-loading-budget-bare-precise-physical-video-'+('audio-readiness-' if r.get('audio_readiness') else '')+('fast-timed-audio' if r['clock_audio_fast_timed'] else 'timed-audio')
        assert sha((ROOT/'validation'/folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        for name,h in r['generated_source_sha256'].items():assert sha((ROOT/'validation'/folder/'src'/name).read_bytes())==h
    # Verify retained original reader vectors against its already-frozen archive.
    old=ROOT/'analysis/reader-timing-v0203';manifest=json.loads((old/'manifest.json').read_text());refs={}
    for name in ['validation/reader-timing/events.json','validation/native-audio-reader/cases.json','validation/native-audio-reader/extension-cases.json']:
        raw=(ROOT/name).read_bytes();h=sha(raw)
        if name in manifest['files']:assert h==manifest['files'][name] and (old/name).read_bytes()==raw
        else:
            item=manifest['compressed'][name];assert h==item['raw_sha256'] and gzip.decompress((old/item['stored']).read_bytes())==raw
        refs[name]=dict(manifest='analysis/reader-timing-v0203/manifest.json',raw_sha256=h)
    paths={ROOT/'README.md',ROOT/'analysis/timed_irq_milestone.md'}
    paths.update(ROOT/'analysis'/n for n in REPORTS)
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.inc'])
    for name in ['validate_reader_timing_68k.py','validate_timed_reader_failures.py','validate_timed_irq_boundaries.py','validate_native_irq_context_boundaries.py','validate_native_source_wait.py','profile_native_loading_budget.py','archive_timed_irq.py']:
        paths.add(ROOT/'tools'/name)
    for folder in FOLDERS:paths.update(p for p in (ROOT/'validation'/folder).rglob('*') if p.is_file())
    paths.update(ROOT/'validation'/n for n in ['timed-irq-build.log','fast-reader-timing-68k-run.log','timed-irq-profile-run.log','fast-timed-stage-read-run.log','timed-irq-readiness-profile-run.log','timed-irq-legacy-wait-run.log'])
    paths.add(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll')
    files={};compressed={};candidates=[]
    for p in sorted(paths):
        raw=p.read_bytes();h=sha(raw)
        name=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else 'observer/'+p.name
        if p.is_relative_to(ROOT/'validation') or len(raw)>65536:
            blob='objects/'+h+'.gz';dest=out/blob;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            assert gzip.decompress(dest.read_bytes())==raw
            compressed[name]=dict(stored=blob,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(dest.read_bytes()))
            # Only regenerable new diagnostics, never source input or numbered ROMs.
            if p.is_relative_to(ROOT/'validation') and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name=='expected.h'):
                candidates.append(p)
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);assert dest.read_bytes()==raw;files[name]=h
    cleanup=[]
    if '--cleanup' in sys.argv:
        validation=(ROOT/'validation').resolve()
        for p in candidates:
            target=p.resolve();assert target.is_relative_to(validation) and target!=validation
            relative=target.relative_to(ROOT).as_posix()
            assert not subprocess.check_output(['git','ls-files','--',relative],cwd=ROOT)
            item=compressed[relative];raw=target.read_bytes();assert sha(raw)==item['raw_sha256']
            assert gzip.decompress((out/item['stored']).read_bytes())==raw
            cleanup.append(dict(path=relative,bytes=len(raw)));target.unlink()
    data=dict(playable_sha256=digest,production_timed_irq=False,files=files,compressed=compressed,immutable_vector_references=refs,removed_verified_generated=cleanup)
    (out/'manifest.json').write_text(json.dumps(data,indent=2)+'\n')
    print(len(files),'snapshots;',len(compressed),'compressed references;',len({x['stored'] for x in compressed.values()}),'stored blobs;',sum(x['bytes'] for x in cleanup),'generated bytes removed')


if __name__=='__main__':main()
