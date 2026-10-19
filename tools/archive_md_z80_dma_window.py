"""Verify successful/rejected32byte DMA guard experiments before archiving."""
from pathlib import Path
import json
import sys
from archive_lossless_evidence import freeze,sha

ROOT=Path(__file__).resolve().parents[1]
ACCEPTED=['video-dma-command-bare','video-dma-snapshot-bare','video-dma-snapshot-proof']
FAILED={'same_line':'video-dma-bare','two_lines':'video-dma-two-lines-bare',
        'fast_one_line':'video-dma-fast-bare','fast_two':'video-dma-fast-two-bare'}


def main():
    previous_raw=(ROOT/'analysis/md-z80-video-v0203/manifest.json').read_bytes();previous=json.loads(previous_raw)
    paths=set();reports={};roots=[]
    for variant in ACCEPTED:
        folder=(ROOT/('validation/md-z80-psg-'+variant)).resolve();roots.append(folder)
        name='analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json'
        raw=(ROOT/name).read_bytes();r=json.loads(raw);reports[name]=sha(raw);paths.add(ROOT/name)
        assert r['video_fixture']=='dma' and r['live_loader'] and r['bulk_fifo_drain'] and r['polled_transfer_attempts']==128
        assert r['bare']==variant.endswith('bare') and len(r['results'])==2
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        assert sha((folder/'driver.bin').read_bytes())==r['driver_sha256']
        assert (folder/'driver-source.asm.snapshot').read_bytes()==(ROOT/'megadrive/z80/md_psg_prefetch_z80.asm').read_bytes()
        for table in ['sources','headers']:
            for filename,digest in r[table].items():
                path=folder/(filename+'.snapshot')
                if not path.exists():path=ROOT/'megadrive/src'/filename
                assert sha(path.read_bytes())==digest,(variant,filename);paths.add(path)
        original=(folder/'original-report-before-limit-clarification.json.snapshot').read_bytes()
        assert sha(original)==r['limit_text_correction']['previous_sha256']
        old=json.loads(original);check=json.loads(raw);check.pop('limit_text_correction');check['limits']=old['limits'];assert check==old
        for row in r['results']:
            assert row['done'] and not row['failures'] and not row['failure_code'] and row['plain_core_identical']
            assert row['cases']==48 and row['bytes']==2976 and not row['extra_cases']
            assert row['video_requests']==2784 and row['video_updates']==2785 and row['errors_master'][0]>=0
            assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
            assert sum(x['spacing_checks'] for x in row['rows'])==96
            for x in row['rows']:
                assert x['sample_gap_master'][1]<17100 and x['clock_line_advance'][1]<=5
                assert x['video_bus_holds_master'][1]<17100 and x['transport_bus_holds_master'][1]<6840
            capture=folder/(row['region']+'-plain');frame=row['frame']
            for name,key in [(f'vram_{frame:05d}.bin','vram_sha256'),(f'vdp_regs_{frame:05d}.bin','registers_sha256'),(f'frame_{frame:05d}.png','image_sha256')]:
                assert sha((capture/name).read_bytes())==row['video'][key]
        paths.add(ROOT/('validation/z80-psg-'+variant+'-run.log'))
    for label,variant in FAILED.items():
        folder=(ROOT/('validation/md-z80-psg-'+variant)).resolve();roots.append(folder)
        name='analysis/md_z80_video_dma_'+label+'_failure_report.json'
        raw=(ROOT/name).read_bytes();r=json.loads(raw);reports[name]=sha(raw);paths.add(ROOT/name)
        assert r['status']=='failed' and r['observed']['failures']
        assert sha((folder/'ntsc-events.json').read_bytes())==r['events_sha256']
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        for n,digest in r['source_snapshots'].items():assert sha((folder/(n+'.snapshot')).read_bytes())==digest
        paths.add(ROOT/('validation/z80-psg-'+variant+'-run.log'))
    name='analysis/md_z80_dma_windows_report.json';raw=(ROOT/name).read_bytes();reports[name]=sha(raw);paths.add(ROOT/name)
    windows=json.loads(raw);assert len(windows['results'])==6
    for row in windows['results']:
        assert row['committed']==2784 and row['hold_max']<=3676
        name='analysis/md_z80_psg_'+row['variant'].replace('-','_')+'_report.json';assert row['report_sha256']==reports[name]
    name='analysis/md_z80_dma_intermediate_report.json';raw=(ROOT/name).read_bytes();reports[name]=sha(raw);paths.add(ROOT/name)
    intermediate=json.loads(raw);assert len(intermediate['results'])==2
    folder=(ROOT/'validation/md-z80-dma-intermediate').resolve();roots.append(folder)
    for row in intermediate['results']:
        assert row['updates']>1 and not row['updates']&1
        assert sha((folder/(row['region']+'-prefix-events.json')).read_bytes())==row['prefix_sha256']
        assert sha((folder/(row['region']+'-vram.bin')).read_bytes())==row['vram_sha256']
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','analysis/world_next.md','analysis/md_z80_dma_window_milestone.md',
                 'megadrive/src/md_z80_video_dma.c','megadrive/src/md_z80_video_dma.h',
                 'tools/md_z80_video_fixture.py','tools/validate_md_z80_psg.py','tools/analyze_md_z80_dma_windows.py',
                 'tools/validate_md_z80_dma_intermediate.py','tools/archive_lossless_evidence.py','tools/archive_md_z80_dma_window.py',
                 'validation/md-z80-dma-windows-run.log','validation/md-z80-dma-intermediate-run.log','validation/md-z80-dma-world-prefix.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/md-z80-dma-world-prefix.json').read_text())
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==previous['playable_sha256']
    metadata=dict(previous_manifest_sha256=sha(previous_raw),playable_sha256=previous['playable_sha256'],reports=reports,
        selected_measurement='video-dma-snapshot-bare',source_checkpoint_proof='video-dma-snapshot-proof',
        dma32_runtime_tested=True,video_frame_deadlines_accepted=False,production_integration=False,
        deadline_scheduler_accepted=False,audio_waveform_validated=False)
    freeze(ROOT,ROOT/'analysis/md-z80-dma-window-v0203',paths,metadata,roots,'--cleanup' in sys.argv)


if __name__=='__main__':main()
