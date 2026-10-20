"""Preserve phase-released native video evidence before verified generated cleanup."""
from pathlib import Path
import gzip
import json
import subprocess
import sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]

def main():
    previous=ROOT/'analysis/md-z80-grant-backoff-v0203/manifest.json'
    old=json.loads(previous.read_bytes())
    # The explicit set separates this investigation from earlier archived trials.
    variants=['video-source-phase4-repeat','video-source-phase4-proof','video-source-phase4-fast']
    contracts=[]
    roots=[ROOT/('validation/md-z80-psg-'+x) for x in variants]
    roots += [ROOT/('validation/md-video-span-contract-'+x) for x in contracts]
    assert all(p.is_dir() for p in roots)
    paths=set(p for d in roots for p in d.rglob('*') if p.is_file())
    reports={}
    for variant in variants:
        path=ROOT/('analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json')
        if path.exists():reports[path]=json.loads(path.read_bytes())
    for variant in contracts:
        path=ROOT/('analysis/md_video_span_contract_'+variant.replace('-','_')+'_report.json')
        reports[path]=json.loads(path.read_bytes())
    for name in ['md_z80_phase_video_windows_report.json','md_z80_phase_prior_windows_report.json']:
        path=ROOT/'analysis'/name;reports[path]=json.loads(path.read_bytes())
    snapshots=list(ROOT.glob('validation/**/md_z80_video_span.*.snapshot'))
    for path,report in reports.items():
        paths.add(path)
        for name,digest in {**report.get('sources',{}),**report.get('headers',{})}.items():
            current=ROOT/'megadrive/src'/name
            matches=[p for p in [current]+snapshots if p.is_file() and sha(p.read_bytes())==digest]
            assert matches,(path,name,digest)
            paths.add(matches[0])
        if 'kernel_sha256' in report:
            folder=ROOT/('validation/md-z80-psg-'+path.stem.removeprefix('md_z80_psg_').removesuffix('_report').replace('_','-')) if path.name.startswith('md_z80_psg_') else ROOT/('validation/md-video-span-contract-'+path.stem.removeprefix('md_video_span_contract_').removesuffix('_report').replace('_','-'))
            assert sha((folder/'out/release/rom.bin').read_bytes())==report['kernel_sha256']
            for row in report['results']:
                assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
    for variant in variants:
        paths.update(ROOT.glob('validation/z80-psg-'+variant+'-*.log'))
    for name in ['README.md','analysis/world_next.md','analysis/md_z80_source_phases_milestone.md',
                 'megadrive/src/md_z80_video_span.c','megadrive/src/md_z80_video_span.h',
                 'megadrive/z80/md_psg_refresh_z80.asm',
                 'tools/md_z80_phase_video_fixture.py','tools/md_clock_service_kernel.py',
                 'tools/validate_md_z80_psg.py','tools/validate_md_video_span_contract.py',
                 'tools/md_z80_source_video_fixture.py','tools/analyze_md_z80_dma_windows.py',
                 'tools/archive_md_z80_source_phases.py','tools/archive_lossless_evidence.py',
                 'validation/md-z80-source-phases-world-prefix.json']:
        paths.add(ROOT/name)
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:
        assert sha((ROOT/name).read_bytes())==old['playable_sha256']
    metadata=dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],
      reports={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in reports},
      rejected=[],phase_release=dict(prefix_pc=0x1706,tail_pc=0x1deb,prefix_tiles=448,tail_tiles=64),
      production_integration=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False)
    out=ROOT/'analysis/md-z80-source-phases-v0203'
    manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
    for item in manifest['compressed'].values():
        encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
    print('Independent source-phase archive readback passed.')

if __name__=='__main__':main()
