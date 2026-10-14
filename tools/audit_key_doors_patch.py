"""Bind the key-door translation and focused source-execution comparisons."""
import hashlib,json
from extract_world import ROOT


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(data)
    original=(ROOT/'input/original.sms').read_bytes()
    assert sha(original)=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    assert len(data)==524288
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
        assert (ROOT/name).read_bytes()==data
    assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535
    assert int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
    names=['key_doors','room_cells']+[stem+suffix for stem in ['dungeon_scroll','dungeon_doors','timing'] for suffix in ['', '-pal']]
    reports={};evidence=[]
    for stem in names:
        name=stem+'_report.json';raw=(ROOT/'validation'/name).read_bytes();report=json.loads(raw)
        assert report['md_sha256']==digest,name
        reports[stem]=report;evidence.append(dict(file=name,sha256=sha(raw)))
    keys=reports['key_doors'];cells=reports['room_cells']
    assert keys['cases_checked']==8192 and keys['source_opened_cases']==180 and keys['source_key_consumption_cases']==120
    assert keys['source_cells_maps_all_room_flags_and_key_count_exact']
    assert cells['room_flag_cases']==8192 and cells['transformation_types_checked']==list(range(21))
    for report in [keys,cells]:
        for name,expected in report['source_copies'].items():
            assert sha((ROOT/'megadrive/src'/name).read_bytes())==expected,name
    fixture=(ROOT/'validation/key-doors/source-key-doors.sms').read_bytes()
    assert sha(fixture)==keys['fixture_sha256']
    assert all(a==b for i,(a,b) in enumerate(zip(original,fixture)) if i not in [0,1,2,0x2f,0xb95] and not 0x3d00<=i<0x3ff0)
    for suffix in ['', '-pal']:
        assert len(reports['dungeon_scroll'+suffix]['cases'])==8
        assert all(c['destination_state_source_exact'] and c['old_objects_hidden'] for c in reports['dungeon_scroll'+suffix]['cases'])
        assert len(reports['dungeon_doors'+suffix]['cases'])==10
        assert all(c['settled_entry_exit_fields_source_exact'] for c in reports['dungeon_doors'+suffix]['cases'])
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
    report=dict(md_sha256=digest,md_size=len(data),rom_aliases_exact=True,additive_checksum_valid=True,
                source_key_door_cases=8192,persistent_room_reconstruction_cases=8192,
                current_targeted_reports=evidence,
                source_files={name:sha((ROOT/name).read_bytes()) for name in
                    ['tools/validate_key_doors.py','tools/validate_room_cells.py','tools/key_doors_harness.c',
                     'tools/build_key_doors_harness.ps1','tools/audit_key_doors_patch.py','megadrive/src/main.c']},
                natural_key_door_gameplay_verified=False,full_game_ported=False,
                limits=['Controlled inputs and positions call dispatch directly; live controller integration, repeated contacts and re-entry require verification.',
                        'Isolated SMS IRQ wait 0B95 is bypassed; source dispatch and redraw remain unchanged.',
                        'Native sound waveforms and source redraw latency are not compared.',
                        'Room-clear triggers, other puzzles, remaining enemies, bosses and ending remain incomplete.'])
    (ROOT/'validation/key_doors_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('8192 key-door cases, 8192 room-state cases and eight reports bound to ROM.')


if __name__=='__main__':main()
