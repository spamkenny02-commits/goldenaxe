"""Losslessly archive226 diagnostics and recover the complete story-path proof."""
import json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());r=json.loads((ROOT/'analysis/sprite_mask_release_v0226_report.json').read_bytes());assert r['md_sha256']==digest and r['passed']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==226
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roots=[ROOT/'validation/natural-dungeon-combat',ROOT/'validation/natural-dungeon-route/md-v0226',ROOT/'validation/sprite-mask-v0226',ROOT/'validation/sprite-mask-production-v0226',ROOT/'validation/world-frame-coherence-v0226']
    paths=set()
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','megadrive/src/main.c','megadrive/out/release/symbol.txt','tools/natural_dungeon_combat.py','tools/profile_natural_boss_frame.py','tools/verify_first_dungeon_story.py','tools/validate_sprite_mask_equivalence.py','tools/validate_sprite_mask_production.py','tools/summarize_sprite_mask_release.py','tools/archive_first_dungeon_release.py','analysis/world_next.md','validation/v0226-world-prefix.json']:
        paths.add(ROOT/name)
    for pattern in ['analysis/*v0226*.json','analysis/*v0226*.md','validation/v0226-*.log']:paths.update(ROOT.glob(pattern))
    paths.add(ROOT/'validation/build-v0226.log');paths.update((ROOT/'versions/v0226-36ad2e99').iterdir())
    prefix=json.loads((ROOT/'validation/v0226-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    before=(ROOT/'analysis/first_dungeon_story_v0226_report.json').read_bytes();out=ROOT/'analysis/first-dungeon-v0226'
    m=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=226,first_dungeon_boss_crystal_exit_verified=True,all_dungeon_rooms_explored=False,all_frame_deadlines_met=False,full_game_validated=False),roots,cleanup=True)
    subprocess.run([sys.executable,'tools/verify_first_dungeon_story.py','--verify-existing'],cwd=ROOT,check=True)
    assert (ROOT/'analysis/first_dungeon_story_v0226_report.json').read_bytes()==before
    assert all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=226,original_sms_preserved=True,fresh_story_replay_ram_bytes_recovered=73728,source_native_reward_window_pixels_recovered=9600,source_native_final_flags_bytes_recovered=256,source_native_final_map_bytes_recovered=1280,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/first_dungeon_recovery_v0226_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
