"""Bind contact-effect translation to original scripts and production evidence."""
import hashlib,json
from actor_reference import ROOT
from extract_contact_scripts import extract
from extract_room_clear import extract as passages,extract_rewards,extract_completions,extract_shutters

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    assert len(rom)==524288 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    assert int.from_bytes(rom[0x18e:0x190],'big')==sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
    original=(ROOT/'input/original.sms').read_bytes();contacts=[r for r in extract(original) if r['target']!=0x5cfb];assert len(contacts)==11
    reference=json.loads((ROOT/'analysis/contact_script_reference.json').read_bytes());assert reference['records']==extract(original)
    lines=['/* Source 5C96 / 5CC7 / 5CEC contact scripts. */','static const u16 world_room_contacts[11][5] = {']
    for r in contacts:
        a=r['explicit_registers'];kind={0x5c96:1,0x5cc7:2,0x5cec:3}[r['target']]
        values=[r['room'],kind,r.get('coordinate',0x168 if kind==2 else 0),a.get('e',a.get('c',0)),a.get('d',0)]
        lines.append('    {'+','.join(str(v) for v in values)+'},')
        for suffix in passages(original)+extract_rewards(original)+extract_completions(original)+extract_shutters(original):
            if suffix['room']==r['room']:assert r['call_site']<suffix['call_site'],r
    lines.append('};');assert (ROOT/'megadrive/src/room_contact.inc').read_text()=='\n'.join(lines)+'\n'
    prior_path=ROOT/'versions/v0050-12d69d55/contact_flags_patch_audit.json';prior=json.loads(prior_path.read_bytes())
    prior_copies=json.loads((prior_path.parent/'contact_flags_report.json').read_bytes())['source_copies']
    for name,expected in prior_copies.items():
        if name!='main.c':assert sha((ROOT/'megadrive/src'/name).read_bytes())==expected,name
    baseline=(ROOT.parents[1]/'work/contact-flags-harness/src/game_main.inc').read_bytes();assert sha(baseline)==prior['source_files']['megadrive/src/main.c']
    current=(ROOT/'megadrive/src/main.c').read_text();start=current.index('/* 5C96 marks passages in the specified room;');end=current.index('/* 6AA5..6AEA: four-cell dungeon floor scan',start)
    restored=(current[:start]+current[end:]).replace('#include "room_contact.inc"\n','').replace('check_dungeon_key_door();check_room_contact(script_flags);','check_dungeon_key_door();')
    assert restored==baseline.decode().replace('\r\n','\n'),'Unexpected production delta'
    snapshot=ROOT/'analysis/baseline-v0050-main.c'
    if snapshot.exists():assert snapshot.read_bytes()==baseline
    else:snapshot.write_bytes(baseline)
    names=['contacts']+[n+s for n in ['contacts_gameplay','shutters_gameplay','key_door_gameplay','timing'] for s in ['', '-pal']]
    reports={};evidence=[]
    for name in names:
        path=ROOT/'validation'/f'{name}_report.json';raw=path.read_bytes();r=json.loads(raw);assert r['md_sha256']==digest,name
        reports[name]=r;evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
    unit=reports['contacts'];assert unit['cases_checked']==8192 and unit['contact_prefix_suffix_state_and_direction_exact'] and unit['repeated_dispatch_verified']
    assert unit['source_cells_maps_all_room_flags_and_key_count_exact'] and unit['loot_allocation_and_preserved_record_bytes_exact']
    assert unit['source_opened_cases']==90 and unit['source_key_consumption_cases']==0
    for name,expected in unit['source_copies'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==expected,name
    for suffix in ['', '-pal']:
        cases=reports['contacts_gameplay'+suffix]['cases'];assert len(cases)==22
        assert {c['room'] for c in cases}=={r['room'] for r in contacts}
        for c in cases:
            assert c['settled_cells_maps_flags_loot_counter_keys_exact'] and c['trigger_timing_exact']
            expected=3400 if c['already_triggered'] else (3414 if suffix else 3415) if c['room']==0x173 else 3410
            assert c['trigger_frame']==expected,(suffix,c)
        cases=reports['shutters_gameplay'+suffix]['cases'];assert len(cases)==10
        for c in cases:
            assert c['before_and_after_state_fields_exact'] and c['timing']['sms']==c['timing']['md']
            if c['occupied']:assert c['closed_reopened'] and c['timing']['md']==dict(closed=3414,opened=3504)
            else:assert c['empty_room_did_not_close']
        cases=reports['key_door_gameplay'+suffix]['cases'];assert len(cases)==9 and all(c['settled_crossing_return_fields_source_exact'] for c in cases)
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
        assert reports['timing'+suffix]['enemy']['differing_motion_counter_frames']==0
    files=['megadrive/src/main.c','megadrive/src/room_contact.inc','tools/extract_contact_scripts.py','tools/validate_room_cells.py','tools/contacts_harness.c','tools/validate_contacts.py','tools/build_contacts_harness.ps1','tools/validate_contacts_gameplay.py','tools/audit_contacts_patch.py','analysis/baseline-v0050-main.c']
    report=dict(md_sha256=digest,md_size=len(rom),checksum_aliases_verified=True,current_reports=evidence,source_files={n:sha((ROOT/n).read_bytes()) for n in files},prior_contact_flag_audit_sha256=sha(prior_path.read_bytes()),production_delta_confined_to_contact_effects=True,source_prefix_before_suffix_order_verified=True,stationary_passage_handlers=7,cell_marker_handlers=1,empty_cell_handlers=3,isolated_cases=8192,live_contact_cases=44,live_shutter_regression_cases=20,live_key_regression_cases=18,full_game_ported=False,limits=['Live fixtures initialize rooms, hero and a frozen actor after a real dungeon entrance. Only stationary-UP triggers use natural controller input; empty cells are injected with their map change.','Full natural block destruction, fights, travel and persistence through an uninterrupted dungeon route are unverified.','36 internal portals, other contact routines, true movable blocks, bosses, quests and ending remain incomplete.','Original map/flag/record bytes and bounded trigger timing are compared; full pixels, sprite priority, audio waveforms and generic IRQ phase are not proven.'])
    (ROOT/'validation/contacts_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('9 current reports bound: 11 contact handlers, 8192 isolated cases, 44 live contacts, 38 live door regressions.')
if __name__=='__main__':main()
