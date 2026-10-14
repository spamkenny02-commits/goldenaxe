"""Bind native clear rewards, persistent keys and source comparison evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom);assert len(rom)==524288
    assert int.from_bytes(rom[0x18e:0x190],'big')==sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535
    assert int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
    from extract_room_clear import extract,extract_rewards,extract_completions,extract_shutters
    original=(ROOT/'input/original.sms').read_bytes();passages=extract(original);rewards=extract_rewards(original)
    assert len(passages)==49 and len(rewards)==20 and sum(r['room']<256 for r in rewards)==9
    reference=json.loads((ROOT/'analysis/room_clear_reference.json').read_bytes());assert reference['records']==passages+rewards+extract_completions(original)
    shutters=extract_shutters(original);assert len(shutters)==13 and reference['shutters']==shutters
    assert len(reference['records'])==96 and len({x['room'] for x in reference['records']+shutters})==97
    names=['room_clear','shutters','key_doors','clear_rewards_save']+[n+s for n in ['shutters_gameplay','clear_rewards_gameplay','room_clear_gameplay','key_door_gameplay','timing'] for s in ['', '-pal']]
    reports={};evidence=[]
    for name in names:
        path=ROOT/'validation'/f'{name}_report.json';raw=path.read_bytes();r=json.loads(raw);assert r['md_sha256']==digest,name
        reports[name]=r;evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
    for name in ['room_clear','shutters','key_doors']:
        assert reports[name]['cases_checked']==8192
        for file,expected in reports[name]['source_copies'].items():assert sha((ROOT/'megadrive/src'/file).read_bytes())==expected,file
    assert reports['room_clear']['loot_allocation_and_preserved_record_bytes_exact'] and reports['room_clear']['repeated_dispatch_verified']
    assert reports['key_doors']['source_opened_cases']==180 and reports['key_doors']['source_key_consumption_cases']==120
    assert reports['shutters']['shutter_close_reopen_state_and_direction_exact']
    assert reports['shutters']['repeated_dispatch_verified']
    for suffix in ['', '-pal']:
        cases=reports['shutters_gameplay'+suffix]['cases'];assert len(cases)==10
        assert all(c['before_and_after_state_fields_exact'] for c in cases)
        for c in cases:
            assert c['timing']['sms']==c['timing']['md']
            if c['occupied']:
                assert c['closed_reopened'] and c['timing']['md']==dict(closed=3414,opened=3504)
            else:assert c['empty_room_did_not_close'] and c['timing']['md']['closed'] is None
        assert sum(c['reward_key'] for c in cases)==2
        cases=reports['clear_rewards_gameplay'+suffix]['cases'];assert len(cases)==16 and all(c['settled_cells_maps_flags_loot_counter_keys_exact'] for c in cases)
        assert sum(c['already_rewarded'] for c in cases)==3
        assert sum(c['key_persists_past_normal_loot_expiry'] for c in cases)==1
        for room in [0x113,0x131]:
            for keys in [2,98,99,255]:
                c=next(c for c in cases if c['room']==room and c['initial_keys']==keys and not c['already_rewarded'] and c['pickup'])
                assert c['expected_keys']==(keys+1 if keys<99 else keys)
        assert len(reports['room_clear_gameplay'+suffix]['cases'])==6 and all(c['settled_cells_exact'] and c['settled_map_exact'] and c['settled_flags_count_keys_exact'] for c in reports['room_clear_gameplay'+suffix]['cases'])
        assert len(reports['key_door_gameplay'+suffix]['cases'])==9 and all(c['settled_crossing_return_fields_source_exact'] for c in reports['key_door_gameplay'+suffix]['cases'])
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
        assert reports['timing'+suffix]['enemy']['differing_motion_counter_frames']==0
    assert len(reports['clear_rewards_save']['cases'])==2 and all(c['keys_cold_loaded']==3 and c['save_payload_bytes_exact']==592 and c['persistent_room_flag_bytes_cold_loaded']==256 for c in reports['clear_rewards_save']['cases'])
    files=['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/actors.h','megadrive/src/room_clear.inc','tools/extract_room_clear.py','tools/validate_room_cells.py','tools/room_clear_harness.c','tools/validate_room_clear.py','tools/validate_clear_rewards_gameplay.py','tools/validate_clear_rewards_save.py','tools/shutters_harness.c','tools/validate_shutters.py','tools/validate_shutters_gameplay.py','tools/audit_shutters_patch.py']
    report=dict(md_sha256=digest,md_size=len(rom),checksum_and_aliases_verified=True,current_reports=evidence,room_clear_handlers=96,new_completion_handlers=27,shutter_handlers=13,distinct_script_rooms=97,live_shutter_cases=20,isolated_clear_shutter_and_key_cases=24576,live_reward_cases=32,live_clear_regression_cases=12,live_key_regression_cases=18,cold_load_cases=2,source_files={name:sha((ROOT/name).read_bytes()) for name in files},full_game_ported=False,limits=['Full natural enemy fights, exterior routes and dungeon progression are not verified by controlled fixtures.','True block pushing, contact prefixes such as 5C96 and room 174 portal 5CFB remain unported; bosses, quests and ending remain incomplete.','Room 131 collection starts at reward centre; only room 113 pickup uses a tested walking path.','Save fixtures transfer earned state to the village save route; uninterrupted travel to that save point is unverified.','Approximate redraw/loading timing, sprite priority/flicker, full scene pixels and audio waveforms remain unresolved.'])
    (ROOT/'validation/shutters_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('14 reports bound: 96 clear handlers, 13 shutters, 24576 isolated cases, 20 live shutter cases, two cold reloads. Full game remains incomplete.')
if __name__=='__main__':main()
