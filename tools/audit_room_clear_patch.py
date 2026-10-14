"""Bind clear-event, floor animation and key regression evidence to one ROM."""
import hashlib,json
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    assert len(rom)==524288
    assert int.from_bytes(rom[0x18e:0x190],'big')==sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535
    assert int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
    names=['room_clear','dungeon_cells','key_doors']+[name+suffix for name in ['room_clear_gameplay','room_clear_cross','key_door_gameplay','timing'] for suffix in ['', '-pal']]
    evidence=[];reports={}
    for stem in names:
        path=ROOT/'validation'/f'{stem}_report.json';raw=path.read_bytes();r=json.loads(raw);assert r['md_sha256']==digest,stem
        reports[stem]=r;evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
    for name in ['room_clear','dungeon_cells','key_doors']:
        r=reports[name];assert r['cases_checked']==8192
        for file,expected in r['source_copies'].items():assert sha((ROOT/'megadrive/src'/file).read_bytes())==expected,file
    assert reports['room_clear']['source_opened_cases']==118
    assert reports['room_clear']['room_clear_latch_exact'] and reports['room_clear']['repeated_dispatch_verified']
    assert reports['key_doors']['source_opened_cases']==180 and reports['key_doors']['source_key_consumption_cases']==120
    assert reports['dungeon_cells']['cells_map_scan_phase_and_flags_exact']
    residual=[]
    for suffix in ['', '-pal']:
        cases=reports['room_clear_gameplay'+suffix]['cases'];assert len(cases)==6
        assert all(c['settled_cells_exact'] and c['settled_map_exact'] and c['settled_flags_count_keys_exact'] for c in cases)
        for c in cases:
            if c['expected_passage_flags']:
                for t in c['timing'].values():assert t['opening']==t['particle_gone']==3404
        cases=reports['room_clear_cross'+suffix]['cases'];assert len(cases)==3 and all(c['cross_and_return_verified'] and c['settled_flags_count_keys_exact'] for c in cases)
        for c in cases:
            if not c['settled_cells_exact']:residual.append(dict(region=suffix or 'ntsc',room=c['room'],cells=c['settled_cell_differences'],timing=c['timing']))
        assert len(reports['key_door_gameplay'+suffix]['cases'])==9
        assert all(c['settled_crossing_return_fields_source_exact'] for c in reports['key_door_gameplay'+suffix]['cases'])
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
        assert reports['timing'+suffix]['enemy']['differing_motion_counter_frames']==0
    from extract_room_clear import extract
    records=extract((ROOT/'input/original.sms').read_bytes());assert len(records)==49
    source_files=['megadrive/src/main.c','megadrive/src/room_clear.inc','megadrive/src/actors.c','analysis/room_clear_reference.json','tools/extract_room_clear.py','tools/validate_room_cells.py','tools/validate_room_clear.py','tools/validate_dungeon_cells.py','tools/validate_room_clear_gameplay.py','tools/room_clear_harness.c','tools/dungeon_cells_harness.c','tools/audit_room_clear_patch.py']
    report=dict(md_sha256=digest,md_size=len(rom),rom_checksum_and_aliases_verified=True,source_clear_rooms=len(records),isolated_cases=24576,live_final_particle_cases=12,live_cross_return_cases=6,key_controller_regression_cases=18,evidence=evidence,source_files={name:sha((ROOT/name).read_bytes()) for name in source_files},remaining_post_return_animation_differences=residual,full_game_ported=False,limits=['Fixtures supply rooms, masks, counters and particle state; natural complete fights and dungeon routes are not verified.','Crossing cases use the original FF hurt guard to exclude enemy attacks.','Original 6AA5 scan/phase behavior matches in isolation; loading offsets can shift animation phases after returning.','Dungeon tile bitmap animation 6A66..6AA5, other clear rewards, push-block scripts, bosses and ending remain incomplete.','Full transition pixels, source redraw IRQ phase and audio waveform remain unverified.'])
    (ROOT/'validation/room_clear_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('11 current reports bound; 49 room handlers, 24576 isolated cases, 18 live clear/cross cases; remaining animation differences:',len(residual))
if __name__=='__main__':main()
