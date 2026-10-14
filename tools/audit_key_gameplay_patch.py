"""Bind live controller and save persistence evidence to the unchanged v0042 ROM."""
import hashlib,json
from run_core import ROOT


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    evidence=[];reports={};offsets=[]
    names=['key_door_save']+[stem+suffix for stem in ['key_door_gameplay','key_door_continue'] for suffix in ['', '-pal']]
    for stem in names:
        name=stem+'_report.json';raw=(ROOT/'validation'/name).read_bytes();report=json.loads(raw)
        assert report['md_sha256']==digest,name
        reports[stem]=report;evidence.append(dict(file=name,sha256=sha(raw)))
    for stem in ['key_door_gameplay','key_door_continue']:
        for suffix in ['', '-pal']:
            report=reports[stem+suffix]
            assert report['production_cartridges_unmodified'] and report['controller_opening_crossing_and_return']
            assert len(report['cases'])==9
            for case in report['cases']:
                assert case['settled_crossing_return_fields_source_exact']
                assert case['keys_after_repeated_contacts']=={'ordinary':1,'master':5,'empty':0}[case['inventory']]
                if stem=='key_door_continue':assert case['death_continue_persistence_verified']
                if case['inventory']!='empty':
                    assert case['opened_crossed_returned']
                    assert case['timing']['md']['opening']==case['timing']['sms']['opening']
                    if stem=='key_door_gameplay':offsets.append(case['timing']['md']['reached']-case['timing']['sms']['reached'])
                else:assert case['empty_inventory_refused']
    saved=reports['key_door_save']
    assert len(saved['cases'])==2 and saved['production_save_and_cold_load_by_normal_input']
    assert all(c['save_payload_bytes_exact']==592 and c['persistent_room_flag_bytes_cold_loaded']==256 for c in saved['cases'])
    source_files=['tools/validate_key_door_gameplay.py','tools/validate_key_door_save.py','tools/audit_key_gameplay_patch.py','megadrive/src/main.c']
    provenance=[]
    for tag in ['sms','md']:
        for inventory in ['ordinary','master']:
            name=f'validation/{tag}-key-gameplay-right-{inventory}/ram_03750.bin'
            provenance.append(dict(file=name,sha256=sha((ROOT/name).read_bytes())))
    report=dict(md_sha256=digest,production_rom_unchanged=True,controller_cases_pal_ntsc=18,
                death_continue_cases_pal_ntsc=18,save_and_cold_load_cases=2,
                opening_decision_frame_source_exact=True,
                first_crossing_resume_offset_frames_min=min(offsets),first_crossing_resume_offset_frames_max=max(offsets),
                current_targeted_reports=evidence,save_state_provenance=provenance,
                source_files={name:sha((ROOT/name).read_bytes()) for name in source_files},
                full_game_ported=False,full_natural_dungeon_progression_verified=False,
                limits=['Starting room/map/position/inventory are controlled; routes to these rooms are not verified.',
                        'Save tests transfer controller-generated door state to the save-point route; uninterrupted travel there is unverified.',
                        'Redraw/transition duration remains faster on MD by 3..8 frames at the first tested crossing.',
                        'Other puzzle scripts, room-clear triggers, remaining enemies, bosses and ending remain incomplete.'])
    (ROOT/'validation/key_gameplay_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('18 live controller cases, 18 death/Continue cases and two cold-load cases bound to v0042.')


if __name__=='__main__':main()
