"""Bind immutable source-word decoding, production scene timing and story checks."""
import json
from run_core import ROOT
from archive_lossless_evidence import sha

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom);reports={};evidence={}
    for name in ['actor_descriptor_words_v0228_report.json','actor_descriptor_production_v0228_report.json','world_frame_coherence_v0228_report.json','first_dungeon_story_v0228_report.json']:
        p=ROOT/'analysis'/name;r=json.loads(p.read_bytes());assert r['md_sha256']==digest and r['passed'];reports[name]=r;evidence[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    words=reports['actor_descriptor_words_v0228_report.json'];assert words['compiled_c_addresses_exact']==65536 and words['native_rom_words_verified']==8425
    scenes=reports['actor_descriptor_production_v0228_report.json'];assert scenes['timing_stage']=='scene_before_mask' and len(scenes['cases'])==10
    overlap=[c for c in scenes['cases'] if c['case']=='overlap'];assert len(overlap)==2 and all(c['current_median_elapsed_master_cycles']<c['previous_median_elapsed_master_cycles'] for c in overlap)
    assert all(c['identical_physical_sprite_frames']==9 for c in scenes['cases'])
    coherence=reports['world_frame_coherence_v0228_report.json'];assert len(coherence['cases'])==12 and all(c['differing_pixels']==0 for c in coherence['cases'])
    story=reports['first_dungeon_story_v0228_report.json'];assert story['first_dungeon_boss_crystal_exit_verified'] and all(c['normal_continue_count']==0 for c in story['cases'])
    paths=[ROOT/'validation/natural-dungeon-combat'/name/'boss_frames.json' for name in ['sms-auto-18','md-auto-24']]
    source,native=[json.loads(p.read_bytes()) for p in paths];assert len(source)==len(native)==182 and [(r['state'],r['timer']) for r in source]==[(r['state'],r['timer']) for r in native]
    assert all(b['frame']==a['frame']+1 for a,b in zip(native,native[1:]))
    for p in paths:evidence[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535;assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
    result=dict(md_sha256=digest,passed=True,checksum=f'{checksum:04X}',native_words=8425,readonly_table_bytes=16850,host_address_cases=65536,identical_production_sprite_pixels=sum(c['sprite_pixels_compared'] for c in scenes['cases']),controlled_overlap_timing=overlap,first_dungeon_story_verified=True,natural_boss_death_state_timer_frames_exact=182,natural_boss_death_timer_stalls=0,all_frame_deadlines_met=False,full_game_validated=False,source_rng_exact=False,evidence=evidence,source_files={n:sha((ROOT/n).read_bytes()) for n in ['megadrive/src/actors.c','megadrive/src/actor_descriptor_words.inc','build.ps1','tools/generate_actor_descriptor_words.py','tools/validate_actor_descriptor_words.py','tools/validate_sprite_mask_production.py','tools/natural_dungeon_combat.py','tools/verify_first_dungeon_story.py']},limits=['Scene construction speed is measured on the same frozen12-actor setup; it is not a global FPS gain. Hero-only timing is essentially unchanged and may differ by a few master cycles.','The natural182-frame boss state/timer sequence matches this SMS run; different encounters/particle streams prevent a controlled whole-route speed comparison or an all-scenes deadline claim.','First-dungeon story path only: optional rooms/items, other dungeons, complete audio/cadence/RNG fidelity and real hardware remain unfinished.'])
    (ROOT/'analysis/actor_descriptor_release_v0228_report.json').write_text(json.dumps(result,indent=2)+'\n');print(overlap)

if __name__=='__main__':main()
