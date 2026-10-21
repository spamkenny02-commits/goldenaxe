"""Freeze descriptor-word evidence before generated binary cleanup."""
import json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());r=json.loads((ROOT/'analysis/actor_descriptor_release_v0228_report.json').read_bytes());assert r['md_sha256']==digest and r['passed']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==228
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roots=[ROOT/'validation/natural-dungeon-combat',ROOT/'validation/natural-dungeon-route/md-v0228']
    for pattern in ['actor-descriptor-v022*','actor-descriptor-production-v022*','world-frame-coherence-v022[78]']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths=set()
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    names=['README.md','build.ps1','megadrive/src/actors.c','megadrive/src/actor_descriptor_words.inc','megadrive/out/release/symbol.txt','tools/generate_actor_descriptor_words.py','tools/validate_actor_descriptor_words.py','tools/validate_sprite_mask_production.py','tools/verify_first_dungeon_story.py','tools/natural_dungeon_combat.py','tools/summarize_actor_descriptor_release.py','tools/archive_actor_descriptor_release.py','analysis/world_next.md','validation/v0228-world-prefix.json']
    paths.update(ROOT/n for n in names)
    for pattern in ['analysis/*v022[78]*.json','analysis/*v0228*.md','validation/v022[78]-*.log','validation/build-v022[78].log']:paths.update(ROOT.glob(pattern))
    paths.update((ROOT/'versions/v0228-a875719f').iterdir());paths.update((ROOT/'versions/v0227-4bea5e39').iterdir())
    prefix=json.loads((ROOT/'validation/v0228-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    before=(ROOT/'analysis/first_dungeon_story_v0228_report.json').read_bytes();out=ROOT/'analysis/actor-descriptor-v0228'
    m=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=228,first_dungeon_story_verified=True,full_game_validated=False,all_frame_deadlines_met=False),roots,cleanup=True)
    subprocess.run([sys.executable,'tools/verify_first_dungeon_story.py','--verify-existing','--native-final','md-auto-25','--native-modal','md-auto-24'],cwd=ROOT,check=True)
    assert (ROOT/'analysis/first_dungeon_story_v0228_report.json').read_bytes()==before and all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=228,original_sms_preserved=True,story_replay_final_ram_bytes_recovered=73728,reward_window_normalized_pixels_recovered=9600,final_source_native_flags_bytes_recovered=256,final_source_native_map_bytes_recovered=1280,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/actor_descriptor_recovery_v0228_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
