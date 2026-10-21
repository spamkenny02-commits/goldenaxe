"""Freeze natural controller route evidence and verify archive-backed replay checks."""
import json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    digest='39e6995514a87d170d4d1fc713938a3645905842fe93a340415c80e996057a31'
    report=ROOT/'analysis/natural_dungeon_route_v0223_report.json';before=report.read_bytes();r=json.loads(before)
    assert r['passed'] and r['md_sha256']==digest and not r['first_dungeon_cleared'] and not r['full_game_validated']
    assert not r['ram_mutations'] and not r['rom_mutations'] and not r['checkpoint_injections']
    for case in r['cases']:
        assert case['settled_playfield_normalized_pixels_compared']==81920
        for tag in ['reference','native']:assert case[tag]['fixed_input_replay_PNG_exact'] and case[tag]['dungeon_checkpoint_and_visited_flag']
    folder=ROOT/'validation/natural-dungeon-route';paths={p for p in folder.rglob('*') if p.is_file()}
    paths.update(ROOT.glob('validation/natural-route*.log'))
    paths.update(ROOT/n for n in ['README.md','analysis/world_next.md','analysis/natural_dungeon_route_v0223.md','analysis/natural_dungeon_route_v0223_report.json','validation/natural-route-world-prefix.json','tools/natural_dungeon_route.py','tools/verify_natural_dungeon_route.py','tools/archive_natural_dungeon_route.py','tools/archive_lossless_evidence.py','tools/run_core.py','tools/movement_reference.py','tools/extract_world.py','tools/extract_title.py','tools/validate_actor_tick.py','megadrive/src/main.c','megadrive/src/door_transition.inc','megadrive/out/release/symbol.txt','gaw-megadrive.bin','gaw-title-megadrive.bin','versions/index.json','versions/v0223-39e69955/natural_dungeon_route_v0223_report.json'])
    for name,h in r['evidence'].items():assert sha((ROOT/name).read_bytes())==h
    prefix=json.loads((ROOT/'validation/natural-route-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    assert sha((ROOT/'gaw-megadrive.bin').read_bytes())==digest
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==223
    out=ROOT/'analysis/natural-route-v0223';m=freeze(ROOT,out,paths,dict(playable_sha256=digest,original_sha256=original,production_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),numbered_roms_preserved=223,first_dungeon_cleared=False,full_game_validated=False),[folder],cleanup=True)
    result=subprocess.run([sys.executable,str(ROOT/'tools/verify_natural_dungeon_route.py'),'--verify-existing'],cwd=ROOT,capture_output=True,text=True)
    (ROOT/'validation/natural-route-archive-recovery.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stdout+result.stderr
    assert report.read_bytes()==before,'Archive recovery changed the verified report'
    assert all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in m['removed_verified_generated'])
    recovery=dict(md_sha256=digest,passed=True,report_byte_identical_after_cleanup=True,controller_replays_recovered=4,final_RAM_bytes_compared=2*(8192+65536),normalized_playfield_pixels_compared=163840,numbered_roms_preserved=len(roms),removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),original_sms_preserved=True)
    (ROOT/'analysis/natural_dungeon_route_recovery_v0223_report.json').write_text(json.dumps(recovery,indent=2)+'\n');print(recovery)

if __name__=='__main__':main()
