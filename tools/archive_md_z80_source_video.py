"""Retain real SMS-mirror -> MD DMA/readback evidence before generated cleanup."""
from pathlib import Path
import gzip
import json
import sys
from archive_lossless_evidence import freeze,sha
from md_z80_source_video_fixture import convert_sms_patterns

ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['video-source-patterns-bare','video-source-patterns-proof']

def main():
    previous_raw=(ROOT/'analysis/md-z80-prepared-video-v0203/manifest.json').read_bytes();previous=json.loads(previous_raw)
    paths=set();roots=[];reports={}
    def report(name):
        path=ROOT/'analysis'/name;raw=path.read_bytes();paths.add(path);reports[path.relative_to(ROOT).as_posix()]=sha(raw);return json.loads(raw)
    for variant in VARIANTS:
        folder=ROOT/('validation/md-z80-psg-'+variant);roots.append(folder)
        r=report('md_z80_psg_'+variant.replace('-','_')+'_report.json')
        assert r['live_loader'] and r['video_source_patterns'] and r['video_job_prepared'] and r['bulk_fifo_drain']
        assert r['bare']==variant.endswith('bare') and r['max_frames']==30000 and len(r['results'])==2
        kernel=sha((folder/'out/release/rom.bin').read_bytes());assert kernel==r['kernel_sha256']
        if variant.endswith('bare'):assert kernel==json.loads((folder/'initial-kernel-sha256.json').read_bytes())['sha256']
        for table in ['sources','headers']:
            for name,digest in r[table].items():
                path=ROOT/'megadrive/src'/name;assert sha(path.read_bytes())==digest;paths.add(path)
        original=json.loads((folder/'report-before-atlas-description.json.snapshot').read_bytes())
        assert original['results']==r['results'] and original['kernel_sha256']==kernel
        for row in r['results']:
            assert row['done'] and not row['failures'] and not row['failure_code'] and row['plain_core_identical']
            assert row['cases']==48 and row['bytes']==2976 and row['video_sources']==48
            assert row['video_updates']==24577 and row['video_requests']==row['video_job_preparations']==row['video_pattern_preparations']==24576
            assert row['video_readback_words']==393216 and not row['video_readback_errors'] and row['errors_master'][0]>=0
            assert sum(x['spacing_checks'] for x in row['rows'])==96
            for x in row['rows']:
                assert x['sample_gap_master'][1]<17100 and x['clock_line_advance'][1]<=5
                assert x['video_bus_holds_master'][1]<=4138 and x['transport_bus_holds_master'][1]<6840
            region=row['region'];assert sha((folder/(region+'-events.json')).read_bytes())==row['events_sha256']
            source=(folder/(region+'-source-patterns.bin')).read_bytes();assert sha(source)==row['video_source_sha256']
            capture=folder/(region+'-plain');frame=row['frame']
            vram=(capture/f'vram_{frame:05d}.bin').read_bytes()
            assert sha(vram)==row['video']['vram_sha256'] and bytes(vram[(512+n)^1] for n in range(16384))==convert_sms_patterns(source)
            assert sha((capture/f'frame_{frame:05d}.png').read_bytes())==row['video']['image_sha256']
        paths.add(ROOT/('validation/z80-psg-'+variant+'-run.log'))
    windows=report('md_z80_source_video_windows_report.json');assert len(windows['results'])==4
    for r in windows['results']:
        assert r['committed']==24576 and r['during_loader']==0 and r['after_delivery_query']==24576 and r['hold_max']==4138
        assert r['report_sha256']==reports['analysis/md_z80_psg_'+r['variant'].replace('-','_')+'_report.json']
    prior=report('md_z80_source_video_prior_windows_report.json')
    old=json.loads((ROOT/'analysis/md_z80_prepared_dma_windows_report.json').read_bytes())
    assert prior['results']==old['results']
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','analysis/world_next.md','analysis/md_z80_source_video_milestone.md',
                 'megadrive/src/pattern_convert.h','megadrive/src/pattern_pair_lut.inc',
                 'tools/md_z80_source_video_fixture.py','tools/md_z80_video_fixture.py','tools/md_live_z80_kernel.py',
                 'tools/validate_md_z80_psg.py','tools/analyze_md_z80_dma_windows.py','tools/archive_md_z80_source_video.py',
                 'tools/archive_lossless_evidence.py','validation/md-z80-source-video-windows-run.log',
                 'validation/md-z80-source-video-prior-windows-run.log','validation/md-z80-source-video-world-prefix.json',
                 'validation/md-z80-source-video-archive-initial-failure.log','validation/md-z80-source-video-archive-failure-audit.json',
                 'analysis/md-z80-source-video-v0203-failed-readback/manifest.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/md-z80-source-video-world-prefix.json').read_bytes())
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==previous['playable_sha256']
    out=ROOT/'analysis/md-z80-source-video-v0203'
    metadata=dict(previous_manifest_sha256=sha(previous_raw),playable_sha256=previous['playable_sha256'],reports=reports,
        source_checkpoint_proof='video-source-patterns-proof',production_integration=False,
        actual_sms_pattern_payload=True,native_word_readback=True,scene_fidelity_validated=False,
        video_frame_deadlines_accepted=False,audio_waveform_validated=False)
    initial=ROOT/'analysis/md-z80-source-video-v0203-failed-readback/manifest.json'
    metadata['initial_archive_attempt_manifest_sha256']=sha(initial.read_bytes())
    manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
    assert json.loads((out/'manifest.json').read_bytes())==manifest
    for name,digest in manifest['files'].items():assert sha((out/name).read_bytes())==digest
    for item in manifest['compressed'].values():
        encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
    print('Independent final source-video archive readback passed.')

if __name__=='__main__':main()
