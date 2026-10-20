"""Freeze passing and rejected prepared-DMA experiments before cleanup."""
from pathlib import Path
import gzip
import json
import sys
from archive_lossless_evidence import freeze,sha

ROOT=Path(__file__).resolve().parents[1]
PASS=['video-byte-stamp-bare','video-byte-stamp-proof']
REJECT=['video-prepared-job-bare','video-prepared-held-bare']

def main():
    previous_raw=(ROOT/'analysis/md-z80-video-service-v0203/manifest.json').read_bytes();previous=json.loads(previous_raw)
    paths=set();roots=[];reports={}
    def report(name):
        path=ROOT/'analysis'/name;raw=path.read_bytes();paths.add(path);reports[path.relative_to(ROOT).as_posix()]=sha(raw);return json.loads(raw)
    for variant in PASS:
        folder=ROOT/('validation/md-z80-psg-'+variant);roots.append(folder)
        r=report('md_z80_psg_'+variant.replace('-','_')+'_report.json')
        assert r['video_job_prepared'] and r['video_pattern_cached'] and r['live_loader'] and r['bulk_fifo_drain']
        assert r['bare']==variant.endswith('bare') and r['polled_transfer_attempts']==128
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        assert sha((folder/'driver.bin').read_bytes())==r['driver_sha256']
        assert sha((folder/'driver-source.asm.snapshot').read_bytes())==r['driver_source_sha256']
        for table in ['sources','headers']:
            for name,digest in r[table].items():
                path=ROOT/'megadrive/src'/name;assert sha(path.read_bytes())==digest;paths.add(path)
        for row in r['results']:
            assert row['done'] and not row['failures'] and not row['failure_code'] and row['plain_core_identical']
            assert row['cases']==48 and row['bytes']==2976 and row['video_updates']==2785
            assert row['video_requests']==row['video_pattern_preparations']==row['video_job_preparations']==2784
            assert row['errors_master'][0]>=0 and sum(x['spacing_checks'] for x in row['rows'])==96
            assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
            for case in row['rows']:
                assert case['sample_gap_master'][1]<17100 and case['clock_line_advance'][1]<=5
                assert case['video_bus_holds_master'][1]<17100 and case['transport_bus_holds_master'][1]<6840
        original=json.loads((folder/'report-before-limit-clarification.json.snapshot').read_bytes())
        assert original['results']==r['results'] and original['kernel_sha256']==r['kernel_sha256']
    for variant in REJECT:
        folder=ROOT/('validation/md-z80-psg-'+variant);roots.append(folder)
        rejected=json.loads((folder/'rejected-run.json').read_bytes());assert rejected['status'].startswith('rejected')
        rows=[]
        for path in sorted(folder.glob('*-events.json')):
            raw=path.read_bytes();data=json.loads(raw);rows.append(dict(region=path.stem.split('-')[0],observed=data['observed'],events_sha256=sha(raw)))
        assert rows and any(not r['observed']['done'] and r['observed']['frame']==20000 for r in rows)
        assert (folder/'md_z80_video_dma.c.snapshot').exists()
        audit=folder/'rejected-capture-audit.json'
        payload=(json.dumps(dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),source_snapshot_sha256=sha((folder/'md_z80_video_dma.c.snapshot').read_bytes()),results=rows),indent=2)+'\n').encode()
        if audit.exists():assert audit.read_bytes()==payload
        else:audit.write_bytes(payload)
    windows=report('md_z80_prepared_dma_windows_report.json');assert len(windows['results'])==4
    assert all(r['committed']==2784 and r['hold_max']==3886 for r in windows['results'])
    for r in windows['results']:assert r['report_sha256']==reports['analysis/md_z80_psg_'+r['variant'].replace('-','_')+'_report.json']
    prior=report('md_z80_prepared_prior_windows_report.json')
    old=json.loads((ROOT/'analysis/md_z80_video_service_trials_windows_report.json').read_bytes())
    for r in prior['results']:assert r==next(x for x in old['results'] if x['variant']==r['variant'] and x['region']==r['region'])
    native=report('md_video_prepared_contract_report.json')
    assert all(r['done'] and r['checks']==26 and not r['failures'] for r in native['results'])
    for name,digest in native['sources'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==digest
    roots.append(ROOT/'validation/md-video-prepared-contract')
    intermediate=report('md_z80_dma_intermediate_video_byte_stamp_bare_report.json')
    folder=ROOT/'validation/md-z80-dma-intermediate-video-byte-stamp-bare';roots.append(folder)
    for r in intermediate['results']:
        assert r['updates']>1 and not r['updates']&1
        assert sha((folder/(r['region']+'-prefix-events.json')).read_bytes())==r['prefix_sha256']
        assert sha((folder/(r['region']+'-vram.bin')).read_bytes())==r['vram_sha256']
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','analysis/world_next.md','analysis/md_z80_prepared_video_milestone.md',
                 'megadrive/src/md_z80_video_dma.h','tools/md_z80_video_fixture.py','tools/validate_md_z80_psg.py',
                 'tools/analyze_md_z80_dma_windows.py','tools/validate_md_video_prepared_contract.py',
                 'tools/validate_md_z80_dma_intermediate.py','tools/archive_lossless_evidence.py','tools/archive_md_z80_prepared_video.py',
                 'validation/md-z80-prepared-world-prefix.json','validation/md-z80-prepared-dma-windows-run.log',
                 'validation/md-z80-prepared-prior-windows-run.log','validation/md-video-prepared-contract-run.log',
                 'validation/md-z80-video-byte-stamp-intermediate-run.log']:
        paths.add(ROOT/name)
    for variant in PASS+REJECT:paths.add(ROOT/('validation/z80-psg-'+variant+'-run.log'))
    prefix=json.loads((ROOT/'validation/md-z80-prepared-world-prefix.json').read_bytes())
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==previous['playable_sha256']
    metadata=dict(previous_manifest_sha256=sha(previous_raw),playable_sha256=previous['playable_sha256'],reports=reports,
        rejected_variants=REJECT,source_checkpoint_proof='video-byte-stamp-proof',production_integration=False,
        video_frame_deadlines_accepted=False,audio_waveform_validated=False)
    out=ROOT/'analysis/md-z80-prepared-video-v0203'
    manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
    # Independent final readback includes the manifest produced by cleanup.
    assert json.loads((out/'manifest.json').read_bytes())==manifest
    for name,digest in manifest['files'].items():assert sha((out/name).read_bytes())==digest
    for item in manifest['compressed'].values():
        encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
    print('Final independent archive readback passed.')

if __name__=='__main__':main()
