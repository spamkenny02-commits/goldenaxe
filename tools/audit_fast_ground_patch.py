"""Bind fast normal-ground movement to original resources and runtime evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    assert sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535==int.from_bytes(rom[0x18e:0x190],'big')
    previous=json.loads((ROOT/'versions/v0093-28ce141a/water_cross_patch_audit.json').read_bytes())
    baseline=ROOT/'analysis/fast-ground-baseline-v0093/main.c'
    assert sha(baseline)==previous['source_files']['megadrive/src/main.c']
    current=(ROOT/'megadrive/src/main.c').read_text()
    current=current.replace('world_hero_frames[],world_walk_table[],world_fast_ground_walk[];','world_hero_frames[],world_walk_table[];')
    current=current.replace('/* 32ED..32F6 selects fast movement with C0EE; 26E5..2718 integrates. */','/* Normal-ground subset of 3295..33DA and object integration 26E5..2718. */')
    current=current.replace('    const u8 *walk=hero_terrain_context==3?world_water_walk+(hero_attack_speed?17:0):\n        hero_terrain_context==0 && hero_attack_speed?world_fast_ground_walk:world_walk_table;\n','')
    current=current.replace('hero_counter=walk[0];','hero_counter=hero_terrain_context==3?world_water_walk[hero_attack_speed?17:0]:world_walk_table[0];')
    current=current.replace('walk+1+accepted*4','(hero_terrain_context==3?world_water_walk+(hero_attack_speed?17:0):world_walk_table)+1+accepted*4')
    current=current.replace('    if(record[2]==14) hero_attack_speed=hero_items[14];\n','')
    assert current==baseline.read_text(),'Undeclared main.c changes'
    save=(ROOT/'megadrive/src/save.inc').read_text().replace('hero_fire_charge=game_save_state[0x16];hero_attack_speed=hero_items[14];','hero_fire_charge=game_save_state[0x16];hero_attack_speed=0;')
    assert save==(ROOT/'analysis/fast-ground-baseline-v0093/save.inc').read_text()
    source=(ROOT/'input/original.sms').read_bytes();resource=json.loads((ROOT/'analysis/fast_ground_resources.json').read_bytes())
    expected='#include <genesis.h>\nconst u8 world_fast_ground_walk[] = { '+','.join(hex(v) for v in source[0x3441:0x3452])+' };\n'
    assert (ROOT/'megadrive/src/fast_ground_data.c').read_text()==expected and resource['source_sha256']==hashlib.sha256(source).hexdigest()
    assert resource['generated_sha256']==sha(ROOT/'megadrive/src/fast_ground_data.c')
    old=json.loads((ROOT/'versions/v0089-1942f987/thrown_axe_patch_audit.json').read_bytes())
    for name in ['megadrive/src/actors.c','megadrive/src/thrown_axe_data.c']:assert sha(ROOT/name)==old['source_files'][name]
    old=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    assert sha(ROOT/'analysis/fast-ground-baseline-v0093/save.inc')==old['unchanged_production_assets']['megadrive/src/save.inc']
    for name,h in old['unchanged_production_assets'].items():
        if name not in ['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/rom_header.c','megadrive/src/save.inc']:assert sha(ROOT/name)==h
    old=json.loads((ROOT/'versions/v0084-7de7d76b/second_spell_patch_audit.json').read_bytes());assert sha(ROOT/'megadrive/src/second_spell_data.c')==old['source_files']['megadrive/src/second_spell_data.c']
    reports=[]
    for name in ['ground_walk_report.json','water_cross_pose_report.json','water_cross_all_diagnostic.json','ground_cross_all_diagnostic.json','fast_ground_cross_improvement.json','thrown_axe_walk_report.json','thrown_axe_walk_fast_report.json','timing_report.json','timing-pal_report.json','item_rewards_gameplay_report.json','item_rewards_gameplay-pal_report.json','item_rewards_save_report.json']:
        p=ROOT/'validation'/name;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,name
        if name=='ground_walk_report.json':assert len(d['cases'])==16 and all(c['frames_exact']==121 and c['hero_pattern_frames_exact']==118 for c in d['cases'])
        elif name=='water_cross_pose_report.json':assert len(d['cases'])==7 and len(d['unresolved_up_cases'])==1
        elif name.startswith('thrown_axe'):assert len(d['cases'])==16 and all(c['frames_exact']==121 for c in d['cases'])
        elif name.startswith('timing'):assert all(c['differing_state_frames']==0 for c in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        elif name=='fast_ground_cross_improvement.json':assert len(d['cases'])==8 and all(c['source_transition_entry']==c['native_transition_entry_after'] for c in d['cases'])
        elif name.startswith('item_rewards_gameplay'):assert len(d['cases'])==22 and all(c['speed_matches_original'] for c in d['cases']) and any(c['room']==343 and c['speed_after_reward']==1 for c in d['cases'])
        elif name=='item_rewards_save_report.json':assert len(d['cases'])==10 and any(c['running_boots_speed_cold_loaded']==1 for c in d['cases'])
        else:assert len(d['cases'])==8 and d['diagnostic_only']
        reports.append(dict(file=name,sha256=sha(p)))
    paths=['megadrive/src/main.c','megadrive/src/fast_ground_data.c','tools/extract_fast_ground.py','tools/validate_ground_walk.py','tools/validate_fast_ground_cross.py','tools/audit_fast_ground_patch.py','analysis/fast_ground_resources.json','analysis/fast_ground_milestone.md','analysis/fast-ground-baseline-v0093/main.c','analysis/fast-ground-baseline-v0093/save.inc','megadrive/src/save.inc','tools/validate_item_rewards_gameplay.py','tools/validate_item_rewards_save.py']
    result=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),only_declared_fast_normal_ground_selection_and_boots_grant_restore_changes_from_v0093=True,source_files={n:sha(ROOT/n) for n in paths},reports=reports,full_game_ported=False,limits=['Controlled ground movement, reward acquisition and cold-load equipment validated; natural dungeon-to-save route, obstacles, combat and other terrain contexts remain unverified.','Up NTSC transition timing, ground arrival pose/loading phases and software-map staging remain incomplete.','No complete framebuffer/audio, all enemy AI, boss, quest, ending or complete playthrough proof.'])
    (ROOT/'validation/fast_ground_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Fast ground patch audit passed',digest)
if __name__=='__main__':main()
