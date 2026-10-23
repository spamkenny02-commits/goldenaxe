"""Freeze audio channel and spell-wait evidence before generated cleanup."""
import gzip,json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    report=ROOT/'analysis/audio_channel_snapshot_release_v0267_report.json';before=report.read_bytes();release=json.loads(before);assert release['passed'];digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest==release['md_sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==267
    roots=[]
    for pattern in ['audio-channel-snapshot*','screen-spell-v0264-cpu*','screen-spell-v0265*','screen-spell-v0266*','screen-spell-v0267*','screen-spell-cost-host','world-frame-coherence-v0265','world-frame-coherence-v0266','world-frame-coherence-v0267']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    for pattern in ['analysis/audio_channel_snapshot*','analysis/screen_spell_v026[4567]*.json','analysis/screen_spell_cost_report.json','analysis/world_frame_coherence_v026[567]*.json','validation/audio-channel-snapshot*.log','validation/screen-spell-v026[4567]*.log','validation/screen-spell-cost*v026[567]*.log','validation/world-frame-coherence-v026[567]*.log','validation/build-v026[4567]*.log','validation/spell-v0264-disassembly.txt']:
        paths.update(p for p in ROOT.glob(pattern) if p.is_file())
    for name in ['README.md','analysis/world_next.md','validation/v0267-world-prefix.json','megadrive/src/main.c','megadrive/src/sound.inc','megadrive/src/screen_spell.inc','megadrive/src/source_audio_tone.c','megadrive/src/source_audio_noise.c','megadrive/out/release/symbol.txt','tools/profile_screen_spell_cpu.py','tools/validate_audio_channel_snapshot.py','tools/validate_audio_channel_snapshot_68k.py','tools/summarize_audio_channel_snapshot_release.py','tools/archive_audio_channel_snapshot_release.py','tools/validate_screen_spell.py']:
        paths.add(ROOT/name)
    for module in json.loads((ROOT/'analysis/audio_channel_snapshot_68k_report.json').read_bytes())['module_sha256']:
        paths.add(ROOT/'megadrive/src'/f'{module}.c')
    for e in json.loads((ROOT/'versions/index.json').read_bytes()):
        if 265<=e['version']<=267:paths.update((ROOT/'versions'/e['rom']).parent.iterdir())
    prefix=json.loads((ROOT/'validation/v0267-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/audio-channel-snapshot-v0267';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=267,full_game_verified=False),roots,cleanup=True)
    recovered=0
    for i in m['compressed'].values():
        encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];recovered+=len(raw)
    subprocess.run([sys.executable,'tools/summarize_audio_channel_snapshot_release.py'],cwd=ROOT,check=True);assert report.read_bytes()==before
    assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==release['source_sha256']
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=267,original_sms_preserved=True,release_identical_after_recovery=True,recovered_bytes_verified=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/audio_channel_snapshot_recovery_v0267_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
