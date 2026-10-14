"""Bind water-transition pose changes to baseline and current runtime evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535
    assert checksum==int.from_bytes(rom[0x18e:0x190],'big') and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    assert rom[0x1b0:0x1bc]==bytes.fromhex('5241f8200020000100203fff')
    old=json.loads((ROOT/'versions/v0089-1942f987/thrown_axe_patch_audit.json').read_bytes())
    p=ROOT/'analysis/water-cross-baseline-v0089/main.c';base=p.read_text();assert sha(p)==old['source_files']['megadrive/src/main.c']
    previous=json.loads((ROOT/'versions/v0092-602393fc/water_cross_patch_audit.json').read_bytes())
    up_base=ROOT/'analysis/up-scroll-baseline-v0092/main.c'
    assert sha(up_base)==previous['source_files']['megadrive/src/main.c']
    up_current=(ROOT/'megadrive/src/main.c').read_text()
    a=up_current.index('/* 2099..20AC:');b=up_current.index('/* 2C63/369F prepares',a)
    up_current=up_current[:a]+up_current[b:]
    assert up_current.count('        if(transition_direction==0) retain_room_map_swap_work();\n')==2
    up_current=up_current.replace('        if(transition_direction==0) retain_room_map_swap_work();\n','')
    assert up_current.count('SYS_isPAL() && transition_direction==1')==3
    up_current=up_current.replace('SYS_isPAL() && transition_direction==1','SYS_isPAL() && transition_direction<2')
    assert up_current==up_base.read_text(),'Undeclared change from v0092'
    current=(ROOT/'megadrive/src/main.c').read_text()
    current=current.replace('static bool transition_water_pose,transition_pose_prepared;\nstatic u16 hero_pattern_wait_frames;\n','')
    a=current.index('/* 2C63/369F prepares');b=current.index('static void step_room_transition(',a);current=current[:a]+current[b:]
    for start,stop in [('static void update_hero_sprites(void)\n{','/* 1B0E: initial map'),('static void begin_room_transition(void)\n{','/* 6594/65D0:')]:
        a=current.index(start);b=current.index(stop,a);x=base.index(start);y=base.index(stop,x);current=current[:a]+base[x:y]+current[b:]
    current=current.replace('''        if(transition_pose_prepared) transition_pose_prepared=FALSE;
        else prepare_hero_patterns();
        world_previous_input=input;''','''        prepare_hero_patterns();world_previous_input=input;''')
    assert current==base,'Undeclared source changes'
    for name in ['megadrive/src/actors.c','megadrive/src/thrown_axe_data.c']:assert sha(ROOT/name)==old['source_files'][name]
    opening=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    for name,h in opening['unchanged_production_assets'].items():
        if name not in ['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/rom_header.c']:assert sha(ROOT/name)==h
    second=json.loads((ROOT/'versions/v0084-7de7d76b/second_spell_patch_audit.json').read_bytes());assert sha(ROOT/'megadrive/src/second_spell_data.c')==second['source_files']['megadrive/src/second_spell_data.c']
    old80=json.loads((ROOT/'versions/v0080-6aee1373/dialogue_publication_patch_audit.json').read_bytes())
    for name in ['build.ps1','megadrive/src/rom_header.c']:assert sha(ROOT/name)==old80['source_files'][name]
    names=['water_cross_pose_report.json','water_cross_all_diagnostic.json','thrown_axe_report.json','thrown_axe_walk_report.json','thrown_axe_walk_fast_report.json','second_spell_report.json','second_spell_fire_regression_report.json','timing_report.json','timing-pal_report.json'];reports=[]
    for name in names:
        p=ROOT/'validation'/name;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,name
        if name=='water_cross_pose_report.json':assert len(d['cases'])==7 and len(d['unresolved_up_cases'])==1 and d['baseline_removed_hero_pattern_difference_frames']=={'auto':27,'pal':24}
        elif name=='water_cross_all_diagnostic.json':assert d['diagnostic_only'] and len(d['cases'])==8
        elif name.startswith('timing'):assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        else:
            assert len(d['cases'])==(16 if '_walk' in name else 22)
            assert all(c['frames_exact']==121 for c in d['cases']),name
        reports.append(dict(file=name,sha256=sha(p)))
    paths=['megadrive/src/main.c','tools/profile_water_cross.py','tools/validate_water_cross_pose.py','tools/audit_water_cross_patch.py','analysis/water-cross-baseline-v0089/main.c','analysis/water-cross-baseline-v0089/water_cross_diagnostic.json','analysis/water_cross_source_timing.json','analysis/water_cross_pose_milestone.md','analysis/up_scroll_transfer_timing.json','analysis/up_scroll_milestone.md','analysis/up-scroll-baseline-v0092/main.c']
    result=dict(md_sha256=digest,source_sha256=sha(ROOT/'input/original.sms'),md_bytes=len(rom),checksum=hex(checksum),only_declared_pose_preparation_and_transition_changes_from_v0089=True,source_files={name:sha(ROOT/name) for name in paths},reports=reports,full_game_ported=False,limits=['Seven controlled directional pose cases pass; NTSC up still has timing/pose errors. No complete transition equivalence claimed.','Mutable-cell publication is one frame early NTSC and software-map staging differs. Source instruction timing has been profiled but full CPU/VDP transfer timing is incomplete.','Only four hero sprites verified during the seven passing transitions; enemy sprites after arrival, framebuffer and audio remain unverified.','Natural water routes/acquisition/combat, other abilities, full enemies/bosses, quests, ending and complete playthrough remain unfinished.'])
    (ROOT/'validation/water_cross_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Water crossing pose audit passed',digest)
if __name__=='__main__':main()
