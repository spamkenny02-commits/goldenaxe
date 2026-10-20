"""Freeze bounded contiguous-DMA tests and delivery-service limitations."""
from pathlib import Path
import gzip
import json
import sys
from archive_lossless_evidence import freeze,sha
from md_z80_source_video_fixture import convert_sms_patterns,jobs_per_case

ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['video-source-span4-bare','video-source-span4-proof','video-source-span3-tail',
          'video-source-span4-no-readback','video-source-span4-delivery']

def main():
    previous_raw=(ROOT/'analysis/md-z80-source-video-v0203/manifest.json').read_bytes();previous=json.loads(previous_raw)
    paths=set();roots=[];reports={}
    def report(name):
        path=ROOT/'analysis'/name;raw=path.read_bytes();paths.add(path);reports[path.relative_to(ROOT).as_posix()]=sha(raw);return json.loads(raw)
    baseline=json.loads((ROOT/'analysis/md_z80_psg_video_source_patterns_bare_report.json').read_bytes())
    expected_vram=baseline['results'][0]['video']['vram_sha256'];expected_image=baseline['results'][0]['video']['image_sha256']
    for variant in VARIANTS:
        folder=ROOT/('validation/md-z80-psg-'+variant);roots.append(folder)
        r=report('md_z80_psg_'+variant.replace('-','_')+'_report.json')
        assert r['live_loader'] and r['video_source_patterns'] and r['video_job_prepared'] and r['bulk_fifo_drain']
        assert r['bare']==(variant!='video-source-span4-proof') and len(r['results'])==2
        tiles=r['video_source_tiles'];jobs=48*jobs_per_case(tiles)
        assert tiles==(3 if variant=='video-source-span3-tail' else 4)
        assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
        assert sha((folder/'driver.bin').read_bytes())==r['driver_sha256']
        assert sha((folder/'driver-source.asm.snapshot').read_bytes())==r['driver_source_sha256']
        for table in ['sources','headers']:
            for name,digest in r[table].items():
                path=ROOT/'megadrive/src'/name;assert sha(path.read_bytes())==digest;paths.add(path)
        for row in r['results']:
            assert row['done'] and not row['failures'] and not row['failure_code'] and row['plain_core_identical']
            assert row['cases']==48 and row['bytes']==2976 and row['video_sources']==48
            assert row['video_updates']==24577 and row['video_requests']==24576
            assert row['video_job_preparations']==row['video_pattern_preparations']==row['video_dma_commits']==jobs
            assert row['video_readback_words']==(0 if variant.endswith('no-readback') else 393216) and not row['video_readback_errors']
            assert row['errors_master'][0]>=0 and sum(x['spacing_checks'] for x in row['rows'])==96
            for x in row['rows']:
                assert x['sample_gap_master'][1]<17100 and x['clock_line_advance'][1]<=5
                assert x['video_bus_holds_master'][1]<17100 and x['transport_bus_holds_master'][1]<6840
            region=row['region'];assert sha((folder/(region+'-events.json')).read_bytes())==row['events_sha256']
            source=(folder/(region+'-source-patterns.bin')).read_bytes();assert sha(source)==row['video_source_sha256']
            capture=folder/(region+'-plain');frame=row['frame'];vram=(capture/f'vram_{frame:05d}.bin').read_bytes()
            assert sha(vram)==row['video']['vram_sha256']==expected_vram
            assert bytes(vram[(512+n)^1] for n in range(16384))==convert_sms_patterns(source)
            assert sha((capture/f'frame_{frame:05d}.png').read_bytes())==row['video']['image_sha256']==expected_image
        paths.add(ROOT/('validation/z80-psg-'+variant+'-run.log'))
    windows=report('md_z80_video_spans_windows_report.json');assert len(windows['results'])==10
    assert sum(x['committed'] for x in windows['results'])==65664
    for r in windows['results']:
        assert r['hold_max']<=6214 and r['during_loader']==0
        assert r['report_sha256']==reports['analysis/md_z80_psg_'+r['variant'].replace('-','_')+'_report.json']
        if r['variant'].endswith('delivery'):assert r['before_last_psg']==(12 if r['region']=='ntsc' else 19)
        else:assert r['after_delivery_query']==r['committed']
    prior=report('md_z80_video_spans_prior_windows_report.json')
    old=json.loads((ROOT/'analysis/md_z80_source_video_windows_report.json').read_bytes());assert prior['results']==old['results']
    native=report('md_video_span_contract_report.json');assert all(r['done'] and r['checks']==44 and not r['failures'] for r in native['results'])
    for name,digest in native['sources'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==digest
    folder=ROOT/'validation/md-video-span-contract';roots.append(folder)
    for row in native['results']:assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','analysis/world_next.md','analysis/md_z80_video_spans_milestone.md',
                 'megadrive/src/pattern_convert.h','megadrive/src/pattern_pair_lut.inc',
                 'tools/md_z80_source_video_fixture.py','tools/md_z80_video_fixture.py','tools/md_live_z80_kernel.py',
                 'tools/validate_md_z80_psg.py','tools/analyze_md_z80_dma_windows.py','tools/archive_md_z80_video_spans.py',
                 'tools/validate_md_video_span_contract.py','tools/archive_lossless_evidence.py',
                 'validation/md-video-span-contract-run.log','validation/md-z80-video-spans-windows-run.log',
                 'validation/md-z80-video-spans-prior-windows-run.log','validation/md-z80-video-spans-world-prefix.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/md-z80-video-spans-world-prefix.json').read_bytes())
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==previous['playable_sha256']
    out=ROOT/'analysis/md-z80-video-spans-v0203'
    metadata=dict(previous_manifest_sha256=sha(previous_raw),playable_sha256=previous['playable_sha256'],reports=reports,
        source_checkpoint_proof='video-source-span4-proof',production_integration=False,
        contiguous_tiles_max=4,actual_audio_overlap_commits=dict(ntsc=12,pal=19),
        delivery_service_selected_as_scheduler=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False)
    manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
    assert json.loads((out/'manifest.json').read_bytes())==manifest
    for name,digest in manifest['files'].items():assert sha((out/name).read_bytes())==digest
    for item in manifest['compressed'].values():
        encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
    print('Independent contiguous-video archive readback passed.')

if __name__=='__main__':main()
