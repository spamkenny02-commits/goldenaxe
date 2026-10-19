"""Freeze polled publisher measurements and verified generated-file cleanup."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['poll128-bare','poll128-proof','poll-shared-edge','poll128-edge']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/md-z80-polled-v0203';assert not out.exists(),'Immutable archive exists'
    previous_raw=(ROOT/'analysis/md-psg-bulk-v0203/manifest.json').read_bytes();previous=json.loads(previous_raw)
    paths=set();reports={};roots=[]
    for variant in VARIANTS:
        root=(ROOT/('validation/md-z80-psg-'+variant)).resolve();roots.append(root)
        name='analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json'
        raw=(ROOT/name).read_bytes();reports[name]=sha(raw);report=json.loads(raw)
        live=variant in VARIANTS[:2];polled=variant!='poll-shared-edge'
        assert report['live_loader']==live and report['bare']==(variant=='poll128-bare')
        assert report.get('polled_transfer_attempts',0)==(128 if polled else 0)
        assert report['physical_phase_offset']==(0 if live else 3419)
        assert sha((root/'out/release/rom.bin').read_bytes())==report['kernel_sha256']
        assert sha((root/'driver.bin').read_bytes())==report['driver_sha256']
        source=(root/'driver-source.asm.snapshot').read_bytes();assert sha(source)==report['driver_source_sha256']
        assert source==(ROOT/'megadrive/z80/md_psg_prefetch_z80.asm').read_bytes()
        if polled:assert 'md_z80_psg_push_poll(&producer,' in (root/'src/main.c').read_text()
        for table in ['sources','headers']:
            for filename,digest in report[table].items():
                path=ROOT/'megadrive/src'/filename;assert sha(path.read_bytes())==digest,(variant,filename)
                paths.add(path)
        assert len(report['results'])==2
        for row in report['results']:
            assert row['done'] and not row['failures'] and not row['failure_code'] and row['plain_core_identical']
            assert row['cases']==48 and row['bytes']==2976 and row['extra_cases']==(0 if live else 26)
            assert row['errors_master'][0]>=0
            if variant=='poll128-bare':assert row['errors_master'][1]<163000
            assert sha((root/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
            assert sum(x['spacing_checks'] for x in row['rows'])==(96 if live else 596)
            for case in row['rows']:
                assert case['sample_gap_master'][1]<17100 and case['clock_line_advance'][1]<=5
                assert case['bus_holds_master'][1]<6840
            if not live:
                assert row['prefetched_commands']==64 and row['max_prefetched_pending']==15
                assert sum(x['counter_wraps'] for x in row['rows'])==1
        paths.add(ROOT/name);paths.add(ROOT/('validation/z80-psg-'+variant+'-run.log'))
    for name in ['analysis/md_z80_bridge_polled_shared_report.json','analysis/md_z80_polled_report.json']:
        raw=(ROOT/name).read_bytes();reports[name]=sha(raw);report=json.loads(raw)
        for filename,digest in report['sources'].items():assert sha((ROOT/'megadrive/src'/filename).read_bytes())==digest
        assert report['checks']==(12016 if 'bridge' in name else 132)
        paths.add(ROOT/name)
    roots.extend((ROOT/('validation/'+name)).resolve() for name in ['md-z80-bridge-polled-shared','md-z80-polled'])
    for root in roots:paths.update(p for p in root.rglob('*') if p.is_file())
    for name in ['README.md','analysis/world_next.md','analysis/md_z80_polled_milestone.md',
                 'megadrive/src/md_z80_psg.c','megadrive/src/md_z80_psg.h',
                 'tools/md_live_z80_kernel.py','tools/validate_md_z80_psg.py','tools/validate_md_z80_bridge.py',
                 'tools/validate_md_z80_polled.py','tools/archive_md_z80_polled.py',
                 'validation/md-z80-bridge-polled-shared-run.log','validation/md-z80-bridge-polled-initial-report-failure.log',
                 'validation/md-z80-polled-world-prefix.json']:
        paths.add(ROOT/name)
    for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:
        assert sha((ROOT/name).read_bytes())==previous['playable_sha256']
    prefix=json.loads((ROOT/'validation/md-z80-polled-world-prefix.json').read_text())
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    files={};compressed={};candidates=[]
    for path in sorted(paths):
        raw=path.read_bytes();digest=sha(raw);name=path.relative_to(ROOT).as_posix()
        if path.is_relative_to(ROOT/'validation') or len(raw)>65536:
            stored='objects/'+digest+'.gz';dest=out/stored;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            encoded=dest.read_bytes();assert gzip.decompress(encoded)==raw
            compressed[name]=dict(stored=stored,raw_sha256=digest,raw_bytes=len(raw),stored_sha256=sha(encoded))
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);files[name]=digest
        if any(path.is_relative_to(root) for root in roots) and (path.suffix in ['.bin','.out','.o','.s','.d','.dll'] or
            path.name.endswith(('-events.json','-clock.json')) or path.name in ['expected.h','psg.h']):candidates.append(path)
    manifest=dict(previous_manifest_sha256=sha(previous_raw),playable_sha256=previous['playable_sha256'],reports=reports,
        selected_measurement='poll128-bare',source_checkpoint_proof='poll128-proof',
        deadline_scheduler_accepted=False,production_integration=False,audio_waveform_validated=False,
        files=files,compressed=compressed,removed_verified_generated=[])
    target=out/'manifest.json';target.write_text(json.dumps(manifest,indent=2)+'\n')
    for name,digest in files.items():assert sha((out/name).read_bytes())==digest
    for item in compressed.values():
        encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
    if '--cleanup' in sys.argv:
        for path in candidates:
            resolved=path.resolve();assert any(resolved.is_relative_to(root) for root in roots)
            name=resolved.relative_to(ROOT).as_posix();assert not subprocess.check_output(['git','ls-files','--',name],cwd=ROOT)
            item=compressed[name];raw=resolved.read_bytes();assert sha(raw)==item['raw_sha256']
            assert gzip.decompress((out/item['stored']).read_bytes())==raw
            manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));resolved.unlink()
        target.write_text(json.dumps(manifest,indent=2)+'\n')
    print(len(compressed),'compressed references;',sum(x['bytes'] for x in manifest['removed_verified_generated']),'generated bytes removed')


if __name__=='__main__':main()
