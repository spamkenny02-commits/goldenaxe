"""Freeze retained DIVU mapping proof after rejected cooperative code is isolated."""
import gzip
import hashlib
import json
import subprocess
import sys
from actor_reference import ROOT


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    out=ROOT/'analysis/md-beam-divu-v0203';assert not out.exists()
    unit=json.loads((ROOT/'analysis/md_psg_plan_report.json').read_text());replay=json.loads((ROOT/'analysis/md_psg_replay_beam_report.json').read_text())
    previous=ROOT/'analysis/md-cooperative-research-v0203';reference_raw=(previous/'manifest.json').read_bytes();reference=json.loads(reference_raw)
    name='analysis/md_psg_plan_report.json';assert sha((ROOT/name).read_bytes())==reference['files'][name]
    kernel=reference['compressed']['validation/md-psg-plan/out/release/rom.bin'];encoded=(previous/kernel['stored']).read_bytes()
    assert sha(encoded)==kernel['stored_sha256'] and sha(gzip.decompress(encoded))==unit['kernel_sha256']
    assert unit['host']['cases']==21024 and unit['host']['beam_cases']==16950 and not unit['host']['failures']
    for r in unit['results']:assert r['done'] and not r['failures'] and r['cases']==2024 and r['beam_cases']==16950
    for name,h in unit['sources'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==h
    for name,h in replay['helpers'].items():assert sha((ROOT/'megadrive/src'/(name+'.c')).read_bytes())==h
    for name,h in replay['replay_sources'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==h
    folder=ROOT/'validation/md-psg-replay-beam';assert sha((folder/'out/release/rom.bin').read_bytes())==replay['kernel_sha256']
    assert sha((ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_io_libretro.dll').read_bytes())==replay['observer_core_sha256']
    for r in replay['results']:
        assert r['done'] and not r['failures'] and r['cases']==48 and r['extra_cases']==33 and r['bytes']==2976 and r['plain_core_identical']
        assert r['errors_master'][0]>=0 and r['errors_master'][1]<3420 and r['poll_gap_master'][1]<10260 and r['seed_gap_master'][1]<10260
        assert sha((folder/(r['region']+'-events.json')).read_bytes())==r['events_sha256']
    playable=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert playable=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    paths={ROOT/'README.md',ROOT/'analysis/world_next.md',ROOT/'analysis/md_beam_divu_milestone.md',ROOT/'analysis/md_psg_plan_report.json',ROOT/'analysis/md_psg_replay_beam_report.json'}
    paths.update(p for p in (ROOT/'megadrive/src').iterdir() if p.suffix in ['.c','.h','.s','.inc'])
    paths.update((ROOT/'megadrive/research').iterdir())
    paths.update(ROOT/'tools'/n for n in ['archive_md_beam_divu.py','validate_md_psg_plan.py','validate_md_psg_replay.py','validate_md_loading_audio.py','validate_queued_loading.py','validate_native_room_finish.py','validate_reader_timing.py'])
    paths.update(p for p in folder.rglob('*') if p.is_file())
    paths.update(ROOT/'validation'/n for n in ['cooperative-final-replay-run.log','beam-divu-playable-build.log','beam-divu-world-prefix.sha256'])
    files={};compressed={};remove=[]
    for p in sorted(paths):
        raw=p.read_bytes();h=sha(raw);name=p.relative_to(ROOT).as_posix()
        if p.is_relative_to(ROOT/'validation') or len(raw)>65536:
            stored='objects/'+h+'.gz';dest=out/stored;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(gzip.compress(raw,mtime=0))
            encoded=dest.read_bytes();assert gzip.decompress(encoded)==raw
            compressed[name]=dict(stored=stored,raw_sha256=h,raw_bytes=len(raw),stored_sha256=sha(encoded))
            if p.is_relative_to(folder) and (p.suffix in ['.bin','.out','.o','.s','.d','.dll'] or p.name.endswith(('-events.json','-clock.json')) or p.name in ['expected.h','psg.h']):remove.append(p)
        else:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);files[name]=h
    manifest=dict(playable_sha256=playable,unit_archive_manifest_sha256=sha(reference_raw),cooperative_scheduler_accepted=False,default_service_hooks_restored=True,files=files,compressed=compressed,removed_verified_generated=[])
    target=out/'manifest.json';target.write_text(json.dumps(manifest,indent=2)+'\n')
    for name,h in files.items():assert sha((out/name).read_bytes())==h
    for v in compressed.values():
        encoded=(out/v['stored']).read_bytes();assert sha(encoded)==v['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==v['raw_sha256'] and len(raw)==v['raw_bytes']
    if '--cleanup' in sys.argv:
        for p in remove:
            resolved=p.resolve();assert resolved.is_relative_to(folder.resolve());name=resolved.relative_to(ROOT).as_posix()
            assert not subprocess.check_output(['git','ls-files','--',name],cwd=ROOT)
            v=compressed[name];raw=resolved.read_bytes();assert sha(raw)==v['raw_sha256'] and gzip.decompress((out/v['stored']).read_bytes())==raw
            manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)));resolved.unlink()
        target.write_text(json.dumps(manifest,indent=2)+'\n')
    print(len(files),'source snapshots;',len(compressed),'compressed references;',sum(x['bytes'] for x in manifest['removed_verified_generated']),'generated bytes removed')


if __name__=='__main__':main()
