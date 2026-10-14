"""Bind the opening prelude delta, actual palette/font checks and regressions."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==524288 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535
    assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
    baseline=ROOT/'analysis/opening-setup-baseline-v0071/main.c'
    previous=json.loads((ROOT/'versions/v0071-b3613817/postscroll_patch_audit.json').read_bytes())
    assert sha(baseline)==previous['source_files']['megadrive/src/main.c']
    current=(ROOT/'megadrive/src/main.c').read_text()
    start=current.index('/* 0AD1/0B92: prepared opening colors become visible on the next IRQ. */')
    stop=current.index('extern const u8 house_npc_text',start)
    restored=current[:start]+'static void opening_dialogue(void)\n{\n    show_dialogue_text(opening_text,FALSE);enter_initial_room();\n}\n\n'+current[stop:]
    wrapped='    if(overlay)\n    {\n        decode_planes(number_font_rle,sms_vram+0x1e00,4);\n        convert_patterns_range(240,16);\n        VDP_loadTileData(md_patterns+240*8,16+240,16,CPU);\n    }'
    original='    decode_planes(number_font_rle,sms_vram+0x1e00,4);\n    convert_patterns_range(240,16);\n    VDP_loadTileData(md_patterns+240*8,16+240,16,CPU);'
    assert restored.count(wrapped)==1
    restored=restored.replace(wrapped,original)
    assert restored==baseline.read_text()
    old=json.loads((ROOT/'versions/v0070-ee7ae2e4/dialogue_scroll_patch_audit.json').read_bytes())
    unchanged={name:h for name,h in old['source_files'].items() if name.startswith('megadrive/src/') and name!='megadrive/src/main.c'}
    prior=json.loads((ROOT/'versions/v0060-b2742e83/item_rewards_report.json').read_bytes())['source_copies']
    unchanged.update({'megadrive/src/'+name:h for name,h in prior.items() if name not in ['main.c','healer.inc']})
    dungeon=json.loads((ROOT/'versions/v0063-62366fff/dungeon_bitmaps_patch_audit.json').read_bytes())
    unchanged['megadrive/src/dungeon_animation_data.c']=dungeon['source_files']['megadrive/src/dungeon_animation_data.c']
    for name,h in unchanged.items():assert sha(ROOT/name)==h,name
    source=(ROOT/'input/original.sms').read_bytes()
    assert source[0x1197:0x11ab]==bytes.fromhex('cd480b cdeb1d 214ca7 11005e 3e04 cd2703 cda40a')
    names=['opening_setup_report.json','opening_setup_profile.json','opening_setup-pal_profile.json','dialogue_scroll_report.json','final_dialogue_report.json','house_dialogue_report.json','timing_report.json','timing-pal_report.json']
    reports=[]
    for name in names:
        path=ROOT/'validation'/name;d=json.loads(path.read_bytes());assert d['md_sha256']==digest,name
        if name=='opening_setup_report.json':assert len(d['cases'])==2 and all(x['story_entry_exact'] and x['palette_entries_0_to_30_cram_words_exact']==1271 and x['font_source_tstates']==70986 for x in d['cases'])
        elif name=='dialogue_scroll_report.json':assert len(d['cases'])==2 and all(x['complete_pose_frame_lists_exact'] and x['all_pattern_pixel_colors_verified'] for x in d['cases'])
        elif name=='final_dialogue_report.json':assert len(d['cases'])==12 and all(x['stable_final_marker_exact'] for x in d['cases'])
        elif name=='house_dialogue_report.json':assert len(d['cases'])==6 and d['natural_walk_conversation_and_restore_verified']
        elif name.startswith('timing'):assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        reports.append(dict(file=name,sha256=sha(path)))
    cases=[]
    for suffix in ['', '-pal']:
        path=ROOT/f'validation/world_clock{suffix}_profile.json';d=json.loads(path.read_bytes());assert d['md_sha256']==digest and not d['ram_injections']
        story=next(x for x in d['source_events'] if x['pc']==0x7444);native=next(x for x in d['native_events'] if x['function']=='render_dialogue_text')
        page=next(x for x in d['source_events'] if x['pc']==0x07f4);wait=next(x for x in d['native_events'] if x['function']=='wait_dialog_continue')
        room={tag:next(x for x in rows if x['frame']>2400 and x['state']==12 and x['room']==149) for tag,rows in d['traces'].items()}
        cases.append(dict(region=d['region'],source_story_entry=story,native_render_entry=native,story_entry_delta=native['frame']-story['frame'],source_page_wait=page,native_page_wait=wait,page_wait_delta=wait['frame']-page['frame'],first_room=room,room_ready_delta=room['md']['frame']-room['sms']['frame'],profile=path.name,profile_sha256=sha(path)))
        reports.append(dict(file=path.name,sha256=sha(path)))
    diagnostic=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),diagnostic_only=True,production_roms_unmodified=True,ram_injections=False,cases=cases,limits=['One natural scripted name/new-game sequence per region.','Page and room discrepancies are diagnostic, not passing fidelity checks.'])
    path=ROOT/'validation/opening_latency_v0076.json';path.write_text(json.dumps(diagnostic,indent=2)+'\n');reports.append(dict(file=path.name,sha256=sha(path)))
    paths=['megadrive/src/main.c','tools/profile_opening_setup.py','tools/validate_opening_setup.py','tools/profile_world_clock.py','tools/audit_opening_setup_patch.py','analysis/opening-setup-baseline-v0071/main.c']
    result=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),checksum=hex(checksum),aliases_verified=True,exact_v0071_restored_by_reverting_opening_prelude_and_font_location=True,source_files={name:sha(ROOT/name) for name in paths},unchanged_production_assets=unchanged,reports=reports,full_game_ported=False,limits=['Palette 31 still has global-clock phase differences.','First page and initial-room timing, whole-dialogue pixels and audio fidelity remain unproven or different.','Merchant, save and free-night checks were not rerun; evidence remains v0070.','Natural complete progression, all abilities, quests, full enemy/boss behavior and ending remain unfinished.'])
    (ROOT/'validation/opening_setup_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Opening patch audit passed:',digest)
    print([(x['region'],x['story_entry_delta'],x['page_wait_delta'],x['room_ready_delta']) for x in cases])

if __name__=='__main__':main()
