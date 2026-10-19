"""Freeze actual loader/Z80 overlap, its early-write regression and replay checks."""
import gzip
import hashlib
import json
import subprocess
import sys
from actor_reference import ROOT

LIVE = {'live-absolute':(False,False,False), 'live-bare':(True,False,False),
        'live-packets-proof':(False,True,False), 'live-packets-bare':(True,True,False),
        'live-boundary-proof':(False,True,True), 'live-boundary-bare':(True,True,True)}
REPLAY = {'absolute-replay':0, 'absolute-edge':3419}
REJECTED = ['live-proof', 'live-checked', 'live-marked']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/md-live-z80-v0203'
    assert not out.exists(), 'Immutable archive exists'
    previous_raw=(ROOT/'analysis/md-z80-psg-margin-v0203/manifest.json').read_bytes()
    previous=json.loads(previous_raw)
    current_driver=(ROOT/'megadrive/z80/md_psg_prefetch_z80.asm').read_bytes()
    legacy=(ROOT/'megadrive/research/md_psg_sampled_z80.asm').read_bytes()
    assert sha(legacy)==previous['files']['megadrive/z80/md_psg_sampled_z80.asm']
    variants=list(LIVE)+list(REPLAY)+REJECTED
    roots=[(ROOT/('validation/md-z80-psg-'+v)).resolve() for v in variants]
    reports={}
    for variant in list(LIVE)+list(REPLAY):
        name='analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json'
        raw=(ROOT/name).read_bytes();report=json.loads(raw);reports[name]=sha(raw)
        folder=ROOT/('validation/md-z80-psg-'+variant)
        assert sha(current_driver)==report['driver_source_sha256']
        assert (folder/'driver-source.asm.snapshot').read_bytes()==current_driver
        for relative,key in [('driver.bin','driver_sha256'),('out/release/rom.bin','kernel_sha256')]:
            assert sha((folder/relative).read_bytes())==report[key]
        for table in ['sources','headers']:
            for filename,h in report[table].items():
                assert sha((ROOT/'megadrive/src'/filename).read_bytes())==h
        assert len(report['results'])==2
        if variant in LIVE:
            bare,packets,boundary=LIVE[variant]
            assert report['live_loader'] and report['bare']==bare
            assert report.get('packet_publication',False)==packets
            assert report.get('loader_boundary_before_clock_query',False)==boundary
            body=(folder/'src/wrapper.c').read_text()
            assert ('queued.timed.sink=cooperative_packet;' in body)==packets
            assert ('snapshot(clock,ctx,p->snapshots+p->points*18);' not in body)==bare
        else:
            assert not report['live_loader'] and report['physical_phase_offset']==REPLAY[variant]
        for row in report['results']:
            assert row['done'] and not row['failures'] and row['plain_core_identical']
            assert row['cases']==48 and row['bytes']==2976
            assert row['extra_cases']==(0 if variant in LIVE else 26)
            assert row['errors_master'][0]>=0
            assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
            assert len(row['rows'])==(48 if variant in LIVE else 74)
            assert sum(x['spacing_checks'] for x in row['rows'])==(96 if variant in LIVE else 596)
            for case in row['rows']:
                assert case['sample_gap_master'][1]<17100 and case['clock_line_advance'][1]<=5
                assert case['bus_holds_master'][1]<6840
            if variant in LIVE:
                assert sum(x['writes_before_loader_finish'] for x in row['rows'])>0
                assert sum(x['writes_outside_publisher'] for x in row['rows'])>0
                assert all(x['loader_finish_master']<=x['delivery_finish_master'] for x in row['rows'])
                if variant in ['live-packets-bare','live-boundary-bare']:assert row['errors_master'][1]<360000
                if report.get('loader_boundary_before_clock_query'):
                    assert all(x['loader_finish_master']<=x['loader_query_master']<=x['delivery_finish_master'] for x in row['rows'])
            else:
                assert sum(x['counter_wraps'] for x in row['rows'])==1
                assert row['prefetched_commands']==64 and row['max_prefetched_pending']==15
    regression=json.loads((ROOT/'analysis/md_z80_live_early_regression.json').read_text())
    bad=ROOT/'validation/md-z80-psg-live-marked'
    assert regression['error_master']==-690 and regression['case']==6 and regression['wrapped_epoch']
    for relative,key in [('driver-source.asm.snapshot','driver_before_sha256'),
                         ('out/release/rom.bin','kernel_before_sha256'),
                         ('ntsc-events.json','events_before_sha256')]:
        assert sha((bad/relative).read_bytes())==regression[key]
    assert sha((ROOT/'analysis/loading_psg_deadlines_report.json').read_bytes())==regression['source_dates_sha256']
    assert 'md_service_clock.h: No such file or directory' in (ROOT/'validation/z80-psg-live-proof-run.log').read_text()
    assert not (ROOT/'validation/md-z80-psg-live-proof/ntsc-events.json').exists()
    core=ROOT.parents[1]/'work/genesis-plus-gx'
    assert sha((core/'genesis_plus_gx_z80_psg_io_libretro.dll').read_bytes())==report['observer_core_sha256']
    for name in ['mem68k.c','membnk.c','vdp_ctrl.c']:
        reference=ROOT/'validation/md-z80-psg-io-core'/(name+'-original.sha256')
        assert sha((core/'core'/name).read_bytes())==reference.read_text().strip()
    prefix,size=(ROOT/'validation/z80-psg-live-world-prefix.sha256').read_text().split()
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:int(size)])==prefix
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:
        assert sha((ROOT/name).read_bytes())==previous['playable_sha256']
    paths={ROOT/name for name in reports}
    paths.update(ROOT/name for name in ['README.md','analysis/world_next.md',
        'analysis/md_z80_psg_live_milestone.md','analysis/md_z80_psg_margin_milestone.md',
        'analysis/md_z80_live_early_regression.json','megadrive/z80/md_psg_prefetch_z80.asm',
        'megadrive/research/md_psg_sampled_z80.asm','tools/archive_md_live_z80.py',
        'tools/md_live_z80_kernel.py','tools/validate_md_z80_psg.py','tools/validate_md_loading_audio.py',
        'tools/validate_queued_loading.py','tools/validate_native_room_finish.py','tools/validate_reader_timing.py'])
    for root in roots:paths.update(p for p in root.rglob('*') if p.is_file())
    paths.update(p for p in (ROOT/'validation').iterdir() if p.is_file() and
                 (p.name.startswith('z80-psg-live-') or p.name.startswith('z80-psg-absolute-')))
    files={};compressed={};candidates=[]
    for path in sorted(paths):
        raw=path.read_bytes();h=sha(raw);name=path.relative_to(ROOT).as_posix()
        if path.is_relative_to(ROOT/'validation') or len(raw)>65536:
            stored='objects/'+h+'.gz';dest=out/stored;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            encoded=dest.read_bytes();assert gzip.decompress(encoded)==raw
            compressed[name]=dict(stored=stored,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(encoded))
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);files[name]=h
        if any(path.is_relative_to(root) for root in roots) and (
                path.suffix in ['.bin','.out','.o','.s','.d','.dll'] or
                path.name.endswith(('-events.json','-clock.json')) or path.name in ['expected.h','psg.h']):
            candidates.append(path)
    manifest=dict(previous_manifest_sha256=sha(previous_raw),playable_sha256=previous['playable_sha256'],
        reports=reports,actual_loader_overlap_tested=True,early_write_regression_checked=True,
        deadline_scheduler_accepted=False,production_integration=False,audio_waveform_validated=False,
        selected_measurement='live-boundary-bare',source_checkpoint_proof='live-boundary-proof',
        files=files,compressed=compressed,removed_verified_generated=[])
    target=out/'manifest.json';target.write_text(json.dumps(manifest,indent=2)+'\n')
    for name,h in files.items():assert sha((out/name).read_bytes())==h
    for item in compressed.values():
        encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
    if '--cleanup' in sys.argv:
        for path in candidates:
            resolved=path.resolve();assert any(resolved.is_relative_to(root) for root in roots)
            name=resolved.relative_to(ROOT).as_posix()
            assert not subprocess.check_output(['git','ls-files','--',name],cwd=ROOT)
            item=compressed[name];raw=resolved.read_bytes();assert sha(raw)==item['raw_sha256']
            assert gzip.decompress((out/item['stored']).read_bytes())==raw
            manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));resolved.unlink()
        target.write_text(json.dumps(manifest,indent=2)+'\n')
    print(len(files),'source snapshots;',len(compressed),'compressed references;',
          sum(x['bytes'] for x in manifest['removed_verified_generated']),'generated bytes removed')


if __name__=='__main__':main()
