"""Bind general arrival preparation to v0097 and current runtime comparisons."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    assert sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535==int.from_bytes(rom[0x18e:0x190],'big')
    prior=json.loads((ROOT/'versions/v0097-51363105/house_patterns_patch_audit.json').read_bytes())
    p=ROOT/'analysis/arrival-pose-baseline-v0097/main.c';assert sha(p)==prior['source_files']['megadrive/src/main.c']
    s=p.read_text().replace('static bool transition_water_pose,transition_pose_prepared;','static bool transition_pose_prepared;').replace('transition_water_pose=hero_terrain_context==3;transition_pose_prepared=FALSE;','transition_pose_prepared=FALSE;').replace('prepare_water_arrival_pose','prepare_arrival_pose')
    s=s.replace('    hero_animation=0;prepare_hero_patterns();transition_pose_prepared=TRUE;','    hero_state=0;hero_flags=3;hero_animation=0;prepare_hero_patterns();transition_pose_prepared=TRUE;')
    s=s.replace('if(transition_water_pose && transition_direction==3','if(transition_direction==3').replace('{ hero_animation=0;transition_pose_prepared=TRUE; }','{ hero_state=0;hero_flags=3;hero_animation=0;transition_pose_prepared=TRUE; }')
    s=s.replace('            if(transition_water_pose)\n            {\n                prepare_arrival_pose();\n                if(SYS_isPAL() && transition_direction==1) { transition_stage=6;return; }\n            }','            prepare_arrival_pose();\n            if(SYS_isPAL() && transition_direction==1) { transition_stage=6;return; }')
    s=s.replace('hero_scroll_x=hero_scroll_y=0;if(!transition_water_pose) hero_animation=0;','hero_scroll_x=hero_scroll_y=0;').replace('if(transition_water_pose && transition_stage!=4)','if(transition_stage!=4)')
    s=s.replace('if(SYS_isPAL() && transition_direction==1) hero_pattern_wait_frames=1;','if(SYS_isPAL() && transition_direction==1 && hero_patterns_pending) hero_pattern_wait_frames=1;').replace('if(SYS_isPAL() && transition_direction==1) { transition_stage=6;return; }','if(hero_pattern_wait_frames) { transition_stage=6;return; }').replace('if(SYS_isPAL() && transition_direction==1) { transition_stage=6;game_state=10; }','if(hero_pattern_wait_frames) { transition_stage=6;game_state=10; }')
    assert s==(ROOT/'megadrive/src/main.c').read_text(),'Undeclared source changes'
    old=json.loads((ROOT/'versions/v0095-f2f9fdc1/fast_ground_patch_audit.json').read_bytes())
    for n,h in old['source_files'].items():
        if n.startswith('megadrive/') and n!='megadrive/src/main.c':assert sha(ROOT/n)==h,n
    opening=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    for n,h in opening['unchanged_production_assets'].items():
        if n not in ['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/rom_header.c','megadrive/src/save.inc']:assert sha(ROOT/n)==h,n
    reports=[]
    for n in ['arrival_pose_report.json','ground_cross_all_diagnostic.json','water_cross_all_diagnostic.json','timing_report.json','timing-pal_report.json']:
        p=ROOT/'validation'/n;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,n
        if n=='arrival_pose_report.json':assert len(d['cases'])==14 and len(d['unresolved_up_ntsc'])==2 and all(c['pose_and_state_frames_exact']==151 for c in d['cases'])
        elif n.startswith('timing'):assert all(c['differing_state_frames']==0 for c in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        else:assert len(d['cases'])==8 and d['diagnostic_only']
        reports.append(dict(file=n,sha256=sha(p)))
    names=['megadrive/src/main.c','tools/profile_water_cross.py','tools/validate_arrival_pose.py','tools/audit_arrival_pose_patch.py','analysis/arrival_pose_milestone.md','analysis/arrival-pose-baseline-v0097/main.c','analysis/arrival-pose-baseline-v0097/ground_cross_all_diagnostic.json','analysis/arrival-pose-baseline-v0097/water_cross_all_diagnostic.json']
    result=dict(md_sha256=digest,source_sha256=sha(ROOT/'input/original.sms'),only_declared_arrival_preparation_changes_from_v0097=True,source_files={n:sha(ROOT/n) for n in names},reports=reports,full_game_ported=False,limits=['14 controlled cases pass; two NTSC upward cases remain wrong. Ground upward resumed-state difference increases from one frame to two while pattern preparation improves.','Ordinary PAL/NTSC timing checks pass; this is not all terrain, all scrolling workloads, complete framebuffer/audio or complete game proof.'])
    (ROOT/'validation/arrival_pose_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Arrival pose patch audit passed',digest)
if __name__=='__main__':main()
