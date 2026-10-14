"""Bind the source 06D6 post-scroll publication and complete pose durations."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=ROOT/'gaw-megadrive.bin';rom=p.read_bytes();digest=sha(p)
    assert len(rom)==524288 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535
    assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
    old=json.loads((ROOT/'versions/v0070-ee7ae2e4/dialogue_scroll_patch_audit.json').read_bytes())
    base=ROOT/'analysis/dialogue-postscroll-baseline-v0070/main.c'
    assert sha(base)==old['source_files']['megadrive/src/main.c']
    s=(ROOT/'megadrive/src/main.c').read_text()
    delta='    /* 06D6 calls 0786 again before parsing/drawing the next word. */\n    sound_effect(0x9f);upload_dialog_bitmap();\n'
    assert s.count(delta)==1 and s.replace(delta,'')==base.read_text()
    for name,h in old['source_files'].items():
        if name.startswith('megadrive/src/') and name!='megadrive/src/main.c':assert sha(ROOT/name)==h
    prior=json.loads((ROOT/'versions/v0060-b2742e83/item_rewards_report.json').read_bytes())['source_copies']
    for name,h in prior.items():
        if name not in ['main.c','healer.inc']:assert sha(ROOT/'megadrive/src'/name)==h
    source=(ROOT/'input/original.sms').read_bytes()
    assert source[0x6d6:0x6d9]==bytes.fromhex('cd8607')
    names=['dialogue_scroll_report.json','final_dialogue_report.json','house_dialogue_report.json','timing_report.json','timing-pal_report.json']
    reports=[]
    for name in names:
        path=ROOT/'validation'/name;d=json.loads(path.read_bytes());assert d['md_sha256']==digest,name
        if name=='dialogue_scroll_report.json':assert len(d['cases'])==2 and all(x['complete_pose_frame_lists_exact'] and x['all_pattern_pixel_colors_verified'] for x in d['cases'])
        elif name=='final_dialogue_report.json':assert len(d['cases'])==12 and all(x['stable_final_marker_exact'] for x in d['cases'])
        elif name=='house_dialogue_report.json':assert len(d['cases'])==6 and d['natural_walk_conversation_and_restore_verified']
        else:assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        reports.append(dict(file=name,sha256=sha(path)))
    diagnostic=ROOT/'validation/opening_latency_v0071.json';d=json.loads(diagnostic.read_bytes());assert d['md_sha256']==digest and d['diagnostic_only']
    for case in d['cases']:
        assert sha(ROOT/'validation'/case['profile'])==case['profile_sha256']
    paths=['megadrive/src/main.c','tools/validate_dialogue_scroll.py','tools/profile_world_clock.py','tools/audit_postscroll_patch.py','analysis/dialogue-postscroll-baseline-v0070/main.c']
    result=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),checksum=hex(checksum),aliases_verified=True,exact_v0070_restored_by_removing_single_postscroll_upload=True,source_files={name:sha(ROOT/name) for name in paths},reports=reports,diagnostic=dict(file=diagnostic.name,sha256=sha(diagnostic)),full_game_ported=False,limits=['Only complete bitmap poses of the first natural opening scroll have equal frame lists; partial transfer frames and subsequent words are unproven.','Before-first-page and initial loading timing still differ; diagnostic attached separately.','Merchant/save/free-night checks remain evidence from v0070 and were not rerun on this change.','Global clock reset, natural full progression, all abilities, quests, full enemy/boss behavior and ending remain unfinished.'])
    (ROOT/'validation/postscroll_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Post-scroll patch audit passed:',digest)

if __name__=='__main__':main()
