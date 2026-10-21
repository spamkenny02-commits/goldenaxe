"""Bind faster exact sprite masking and first-dungeon story evidence to v226."""
import json
from run_core import ROOT
from archive_lossless_evidence import sha

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());evidence={};reports={}
    for name in ['sprite_mask_equivalence_v0226_report.json','sprite_mask_production_v0226_report.json','world_frame_coherence_v0226_report.json','first_dungeon_story_v0226_report.json']:
        p=ROOT/'analysis'/name;r=json.loads(p.read_bytes());assert r['md_sha256']==digest and r['passed'];evidence[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes());reports[name]=r
    host=reports['sprite_mask_equivalence_v0226_report.json'];assert host['compiled_c_cases']==133120
    native=reports['sprite_mask_production_v0226_report.json'];assert len(native['cases'])==10 and all(c['identical_physical_sprite_frames']==9 and c['current_median_elapsed_master_cycles']<c['previous_median_elapsed_master_cycles'] for c in native['cases'])
    coherence=reports['world_frame_coherence_v0226_report.json'];assert len(coherence['cases'])==12 and all(c['differing_pixels']==0 for c in coherence['cases'])
    story=reports['first_dungeon_story_v0226_report.json'];assert story['first_dungeon_boss_crystal_exit_verified'] and not story['all_dungeon_rooms_explored'] and story['reward_window_normalized_rgb_pixels_exact']==9600
    stalls=[]
    for name in ['sms-auto-18','md-auto-18','md-auto-21']:
        path=ROOT/'validation/natural-dungeon-combat'/name/'boss_frames.json';rows=json.loads(path.read_bytes());repeats=[b['frame'] for a,b in zip(rows,rows[1:]) if a['state']==b['state'] and a['timer']==b['timer']]
        stalls.append(dict(case=name,observed_boss_death_frames=len(rows),repeated_simulation_timer_frames=repeats));evidence[path.relative_to(ROOT).as_posix()]=sha(path.read_bytes())
    assert [len(s['repeated_simulation_timer_frames']) for s in stalls]==[0,1,5]
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535;assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
    result=dict(md_sha256=digest,passed=True,checksum=f'{checksum:04X}',host_equivalence_cases=133120,production_sprite_plane_pixels_exact=sum(c['sprite_pixels_compared'] for c in native['cases']),production_timing_cases=native['cases'],first_dungeon_boss_crystal_exit_verified=True,natural_boss_death_examples=stalls,all_frame_deadlines_met=False,full_game_validated=False,source_rng_exact=False,evidence=evidence,source_files={name:sha((ROOT/name).read_bytes()) for name in ['megadrive/src/main.c','tools/natural_dungeon_combat.py','tools/validate_sprite_mask_equivalence.py','tools/validate_sprite_mask_production.py','tools/verify_first_dungeon_story.py']},limits=['Measured reductions apply to the masking routine on frozen controlled scenes; elapsed times may include IRQ work. They are not global FPS or fidelity percentages.','Natural boss particle streams differ: the examples show remaining stalls, not a controlled before/after performance comparison. The optimization does not solve all frame deadlines.','The first dungeon story path reaches boss/crystal/exit; optional rooms/items, other dungeons, hardware console and complete audio/RNG/cadence fidelity remain unfinished.'])
    (ROOT/'analysis/sprite_mask_release_v0226_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result['production_sprite_plane_pixels_exact'], 'sprite pixels exact;',stalls)

if __name__=='__main__':main()
