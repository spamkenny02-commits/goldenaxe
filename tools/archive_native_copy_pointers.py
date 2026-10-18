"""Freeze pointer-copy/source equivalence and exact read-only CPU profiles."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from actor_reference import ROOT

REPORTS=['md_loading_instruction_cost_report.json','md_loading_instruction_cost_current_report.json',
 'native_planned_room_finish_report.json','native_planned_room_finish_68k_report.json','pattern_plan_phases_68k_report.json','pattern_window_divu_report.json',
 *['native_planned_loading_budget_bare_precise_physical_video_'+s+'_report.json' for s in ['fast_timed_audio','audio_readiness_fast_timed_audio']]]
FOLDERS=['md-instruction-cost','md-instruction-cost-current','plan-copy-only-baseline','pattern-plan-phases-68k','pattern-window-divu','native-planned-room-finish/kernel',
 *['native-planned-loading-budget-bare-precise-physical-video-'+s for s in ['fast-timed-audio','audio-readiness-fast-timed-audio']]]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/native-copy-pointers-v0203';assert not out.exists(),'Immutable archive exists'
    reports={n:json.loads((ROOT/'analysis'/n).read_text()) for n in REPORTS}
    for n,r in reports.items():
        for name,h in r.get('helpers',{}).items():
            p=ROOT/'megadrive/src'/(name if Path(name).suffix else name+'.c');assert sha(p.read_bytes())==h,(n,name)
    for reg in reports['native_planned_room_finish_68k_report.json']['results']:assert reg['done'] and reg['cases']==24 and not reg['failures']
    for reg in reports['pattern_plan_phases_68k_report.json']['results']:assert reg['done'] and reg['cases']==16 and not reg['failures']
    assert reports['pattern_plan_phases_68k_report.json']['module_sha256']==sha((ROOT/'megadrive/src/source_pattern_clock.c').read_bytes())
    for reg in reports['pattern_window_divu_report.json']['results']:assert reg['done'] and reg['cases']==1070469 and not reg['failures']
    assert reports['pattern_window_divu_report.json']['helper_sha256']==sha((ROOT/'megadrive/src/source_pattern_clock.c').read_bytes())
    budget=reports[REPORTS[-2]];profile=reports['md_loading_instruction_cost_current_report.json']
    assert profile['current'] and profile['kernel_sha256']==budget['kernel_sha256']
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_cost_libretro.dll'
    for name in REPORTS[:2]:
        assert reports[name]['observer_core_sha256']==sha(core.read_bytes())
        for reg in reports[name]['results']:
            assert reg['observed']['done'] and reg['observed']['cases']==12 and not reg['observed']['failures']
            assert all(sum(b['master'] for b in row['bins'])==row['whole_master'] for row in reg['rows'])
    for b,p in zip(budget['results'],profile['results']):
        assert [r['measured_master'] for r in b['rows']]==[r['whole_master'] for r in p['rows']]
        assert all(row['remaining_source_master']>0 for row in b['rows'])
    for n in REPORTS[-2:]:
        r=reports[n];assert r['absolute_source_psg_dates'] and not r['audio_deadline_pacing']
        assert sum(row['psg_writes'] for reg in r['results'] for row in reg['rows'])==1488
        assert all(row['source_psg_dates_verified'] for reg in r['results'] for row in reg['rows'])
        if r.get('audio_readiness'):assert all(row['late_source_psg_bytes']==0 for reg in r['results'] for row in reg['rows'])
        folder=ROOT/'validation'/('native-planned-loading-budget-bare-precise-physical-video-'+('audio-readiness-' if r.get('audio_readiness') else '')+'fast-timed-audio')
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        for source,h in r['generated_source_sha256'].items():assert sha((folder/'src'/source).read_bytes())==h
    original=ROOT.parents[1]/'work/genesis-plus-gx/core/m68k/m68kcpu.c'
    assert sha(original.read_bytes())==(ROOT/'validation/md-instruction-cost/m68kcpu-original.sha256').read_text().strip()
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    paths={ROOT/'README.md',ROOT/'analysis/native_copy_pointers_milestone.md',ROOT/'validation/native-planned-room-finish/cases.json',core,original}
    paths.update(ROOT/'analysis'/n for n in REPORTS)
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.inc'])
    paths.update(ROOT/'tools'/n for n in ['build_md_cost_core.py','build_timing_core.py','profile_md_instruction_cost.py','profile_native_loading_budget.py','validate_native_room_finish.py','validate_native_room_finish_68k.py','validate_pattern_windows_68k.py','validate_pattern_window_divu.py','archive_native_copy_pointers.py'])
    for folder in FOLDERS:paths.update(p for p in (ROOT/'validation'/folder).rglob('*') if p.is_file())
    for pattern in ['copy-pointers-*.log','plan-copy-*.log']:paths.update((ROOT/'validation').glob(pattern))
    files={};compressed={};candidates=[]
    for p in sorted(paths):
        raw=p.read_bytes();h=sha(raw);name=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else 'observer/'+p.name
        if p.is_relative_to(ROOT/'validation') or len(raw)>65536 or not p.is_relative_to(ROOT):
            blob='objects/'+h+'.gz';dest=out/blob;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            assert gzip.decompress(dest.read_bytes())==raw
            compressed[name]=dict(stored=blob,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(dest.read_bytes()))
            if p.is_relative_to(ROOT/'validation') and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name in ['expected.h','disassembly.txt']):candidates.append(p)
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);assert dest.read_bytes()==raw;files[name]=h
    data=dict(playable_sha256=digest,production_clock_wired=False,files=files,compressed=compressed,
        baseline_manifest_sha256=sha((ROOT/'analysis/native-divu-loading-v0203/manifest.json').read_bytes()),removed_verified_generated=[])
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
