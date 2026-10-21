"""Freeze v0225 evidence before removing regenerated binary captures."""
import json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());r=json.loads((ROOT/'analysis/terrain_publication_v0225_report.json').read_bytes());assert r['passed'] and r['md_sha256']==digest
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==225
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roots=[ROOT/'validation/cell-publication-v0224',ROOT/'validation/cell-publication-v0225',ROOT/'validation/natural-dungeon-combat',ROOT/'validation/natural-dungeon-route/md-v0225']
    for pattern in ['*-clear-gameplay-*-puzzles*','*second-spell-terrain*']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths=set()
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','megadrive/src/main.c','megadrive/out/release/symbol.txt','analysis/terrain_publication_v0225.md','analysis/terrain_publication_v0225_report.json','analysis/natural_dungeon_progress_v0225_report.json','validation/puzzles_gameplay_report.json','validation/puzzles_gameplay-pal_report.json','validation/second_spell_terrain_report.json','tools/validate_cell_publication.py','tools/summarize_terrain_publication_release.py','tools/natural_dungeon_combat.py','tools/verify_natural_dungeon_progress.py','tools/archive_terrain_publication_release.py','analysis/world_next.md','validation/v0225-world-prefix.json']:
        paths.add(ROOT/name)
    paths.update(ROOT.glob('analysis/cell_publication_v022[45]*_report.json'));paths.update(ROOT.glob('validation/v0225-*.log'));paths.add(ROOT/'validation/build-v0225.log')
    paths.update((ROOT/'versions/v0225-71b56c3c').iterdir())
    before=(ROOT/'analysis/natural_dungeon_progress_v0225_report.json').read_bytes()
    prefix=json.loads((ROOT/'validation/v0225-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/terrain-publication-v0225';m=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=225,first_dungeon_cleared=False,full_game_validated=False),roots,cleanup=True)
    subprocess.run([sys.executable,'tools/verify_natural_dungeon_progress.py','--verify-existing'],cwd=ROOT,check=True)
    assert (ROOT/'analysis/natural_dungeon_progress_v0225_report.json').read_bytes()==before
    assert all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in m['removed_verified_generated'])
    result=dict(md_sha256=digest,passed=True,natural_replay_final_ram_bytes_recovered=73728,natural_source_native_map_bytes_recovered=1280,natural_source_native_flags_bytes_recovered=256,numbered_roms_preserved=len(roms),original_sms_preserved=True,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/terrain_publication_recovery_v0225_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
