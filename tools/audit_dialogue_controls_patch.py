"""Bind text-control fixes and direct original-renderer fixture comparisons."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535
    assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
    assert int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    old=json.loads((ROOT/'versions/v0080-6aee1373/dialogue_publication_patch_audit.json').read_bytes())
    path=ROOT/'analysis/dialogue-controls-baseline-v0080/main.c';base=path.read_text();assert sha(path)==old['source_files']['megadrive/src/main.c']
    current=(ROOT/'megadrive/src/main.c').read_text()
    for start,stop in [('static u16 dialog_glyph(', 'static void upload_dialog_bitmap('),('static void render_dialogue_text(', 'static void show_dialogue_text(')]:
        a=current.index(start);b=current.index(stop,a);x=base.index(start);y=base.index(stop,x)
        current=current[:a]+base[x:y]+current[b:]
    assert current==base
    for name in ['megadrive/src/rom_header.c','build.ps1']:assert sha(ROOT/name)==old['source_files'][name]
    assets=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())['unchanged_production_assets']
    for name,h in assets.items():
        if name!='megadrive/src/rom_header.c':assert sha(ROOT/name)==h
    baseline=ROOT/'analysis/dialogue-controls-baseline-v0080/dialogue_controls_baseline_report.json';b=json.loads(baseline.read_bytes());assert b['md_sha256']==old['md_sha256'] and b['baseline_diagnostic']
    controls=json.loads((ROOT/'validation/dialogue_controls_report.json').read_bytes())
    assert controls['md_sha256']==digest and controls['test_rom_text_resources_modified'] and controls['production_roms_unmodified']
    assert len(controls['cases'])==26 and all(x['passed'] for x in controls['cases'])
    key=lambda x:(x['region'],x['text_hex'],str(x['argument_hex']))
    previous={key(x):x for x in b['cases']};improved=[x['name']+':'+x['region'] for x in controls['cases'] if key(x) in previous and not previous[key(x)]['passed']]
    assert len(improved)==16
    source=(ROOT/'input/original.sms').read_bytes()
    assert source[0x631:0x639]==bytes.fromhex('3ac6dcee0132c6dc')
    assert source[0x76b:0x771]==bytes.fromhex('cdee07c3a105')
    names=['dialogue_controls_report.json','dialogue_scroll_report.json','final_dialogue_report.json','house_dialogue_report.json','all_merchants_report.json','timing_report.json','timing-pal_report.json','dialogue_publications_report.json','dialogue_preparation_profile.json','dialogue_preparation-pal_profile.json','world_clock_profile.json','world_clock-pal_profile.json']
    reports=[]
    for name in names:
        p=ROOT/'validation'/name;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,name
        if name=='dialogue_scroll_report.json':assert all(x['complete_pose_frame_lists_exact'] and x['all_pattern_pixel_colors_verified'] for x in d['cases'])
        elif name=='final_dialogue_report.json':assert len(d['cases'])==12 and all(x['stable_final_marker_exact'] for x in d['cases'])
        elif name=='house_dialogue_report.json':assert len(d['cases'])==6 and d['natural_walk_conversation_and_restore_verified']
        elif name=='all_merchants_report.json':assert len(d['cases'])==43 and d['all_23_towns_checked']
        elif name.startswith('timing'):assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        elif name=='dialogue_publications_report.json':assert all(x['all_complete_source_bitmaps_present_in_order'] for x in d['cases'])
        reports.append(dict(file=name,sha256=sha(p)))
    paths=['megadrive/src/main.c','tools/validate_dialogue_controls.py','tools/audit_dialogue_controls_patch.py','analysis/dialogue-controls-baseline-v0080/main.c','analysis/dialogue-controls-baseline-v0080/dialogue_controls_baseline_report.json']
    result=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),md_bytes=len(rom),checksum=hex(checksum),aliases_header_and_prior_assets_verified=True,exact_v0080_restored_by_replacing_only_glyph_lookup_and_renderer=True,source_files={name:sha(ROOT/name) for name in paths},reports=reports,original_renderer_fixture_cases=26,formerly_failing_identical_fixtures_now_passing=improved,full_game_ported=False,limits=['Fixture ROM copies replace only opening text and native checksum; controlled argument RAM writes are explicit. These are not natural game progression tests.','Stable bitmap/control continuation equality, not exact timing, marker, palette, partial word clearing or audio.','First-page waits remain 9 frames late NTSC / 10 PAL; initial room remains 33/31 early.','Save/free-healer evidence remains v0080 and was not rerun for this change.','Global clock reset, full parameter streams and renderer edge cases, full enemy/boss behavior, abilities, quests, ending and a natural complete playthrough remain unfinished.'])
    (ROOT/'validation/dialogue_controls_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Dialogue control audit passed:',digest)

if __name__=='__main__':main()
