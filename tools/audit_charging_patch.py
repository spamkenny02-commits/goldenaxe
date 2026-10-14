"""Bind the translated3A/3B milestone to its cartridge and live-core evidence."""
import hashlib
import json
from pathlib import Path
from actor_reference import ROOT
from finalize_md_rom import md_checksum


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    data = (ROOT/'gaw-megadrive.bin').read_bytes()
    digest = sha(data)
    assert len(data) == 524288
    assert int.from_bytes(data[0x18e:0x190], 'big') == md_checksum(data)
    assert int.from_bytes(data[0x1a4:0x1a8], 'big') == len(data)-1
    for alias in ['gaw-title-megadrive.bin', 'megadrive/out/release/rom.bin']:
        assert (ROOT/alias).read_bytes() == data
    original = (ROOT/'input/original.sms').read_bytes()
    assert original == Path(r'D:\Cartmod\GoldenAxeWarrior\chat\Golden Axe Warrior (USA, Europe).sms').read_bytes()
    assert sha(original) == '852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    names = ['charging_actors', 'charging_actors-pal', 'charging_spawns', 'charging_spawns-pal',
             'charging_rooms', 'bouncing_shooters', 'scroll_objects', 'scroll_objects-pal',
             'timing', 'timing-pal', 'title_cadence', 'title_cadence-pal']
    evidence = []
    record_count = 0
    for name in names:
        path = ROOT/f'validation/{name}_report.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, path
        if name.startswith('charging_actors'):
            assert report['deterministic_cases'] == 72 and report['blocked_terrain_cases'] == 48
            assert len(report['controlled_decisions']) == 192 and len(report['charge_stops']) == 8
            assert report['record_comparisons'] == 4086
            record_count += report['record_comparisons']
        if name.startswith('charging_spawns'):
            assert len(report['accepted']) == 4 and len(report['rejected']) == 6
        if name == 'charging_rooms':
            assert report['both_types_charge_in_at_least_one_room'] and not report['ram_mutations']
            assert len(report['rows']) == 4
        evidence.append(dict(file=path.name, sha256=sha(raw)))
    sources = ['megadrive/src/actors.c', 'megadrive/src/actor_data.c',
               'tools/extract_actors.py', 'tools/validate_charging_actors.py',
               'tools/validate_charging_spawns.py', 'tools/validate_charging_rooms.py']
    audit = dict(md_sha256=digest, source_sha256=sha(original), rom_bytes=len(data),
                 additive_checksum_valid=True, aliases_equal=True, original_unchanged=True,
                 evidence=evidence, source_files={name: sha((ROOT/name).read_bytes()) for name in sources},
                 charging_actor_record_comparisons=record_count, full_game_ported=False,
                 original_rng_stream_reproduced=False, full_transition_timing_equivalence=False,
                 notes=['Collision-list descriptor bytes27/28 excluded from actor record comparisons',
                        'Cold-load room checkpoints verify walking and charging, not full progression',
                        'Spawn fixtures explicitly control random choices and IRQ phase',
                        'Existing intro startup offsets, quests/dungeons and remaining actors are pending'])
    (ROOT/'validation/charging_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} targeted reports bound to {digest}')


if __name__ == '__main__':
    main()
