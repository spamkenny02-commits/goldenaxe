"""Bind persistent cell reconstruction and its source-execution evidence."""
import hashlib
import json
import re
from extract_world import ROOT, initial_room


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
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in
             (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    *_,arrays,_=initial_room(original)
    for name in ['world_room_metadata','world_dungeon_metadata','world_room_index','world_room_streams']:
        address=symbols[name]
        assert data[address:address+len(arrays[name])]==arrays[name],name
    assert len(arrays['world_room_metadata'])==111*4+1
    assert len(arrays['world_dungeon_metadata'])==73*4+1
    evidence=[];reports={}
    names=['room_cells','merchant']+[stem+suffix for stem in
        ['dungeon_scroll','dungeon_doors','dungeon_continue','scroll_objects','timing'] for suffix in ['', '-pal']]
    for stem in names:
        name=stem+'_report.json';raw=(ROOT/'validation'/name).read_bytes();report=json.loads(raw)
        assert report['md_sha256']==digest,name
        evidence.append(dict(file=name,sha256=sha(raw)));reports[stem]=report
    cells=reports['room_cells']
    assert cells['room_flag_cases']==8192 and cells['rooms']==512 and len(cells['flags'])==16
    assert cells['transformation_types_checked']==list(range(21))
    assert cells['metadata_and_persistent_flags_exact']
    for name,expected in cells['source_copies'].items():
        assert sha((ROOT/'megadrive/src'/name).read_bytes())==expected,name
    fixture=(ROOT/'validation/room-cells/source-room-cells.sms').read_bytes()
    assert sha(fixture)==cells['fixture_sha256']
    assert all(a==b for i,(a,b) in enumerate(zip(original,fixture)) if i not in [0,1,2,0x2f] and not 0x3e00<=i<0x3ff0)
    for suffix in ['', '-pal']:
        assert len(reports['dungeon_scroll'+suffix]['cases'])==8
        for stem in ['dungeon_doors','dungeon_continue']:
            cases=reports[stem+suffix]['cases']
            assert len(cases)==10 and all(c['settled_entry_exit_fields_source_exact'] for c in cases)
        assert all(c['checks']['md']['nonhero_sprite_errors']==0 for c in reports['scroll_objects'+suffix]['cases'])
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
    report=dict(md_sha256=digest,md_size=len(data),compiled_exterior_metadata_records=111,
                compiled_dungeon_metadata_records=73,original_z80_room_flag_cases_verified=8192,
                transformation_types_verified=21,rom_aliases_exact=True,additive_checksum_valid=True,
                current_targeted_reports=evidence,
                source_files={name:sha((ROOT/name).read_bytes()) for name in
                    ['tools/extract_world.py','tools/validate_room_cells.py','tools/room_cells_harness.c',
                     'tools/build_room_cells_harness.ps1','tools/audit_room_cells_patch.py','megadrive/src/main.c']},
                full_game_ported=False,natural_puzzle_activation_verified=False,
                limits=['Persistent flags are supplied by fixtures; puzzle triggers and key consumption remain to port.',
                        'Out-of-playfield scratch/queue writes are excluded from the 160-cell reconstruction comparison.',
                        'Exterior quest/portal processing after 1976, remaining enemies, bosses and ending remain incomplete.',
                        'Dungeon transition timing, lantern activation and full tile animation remain incomplete.'])
    (ROOT/'validation/room_cells_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Compiled metadata and twelve current reports bound to ROM; natural puzzle activation unverified.')


if __name__=='__main__':main()
