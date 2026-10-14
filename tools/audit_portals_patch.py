"""Bind native internal portals, exact visible wipes and bounded load timing."""
import hashlib,json
from actor_reference import ROOT
from extract_contact_scripts import extract
from extract_room_clear import extract as clear,extract_rewards,extract_completions

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    assert len(rom)==524288 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    assert int.from_bytes(rom[0x18e:0x190],'big')==sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
    original=(ROOT/'input/original.sms').read_bytes();portals=[r for r in extract(original) if r['target']==0x5cfb];assert len(portals)==36
    clears={r['room']:r for r in clear(original)+extract_rewards(original)+extract_completions(original)}
    lines=['/* Source portal room / coordinate / destination / after-clear stage. */','static const u16 world_room_portals[36][4] = {']
    for r in portals:
        stage=int(r['room'] in clears and clears[r['room']]['call_site']<r['call_site'])
        lines.append('    {'+','.join(str(v) for v in [r['room'],r['coordinate'],r['destination_room'],stage])+'},')
    lines.append('};');assert (ROOT/'megadrive/src/room_portals.inc').read_text()=='\n'.join(lines)+'\n'
    prior_path=ROOT/'versions/v0051-3161f829/contacts_patch_audit.json';prior=json.loads(prior_path.read_bytes())
    baseline=(ROOT.parents[1]/'work/contacts-harness/src/game_main.inc').read_bytes();assert sha(baseline)==prior['source_files']['megadrive/src/main.c']
    old=baseline.decode().replace('\r\n','\n');current=(ROOT/'megadrive/src/main.c').read_text()
    a=current.index('/* Consecutive portal waits');b=current.index('extern const u8 world_door_records',a)
    restored=(current[:a]+current[b:]).replace('#include "room_portals.inc"\n','')
    a=restored.index('            if(hero_health)\n            {\n                u32 script_started=vtimer;');b=restored.index('\n            animate_dungeon_cells();',a)
    old_dispatch=next(line for line in old.splitlines() if 'if(hero_health) { u8 script_flags=' in line)
    restored=restored[:a]+old_dispatch+restored[b:];assert restored==old,'Unexpected production delta'
    copies=json.loads((prior_path.parent/'contacts_report.json').read_bytes())['source_copies']
    for name,expected in copies.items():
        if name!='main.c':assert sha((ROOT/'megadrive/src'/name).read_bytes())==expected,name
    snapshot=ROOT/'analysis/baseline-v0051-main.c'
    if snapshot.exists():assert snapshot.read_bytes()==baseline
    else:snapshot.write_bytes(baseline)
    names=[n+s for n in ['portals_gameplay','contacts_gameplay','shutters_gameplay','key_door_gameplay','timing'] for s in ['', '-pal']]
    reports={};evidence=[];timing=[]
    for name in names:
        path=ROOT/'validation'/f'{name}_report.json';raw=path.read_bytes();r=json.loads(raw);assert r['md_sha256']==digest,name
        reports[name]=r;evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
    for suffix in ['', '-pal']:
        cases=reports['portals_gameplay'+suffix]['cases'];assert len(cases)==36 and {c['room'] for c in cases}=={r['room'] for r in portals}
        for c in cases:
            assert c['loaded_state_cells_maps_flags_masks_loot_exact'] and c['visible_wipe_frames_exact']==20 and c['stationary_negative_guard_verified']
            assert c['destination']==next(r['destination_room'] for r in portals if r['room']==c['room'])
            assert all(t['changed']<t['loading']<t['resume'] for t in c['timing'].values())
            assert c['resume_delta'] in (0,1),(suffix,c)
            timing.append(dict(region='pal' if suffix else 'auto',room=c['room'],delta=c['resume_delta']))
        cases=reports['contacts_gameplay'+suffix]['cases'];assert len(cases)==22 and all(c['settled_cells_maps_flags_loot_counter_keys_exact'] and c['trigger_timing_exact'] for c in cases)
        cases=reports['shutters_gameplay'+suffix]['cases'];assert len(cases)==10 and all(c['before_and_after_state_fields_exact'] and c['timing']['sms']==c['timing']['md'] for c in cases)
        cases=reports['key_door_gameplay'+suffix]['cases'];assert len(cases)==9 and all(c['settled_crossing_return_fields_source_exact'] for c in cases)
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
        assert reports['timing'+suffix]['enemy']['differing_motion_counter_frames']==0
    source_audit=ROOT/'analysis/portal-source-v0051/portal_source_audit.json';r=json.loads(source_audit.read_bytes());assert r['source_sha256']==sha(original) and r['full_wipe_frame_maps_checked']==1440 and r['source_only_evidence']
    files=['megadrive/src/main.c','megadrive/src/room_portals.inc','tools/extract_contact_scripts.py','tools/validate_portals_gameplay.py','tools/audit_portals_patch.py','analysis/baseline-v0051-main.c']
    report=dict(md_sha256=digest,md_size=len(rom),checksum_aliases_verified=True,current_reports=evidence,source_files={n:sha((ROOT/n).read_bytes()) for n in files},prior_contact_audit_sha256=sha(prior_path.read_bytes()),source_portal_audit_sha256=sha(source_audit.read_bytes()),production_delta_confined_to_portals=True,source_portal_clear_order_exact=True,native_portals=36,live_portal_cases=72,visible_wipe_frames_exact=1440,live_contact_regression_cases=44,live_combat_door_regression_cases=20,live_key_door_regression_cases=18,resume_timing=timing,resume_exact_cases=sum(c['delta']==0 for c in timing),resume_one_frame_late_cases=sum(c['delta']==1 for c in timing),full_game_ported=False,limits=['Controlled solved-origin flag, source-prepared map, hero and frozen actor after real dungeon entry. Full natural puzzle completion and dungeon routes are unverified.','Loaded cells/maps/flags/masks/loot and arrival pose match at each system first gameplay-ready frame; actor AI/RNG progression after loading is not established.','Visible wipe positions match on all twenty frames; hidden VRAM preparation/IRQ phase differs and some resumes are one frame late.','Loader timing uses dynamic graphics T states plus a shared regional overhead, not per-room frame tables. Actor-history respawn, other puzzles, bosses and ending remain incomplete.','Full scene pixels, sprite priority edge cases and audio waveforms remain unverified.'])
    (ROOT/'validation/portals_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('10 current reports bound: 36 native portals, 72 live crossings, 1440 visible wipe frames; resumes',report['resume_exact_cases'],'exact,',report['resume_one_frame_late_cases'],'one frame late.')
if __name__=='__main__':main()
