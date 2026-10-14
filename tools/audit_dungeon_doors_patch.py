"""Bind the dungeon entrance milestone to its cartridge and focused evidence."""
import hashlib
import json
import re
from extract_world import ROOT, initial_room


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    data = (ROOT / 'gaw-megadrive.bin').read_bytes()
    digest = sha(data)
    original = (ROOT / 'input/original.sms').read_bytes()
    assert sha(original) == '852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    assert len(data) == 524288
    for name in ['gaw-title-megadrive.bin', 'megadrive/out/release/rom.bin']:
        assert (ROOT / name).read_bytes() == data, name
    assert int.from_bytes(data[0x18e:0x190], 'big') == sum(int.from_bytes(data[i:i+2], 'big') for i in range(0x200, len(data), 2)) & 65535
    assert int.from_bytes(data[0x1a4:0x1a8], 'big') == len(data) - 1
    symbols = {m[2].split('.lto_priv.')[0]: int(m[1], 16) for line in
               (ROOT / 'megadrive/out/release/symbol.txt').read_text().splitlines()
               if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    *_, arrays, _ = initial_room(original)
    for name in ['world_room_index', 'world_room_streams', 'world_dungeon_background_rle',
                 'world_dungeon_extra_meta', 'world_dungeon_palettes',
                 'world_dungeon_dark_rooms', 'world_dungeon_color_cycle']:
        address = symbols[name]
        assert data[address:address+len(arrays[name])] == arrays[name], name
    doors = json.loads((ROOT / 'analysis/doors_reference.json').read_bytes())
    entrances = doors['direct_unconditional_dungeon_doors']
    exits = doors['standard_dungeon_exits']
    assert len(entrances) == len(exits) == 10
    records = b''.join(d[k].to_bytes(2, 'big') for d in entrances for k in ['room', 'x', 'y', 'target', 'index'])
    address = symbols['world_dungeon_door_records']
    assert data[address:address+len(records)] == records
    for d in entrances:
        offset = d['rom_stub_offset']
        assert original[offset:offset+8] == b'\x01' + d['source_coordinate'].to_bytes(2, 'little') + b'\x1e' + bytes([d['index']]) + bytes.fromhex('cd6065')
        assert d['target'] == 256 + original[0x6589+d['index']]
    for room in exits:
        assert original[0xb762+room*2:0xb764+room*2] == bytes.fromhex('4d65')
    address = symbols['world_standard_dungeon_exit']
    assert data[address:address+256] == bytes(int(256+n in exits) for n in range(256))
    names = ['dungeon_world_assets', 'world_loader_harness', 'merchant']
    names += [stem+suffix for stem in ['dungeon_doors', 'dungeon_continue', 'scroll_objects', 'timing', 'title_cadence', 'intro'] for suffix in ['', '-pal']]
    reports = {}
    evidence = []
    for stem in names:
        name = stem + '_report.json'
        raw = (ROOT / 'validation' / name).read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, name
        reports[stem] = report
        evidence.append(dict(file=name, sha256=sha(raw)))
    source = reports['dungeon_world_assets']
    assert source['maps_checked'] == 512
    for name, expected in source['files'].items():
        assert sha((ROOT / name).read_bytes()) == expected, name
    native = reports['world_loader_harness']
    assert native['rooms_checked'] == native['hardware_background_uploads_checked'] == 512
    assert native['dungeon_palettes_exercised'] == 10 and native['dark_room_loads_checked'] == 38
    for name, expected in native['source_copies'].items():
        assert sha((ROOT / 'megadrive/src' / name).read_bytes()) == expected, name
    for suffix in ['', '-pal']:
        for stem in ['dungeon_doors', 'dungeon_continue']:
            report = reports[stem+suffix]
            assert len(report['cases']) == 10
            for case in report['cases']:
                assert case['settled_entry_exit_fields_source_exact']
                assert case['actor_mask_bytes_source_exact'] == 512
                assert case['fixed_palette_bytes_source_exact'] == 13
                assert case['music_source_exact'] and case['visited_flag_source_exact']
                assert case['animated_palette_colors_valid']
                assert case['death_continue_checked'] == (stem == 'dungeon_continue')
        assert all(c['checks']['md']['nonhero_sprite_errors'] == 0 for c in reports['scroll_objects'+suffix]['cases'])
        assert all(c['differing_state_frames'] == 0 for c in reports['timing'+suffix]['natural_input_sequences'])
    report = dict(md_sha256=digest, md_size=len(data), compiled_unconditional_dungeon_entrances=10,
                  compiled_standard_dungeon_exits=10, source_z80_maps_verified=512,
                  native_68000_base_room_loads_verified=512, controlled_door_and_continue_cases=40,
                  current_targeted_reports=evidence, rom_aliases_exact=True, additive_checksum_valid=True,
                  full_game_ported=False, full_natural_dungeon_progression_verified=False,
                  limits=['Dungeon scrolling is still disabled.',
                          'Entrance fixtures initialize room maps and positions; natural routes are untested.',
                          'Entry fades, loading latency and animated palette phase are not source exact.',
                          'Conditional cells, keys, puzzles, quests, remaining enemies, bosses and ending are incomplete.',
                          'Dark rooms load unlit; lantern activation and full tile animation remain incomplete.'])
    (ROOT / 'validation/dungeon_doors_patch_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Ten compiled entrances/exits, 40 controlled cases and 15 current reports bound to ROM.')


if __name__ == '__main__':
    main()
