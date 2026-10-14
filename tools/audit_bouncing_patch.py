"""Bind the walkers38/39 and bouncing1F milestone to the tested cartridge."""
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
    names = ['bouncing_shooters', 'bouncing_shooters-pal', 'bouncing_rooms',
             'burst_walkers', 'scroll_objects', 'scroll_objects-pal',
             'timing', 'timing-pal', 'title_cadence', 'title_cadence-pal']
    evidence = []
    for name in names:
        path = ROOT/f'validation/{name}_report.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, path
        if name.startswith('bouncing_shooters'):
            assert report['deterministic_shooter_cases'] == 72
            assert report['record_comparisons'] == 4574
            assert len(report['controlled_decisions']) == 192
            assert report['projectile_pool_cases'] == 9
            assert report['boundary_and_arithmetic_cases'] == 14
            assert len(report['clears']) == 8 and report['bounces']
        if name == 'bouncing_rooms':
            assert report['both_types_aim_in_at_least_one_room']
            assert len(report['rows']) == 4 and not report['ram_mutations']
        evidence.append(dict(file=path.name, sha256=sha(raw)))
    sources = ['megadrive/src/actors.c', 'megadrive/src/actor_data.c',
               'tools/extract_actors.py', 'tools/validate_bouncing_shooters.py',
               'tools/validate_bouncing_rooms.py']
    audit = dict(md_sha256=digest, source_sha256=sha(original), rom_bytes=len(data),
                 additive_checksum_valid=True, aliases_equal=True, original_unchanged=True,
                 evidence=evidence, source_files={name: sha((ROOT/name).read_bytes()) for name in sources},
                 source_record_comparisons=9148, full_game_ported=False,
                 original_rng_stream_reproduced=False, full_transition_timing_equivalence=False,
                 notes=['Collision-list descriptor bytes27/28 excluded from record comparisons',
                        'Cold-load room checkpoints verify activity and shots, not complete progression',
                        'Both types aim in at least one checkpoint; MD type38 does not aim during the observed room24 run',
                        'Existing intro startup offsets, quest/dungeon and remaining actor work are pending'])
    (ROOT/'validation/bouncing_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} targeted reports bound to {digest}')


if __name__ == '__main__':
    main()
