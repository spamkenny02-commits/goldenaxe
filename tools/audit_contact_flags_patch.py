"""Bind complete contact-flag translation and bounded regression evidence."""
import hashlib,json
from pathlib import Path
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    assert len(rom)==524288 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    assert int.from_bytes(rom[0x18e:0x190],'big')==sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
    archive=ROOT/'versions/v0049-3e6de542';prior=json.loads((archive/'shutters_patch_audit.json').read_bytes())
    baseline_path=ROOT.parents[1]/'work/shutters-harness/src/game_main.inc'
    baseline=baseline_path.read_bytes();assert sha(baseline)==prior['source_files']['megadrive/src/main.c']
    s=baseline.decode().replace("\r\n","\n")
    s=s.replace('room_script_coordinate,room_script_coordinate_pending;','room_script_coordinate,room_script_coordinate_pending,room_script_direction;')
    s=s.replace('room_script_flags(u16 old_x,u16 old_y)','room_script_flags(u16 old_x,u16 old_y,u16 old_direction)')
    s=s.replace('    u8 flags=0;\n    if(room_script_coordinate_pending) { room_script_coordinate=coordinate;room_script_coordinate_pending=0; }','    u8 flags=(u8)hero_direction;\n    if(input&BUTTON_UP) flags|=4;\n    if(room_script_coordinate_pending) { room_script_coordinate=coordinate;room_script_direction=old_direction;room_script_coordinate_pending=0; }')
    s=s.replace('        room_script_coordinate=coordinate;\n    }\n    return flags;','        room_script_coordinate=coordinate;\n        if(room_script_direction!=hero_direction) flags|=0x40;\n        room_script_direction=hero_direction;\n    }\n    return flags;')
    s=s.replace('u16 old_x=hero_x>>8,old_y=hero_y>>8;','u16 old_x=hero_x>>8,old_y=hero_y>>8,old_direction=hero_direction;')
    s=s.replace('room_script_flags(old_x,old_y);','room_script_flags(old_x,old_y,old_direction);')
    assert s==(ROOT/'megadrive/src/main.c').read_text(),'Unexpected production change'
    for name,expected in prior['source_files'].items():
        if name.startswith('megadrive/src/') and name!='megadrive/src/main.c':assert sha((ROOT/name).read_bytes())==expected,name
    snapshot=ROOT/'analysis/baseline-v0049-main.c'
    if snapshot.exists():assert snapshot.read_bytes()==baseline
    else:snapshot.write_bytes(baseline)
    names=['contact_flags']+[n+suffix for n in ['contact_cache_gameplay','shutters_gameplay','timing'] for suffix in ['', '-pal']]
    reports={};evidence=[]
    for name in names:
        path=ROOT/'validation'/f'{name}_report.json';raw=path.read_bytes();r=json.loads(raw);assert r['md_sha256']==digest,name
        reports[name]=r;evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
    unit=reports['contact_flags'];assert unit['cases_checked']==8192 and unit['two_consecutive_dispatches'] and unit['all_flags_and_cached_coordinate_direction_exact']
    assert unit['stationary_up_gate_covered'] and unit['moving_inside_gate_covered']
    for name,expected in unit['source_copies'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==expected,name
    for suffix in ['', '-pal']:
        r=reports['contact_cache_gameplay'+suffix];assert r['frames_checked']==371 and r['differing_cached_state_frames']==0 and r['controller_only_no_ram_injections']
        cases=reports['shutters_gameplay'+suffix]['cases'];assert len(cases)==10
        for c in cases:
            assert c['before_and_after_state_fields_exact'] and c['timing']['sms']==c['timing']['md']
            if c['occupied']:assert c['closed_reopened'] and c['timing']['md']==dict(closed=3414,opened=3504)
            else:assert c['empty_room_did_not_close'] and c['timing']['md']['closed'] is None
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
        assert reports['timing'+suffix]['enemy']['differing_motion_counter_frames']==0
    files=['megadrive/src/main.c','tools/validate_contact_flags.py','tools/contact_flags_harness.c','tools/contact_flags_cases.inc','tools/build_contact_flags_harness.ps1','tools/validate_contact_cache_gameplay.py','tools/audit_contact_flags_patch.py','analysis/baseline-v0049-main.c']
    report=dict(md_sha256=digest,md_size=len(rom),checksum_aliases_verified=True,current_reports=evidence,source_files={n:sha((ROOT/n).read_bytes()) for n in files},prior_audit_sha256=sha((archive/'shutters_patch_audit.json').read_bytes()),production_delta_exactly_contact_flags=True,prior_room_effect_handlers_unchanged=True,isolated_cases=8192,consecutive_dispatches_per_case=2,live_cache_frames=742,live_shutter_regression_cases=20,full_game_ported=False,limits=['47 inventoried contact-script effects are still not enabled; this patch supplies their correct flag prerequisite.','Current isolated fixtures cover boundary positions, four directions, UP held/released, matching/different cached coordinates and direction, and pending room initialization. They do not establish full progression.','Previous v0049 room-effect unit reports are inherited evidence for unchanged handlers, not reruns of this ROM.','Loading IRQ phase, other puzzles, natural dungeon routes, bosses, ending, full pixels and audio remain incomplete.'])
    (ROOT/'validation/contact_flags_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('7 current reports bound: 8192 flag cases, 742 live cache frames, 20 live shutter cases. Full game remains incomplete.')
if __name__=='__main__':main()
