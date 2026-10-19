"""Freeze clock/client/live-loading proof, including rejected blocking timing."""
import gzip
import hashlib
import json
import re
import subprocess
import sys
from actor_reference import ROOT

FOLDERS=['md-service-clock','md-service-clock-candidate','md-service-client','md-service-io-core','md-loading-audio','md-loading-audio-prepared','md-loading-audio-bare']
REPORTS=['md_service_clock_report.json','md_service_clock_candidate_report.json','md_service_client_report.json','md_loading_audio_report.json','md_loading_audio_bare_report.json']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/md-service-clock-v0203';assert not out.exists(),'Immutable archive exists'
    reports={n:json.loads((ROOT/'analysis'/n).read_text()) for n in REPORTS}
    for name,report in reports.items():
        for key in ['sources','assembly_sources']:
            for filename,h in report.get(key,{}).items():
                if filename=='md_service_clock_z80.asm':
                    path=ROOT/('validation/md-service-clock/driver-source.asm.snapshot' if name==REPORTS[0] else 'megadrive/z80/md_service_clock_z80.asm')
                else:path=ROOT/'megadrive/src'/(filename if '.' in filename else filename+'.c')
                assert sha(path.read_bytes())==h,(name,filename)
    for name,folder_name in [(REPORTS[0],FOLDERS[0]),(REPORTS[1],FOLDERS[1]),(REPORTS[3],FOLDERS[5]),(REPORTS[4],FOLDERS[6])]:
        report=reports[name];folder=ROOT/'validation'/folder_name
        assert sha((folder/'out/release/rom.bin').read_bytes())==report['kernel_sha256']
        assert sha((folder/'driver.bin').read_bytes())==report['driver_sha256']
        assert sha((ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_service_io_libretro.dll').read_bytes())==report['observer_core_sha256']
        for r in report['results']:
            assert r['done'] and not r['failures'] and r['plain_core_identical']
            raw=(folder/(r['region']+'-events.json')).read_bytes();assert sha(raw)==r['events_sha256']
            if name in REPORTS[:2]:
                assert r['count']==1200 and r['counter_wraps']==14 and r['z80_sample_gap_master'][1]<17100
            else:
                assert r['cases']==48 and r['bytes']==2976
                assert 0<=r['errors_master'][0] and r['errors_master'][1]>3420
                assert len(r['rows'])==48 and all(x['finish_delta']>0 for x in r['rows'])
                assert all(x['z80_sample_gap_master'][1]<17100 for x in r['rows'])
                assert sha((folder/'driver-source.asm.snapshot').read_bytes())==report['driver_source_sha256']
    client=reports[REPORTS[2]];assert client['checks']==523639 and sum(r['cases'] for r in client['results'])==523625
    assert reports[REPORTS[1]]['sample_delay']==48
    assert int(re.search(rb'loop:\s+ld b,(\d+)',(ROOT/'validation/md-service-clock/driver-source.asm.snapshot').read_bytes())[1])==24
    for filename,h in client['references'].items():assert sha((ROOT.parents[1]/'work/genesis-plus-gx/core'/filename).read_bytes())==h
    for filename in ['mem68k.c','vdp_ctrl.c']:
        assert sha((ROOT.parents[1]/'work/genesis-plus-gx/core'/filename).read_bytes())==(ROOT/'validation/md-service-io-core'/(filename+'-original.sha256')).read_text().strip()
    playable=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert playable=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    paths={ROOT/'README.md',ROOT/'analysis/md_service_clock_milestone.md',ROOT/'analysis/world_next.md'}
    paths.update(ROOT/'analysis'/name for name in REPORTS)
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.inc','.s'])
    paths.add(ROOT/'megadrive/z80/md_service_clock_z80.asm')
    paths.update(ROOT/'tools'/name for name in ['archive_md_service_clock.py','validate_md_service_clock.py','validate_md_service_client.py','validate_md_loading_audio.py','build_md_io_core.py','build_timing_core.py','validate_queued_loading.py','validate_native_room_finish.py','validate_reader_timing.py','run_core.py','actor_reference.py'])
    for name in FOLDERS:paths.update(p for p in (ROOT/'validation'/name).rglob('*') if p.is_file())
    paths.update(p for p in (ROOT/'validation').iterdir() if p.is_file() and (p.name.startswith('service-') or p.name.startswith('md-loading-audio-')))
    orphan=ROOT/'megadrive/out/release/src/md_service_clock_z80.s'
    if orphan.exists():paths.add(orphan)
    files={};compressed={};candidates=[]
    def retain(name,raw,compress):
        h=sha(raw)
        if compress:
            blob='objects/'+h+'.gz';dest=out/blob;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            encoded=dest.read_bytes();assert gzip.decompress(encoded)==raw
            compressed[name]=dict(stored=blob,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(encoded))
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);assert dest.read_bytes()==raw;files[name]=h
    for p in sorted(paths):
        raw=p.read_bytes();name=p.relative_to(ROOT).as_posix();retain(name,raw,p.is_relative_to(ROOT/'validation') or p==orphan or len(raw)>65536)
        inside=any(p.is_relative_to(ROOT/'validation'/n) for n in FOLDERS)
        if inside and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name.endswith('-events.json') or p.name=='expected.h'):candidates.append(p)
        if p==orphan or p==ROOT/'validation/service-clock.bin':candidates.append(p)
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_service_io_libretro.dll'
    retain('emulator/'+core.name,core.read_bytes(),True)
    data=dict(playable_sha256=playable,hardware_clock_validated=True,game_audio_on_68000=True,blocking_loader_scheduler_accepted=False,production_integration=False,
              rejected_research='md-loading-audio initial setup-in-budget and startup-mute parsing attempt preserved; prepared/bare reports prove blocking schedule misses deadlines. No deadline gate relaxed.',
              files=files,compressed=compressed,removed_verified_generated=[])
    manifest=out/'manifest.json';manifest.write_text(json.dumps(data,indent=2)+'\n')
    # Independent readback of every stored object precedes any removal.
    for name,h in files.items():assert sha((out/name).read_bytes())==h
    for item in compressed.values():
        encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded)
        assert len(raw)==item['raw_bytes'] and sha(raw)==item['raw_sha256']
    if '--cleanup' in sys.argv:
        for p in candidates:
            target=p.resolve();assert any(target.is_relative_to((ROOT/'validation'/n).resolve()) for n in FOLDERS) or target==orphan.resolve() or target==(ROOT/'validation/service-clock.bin').resolve()
            name=target.relative_to(ROOT).as_posix();assert not subprocess.check_output(['git','ls-files','--',name],cwd=ROOT)
            item=compressed[name];raw=target.read_bytes();assert sha(raw)==item['raw_sha256'] and gzip.decompress((out/item['stored']).read_bytes())==raw
            data['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));target.unlink()
        manifest.write_text(json.dumps(data,indent=2)+'\n')
    print(len(files),'snapshots;',len(compressed),'compressed references;',sum(x['bytes'] for x in data['removed_verified_generated']),'generated bytes removed')


if __name__=='__main__':main()
