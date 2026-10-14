"""Bind the v0080 dialogue publication delta, 1 MiB header and regressions."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    assert int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    assert rom[0x1b0:0x1bc]==bytes.fromhex('5241f8200020000100203fff')
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535
    assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
    original_header=bytearray((ROOT/'versions/v0076-a171c534/gaw-megadrive-v0076.bin').read_bytes()[0x100:0x200])
    current_header=bytearray(rom[0x100:0x200])
    for header in [original_header,current_header]:
        header[0x8e:0x90]=bytes(2);header[0xa4:0xa8]=bytes(4)
    assert original_header==current_header
    old=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    path=ROOT/'analysis/dialogue-publication-baseline-v0076/main.c';base=path.read_text();assert sha(path)==old['source_files']['megadrive/src/main.c']
    current=(ROOT/'megadrive/src/main.c').read_text()
    start=current.index('/* 0786 publication boundary. Native transfer/IRQ ordering remains to align. */')
    end=current.index('static void show_dialogue_text(',start)
    bstart=base.index('static void render_dialogue_text(');bend=base.index('static void show_dialogue_text(',bstart)
    assert current[:start]+base[bstart:bend]+current[end:]==base
    for name,h in old['unchanged_production_assets'].items():
        if name!='megadrive/src/rom_header.c':assert sha(ROOT/name)==h,name
    source=(ROOT/'input/original.sms').read_bytes()
    assert source[0xca54:0xca5e]==bytes.fromhex('a1a4a5212b2c2d2e2f3f')
    names=['dialogue_publications_report.json','dialogue_preparation_profile.json','dialogue_preparation-pal_profile.json','opening_setup_report.json','opening_setup_profile.json','opening_setup-pal_profile.json','dialogue_scroll_report.json','final_dialogue_report.json','house_dialogue_report.json','all_merchants_report.json','healer_report.json','healer-pal_report.json','save_report.json','timing_report.json','timing-pal_report.json','world_clock_profile.json','world_clock-pal_profile.json']
    reports=[]
    for name in names:
        p=ROOT/'validation'/name;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,name
        if name=='dialogue_publications_report.json':assert len(d['cases'])==2 and all(x['all_complete_source_bitmaps_present_in_order'] and x['name_only_pose_missing_in_v0076_and_present_now'] for x in d['cases'])
        elif name=='dialogue_scroll_report.json':assert len(d['cases'])==2 and all(x['complete_pose_frame_lists_exact'] and x['all_pattern_pixel_colors_verified'] for x in d['cases'])
        elif name=='final_dialogue_report.json':assert len(d['cases'])==12 and all(x['stable_final_marker_exact'] for x in d['cases'])
        elif name=='house_dialogue_report.json':assert len(d['cases'])==6 and d['natural_walk_conversation_and_restore_verified']
        elif name=='all_merchants_report.json':assert len(d['cases'])==43 and d['all_23_towns_checked']
        elif name.startswith('healer'):assert len(d['cases'])==5
        elif name=='save_report.json':assert len(d['cases'])==3 and d['death_continue_saved_checkpoint_verified'] and d['occupied_slot_overwrite_verified']
        elif name.startswith('timing'):assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        elif name=='opening_setup_report.json':assert len(d['cases'])==2 and all(x['story_entry_exact'] and x['palette_entries_0_to_30_cram_words_exact']==1271 for x in d['cases'])
        reports.append(dict(file=name,sha256=sha(p)))
    paths=['megadrive/src/main.c','megadrive/src/rom_header.c','build.ps1','tools/profile_dialogue_preparation.py','tools/validate_dialogue_publications.py','tools/audit_dialogue_publication_patch.py','analysis/dialogue-publication-baseline-v0076/main.c']
    result=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),checksum=hex(checksum),md_bytes=len(rom),aliases_and_header_verified=True,sram_header_unchanged=True,exact_v0076_main_restored_by_replacing_renderer_and_removing_publication_helper=True,source_files={name:sha(ROOT/name) for name in paths},reports=reports,full_game_ported=False,limits=['Complete first-page bitmap shapes/order verified, not equal publication dwell times or complete framebuffers.','First-page wait is nine frames late in the measured PAL/NTSC sequence; first room remains 33/31 frames early.','Source IRQ-before-transfer ordering is not reproduced by the native publication helper.','Palette 31 phase, text case/control/substitution edge cases, natural full progression, all abilities, quests, full enemy/boss behavior, ending and audio waveform fidelity remain incomplete or unproven.'])
    (ROOT/'validation/dialogue_publication_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Dialogue publication audit passed:',digest)

if __name__=='__main__':main()
