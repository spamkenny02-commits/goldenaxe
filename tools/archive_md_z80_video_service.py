"""Freeze video service experiments, including results rejected on timing."""
from pathlib import Path
import json
import sys
from archive_lossless_evidence import freeze,sha

ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['video-service64-bare','video-pattern-cache-bare','video-batch-service-bare','video-pattern-cache-proof']


def main():
    previous_raw=(ROOT/'analysis/md-z80-dma-window-v0203/manifest.json').read_bytes();previous=json.loads(previous_raw)
    paths=set();reports={};roots=[]
    for variant in VARIANTS:
        folder=(ROOT/('validation/md-z80-psg-'+variant)).resolve();roots.append(folder)
        name='analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json'
        raw=(ROOT/name).read_bytes();r=json.loads(raw);reports[name]=sha(raw);paths.add(ROOT/name)
        assert r['video_fixture']=='dma' and r['live_loader'] and r['bulk_fifo_drain'] and r['polled_transfer_attempts']==128
        assert r['bare']==variant.endswith('bare') and len(r['results'])==2
        assert r.get('video_pattern_cached',False)==('pattern-cache' in variant or 'batch-service' in variant)
        assert r['video_service_stride']==(64 if variant=='video-service64-bare' else 1 if variant=='video-batch-service-bare' else 0)
        if variant=='video-batch-service-bare':assert r['video_service_kind']=='repeat-disabled'
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        assert sha((folder/'driver.bin').read_bytes())==r['driver_sha256']
        assert (folder/'driver-source.asm.snapshot').read_bytes()==(ROOT/'megadrive/z80/md_psg_prefetch_z80.asm').read_bytes()
        for table in ['sources','headers']:
            for filename,digest in r[table].items():
                path=ROOT/'megadrive/src'/filename;assert sha(path.read_bytes())==digest,(variant,filename);paths.add(path)
        for row in r['results']:
            assert row['done'] and not row['failures'] and not row['failure_code'] and row['plain_core_identical']
            assert row['cases']==48 and row['bytes']==2976 and not row['extra_cases'] and row['errors_master'][0]>=0
            assert row['video_requests']==2784 and row['video_updates']==2785
            if r.get('video_pattern_cached',False):assert row['video_pattern_preparations']==2784
            if r['video_service_stride']:assert row['video_service_calls']==(38872 if variant=='video-service64-bare' else 1344)
            assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
            assert sum(x['spacing_checks'] for x in row['rows'])==96
            for x in row['rows']:
                assert x['sample_gap_master'][1]<17100 and x['clock_line_advance'][1]<=5
                assert x['video_bus_holds_master'][1]<17100 and x['transport_bus_holds_master'][1]<6840
            capture=folder/(row['region']+'-plain');frame=row['frame']
            for name,key in [(f'vram_{frame:05d}.bin','vram_sha256'),(f'vdp_regs_{frame:05d}.bin','registers_sha256'),(f'frame_{frame:05d}.png','image_sha256')]:
                assert sha((capture/name).read_bytes())==row['video'][key]
        paths.add(ROOT/('validation/z80-psg-'+variant+'-run.log'))
    name='analysis/md_z80_video_service_trials_windows_report.json';raw=(ROOT/name).read_bytes();reports[name]=sha(raw);paths.add(ROOT/name)
    windows=json.loads(raw);assert len(windows['results'])==8
    for row in windows['results']:
        assert row['committed']==2784 and row['hold_max']<=3732
        assert row['pre_bus_beam_reads']<=row['attempts'] and row['pre_bus_beam_reads']>=row['post_bus_beam_reads']>=2784
        name='analysis/md_z80_psg_'+row['variant'].replace('-','_')+'_report.json';assert row['report_sha256']==reports[name]
    name='analysis/md_z80_dma_window_regression_report.json';raw=(ROOT/name).read_bytes();reports[name]=sha(raw);paths.add(ROOT/name)
    old=json.loads((ROOT/'analysis/md_z80_dma_windows_report.json').read_bytes());regression=json.loads(raw)
    for row in regression['results']:
        prior=next(x for x in old['results'] if x['variant']==row['variant'] and x['region']==row['region'])
        for key,value in prior.items():
            if key=='rows':
                assert len(value)==len(row['rows'])
                for a,b in zip(value,row['rows']):assert all(b[k]==v for k,v in a.items())
            else:assert row[key]==value
    name='analysis/md_z80_dma_intermediate_video_pattern_cache_bare_report.json';raw=(ROOT/name).read_bytes();reports[name]=sha(raw);paths.add(ROOT/name)
    intermediate=json.loads(raw);assert len(intermediate['results'])==2
    folder=(ROOT/'validation/md-z80-dma-intermediate-video-pattern-cache-bare').resolve();roots.append(folder)
    for row in intermediate['results']:
        assert row['updates']>1 and not row['updates']&1
        assert sha((folder/(row['region']+'-prefix-events.json')).read_bytes())==row['prefix_sha256']
        assert sha((folder/(row['region']+'-vram.bin')).read_bytes())==row['vram_sha256']
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','analysis/world_next.md','analysis/md_z80_video_service_milestone.md',
                 'tools/md_z80_video_fixture.py','tools/validate_md_z80_psg.py','tools/md_clock_service_kernel.py',
                 'tools/analyze_md_z80_dma_windows.py','tools/validate_md_z80_dma_intermediate.py','tools/archive_md_z80_video_service.py',
                 'tools/archive_lossless_evidence.py','validation/md-z80-video-service-trials-windows-run.log',
                 'validation/md-z80-dma-window-regression-run.log','validation/md-z80-video-pattern-cache-intermediate-run.log',
                 'validation/md-z80-video-pattern-cache-intermediate-initial-report-failure.log','validation/md-z80-video-service-world-prefix.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/md-z80-video-service-world-prefix.json').read_text())
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==previous['playable_sha256']
    metadata=dict(previous_manifest_sha256=sha(previous_raw),playable_sha256=previous['playable_sha256'],reports=reports,
        diagnostic_payload_cache_tested=True,rejected_service_optimizations=['video-service64-bare','video-batch-service-bare'],
        source_checkpoint_proof='video-pattern-cache-proof',video_frame_deadlines_accepted=False,
        production_integration=False,deadline_scheduler_accepted=False,audio_waveform_validated=False)
    freeze(ROOT,ROOT/'analysis/md-z80-video-service-v0203',paths,metadata,roots,'--cleanup' in sys.argv)


if __name__=='__main__':main()
