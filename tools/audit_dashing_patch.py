"""Bind the3C translation and distinct-octant regression to its cartridge."""
import hashlib
import json
from pathlib import Path
import re
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
    sy = {m[2].split('.lto_priv.')[0]: int(m[1], 16)
          for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
          if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    assert data[sy['actor_dash_vectors']:sy['actor_dash_vectors']+40] == original[0x93f2:0x941a]
    assert data[sy['actor_spawn_terrain']:sy['actor_spawn_terrain']+11] == original[0x586d:0x5878]
    names = ['dashing_actor', 'dashing_actor-pal', 'dashing_spawns', 'dashing_spawns-pal',
             'dashing_rooms', 'bouncing_shooters', 'scroll_objects', 'scroll_objects-pal',
             'timing', 'timing-pal', 'title_cadence', 'title_cadence-pal']
    evidence, count = [], 0
    for name in names:
        path = ROOT/f'validation/{name}_report.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, path
        if name.startswith('dashing_actor'):
            assert report['deterministic_cases'] == 32 and report['boundary_cases'] == 9
            assert len(report['controlled_decisions']) == 192
            assert len(report['trajectories']) == 11
            assert {t['octant'] for t in report['trajectories']} == set(range(8))
            assert report['record_comparisons'] == 4355
            count += report['record_comparisons']
        if name.startswith('dashing_spawns'):
            assert len(report['accepted']) == 2 and len(report['rejected']) == 4
            assert {r['next_state'] for r in report['accepted']} == {2, 4}
        if name == 'dashing_rooms':
            assert report['actor_dashes_in_at_least_one_room'] and not report['ram_mutations']
            assert len(report['rows']) == 4
        if name == 'bouncing_shooters':
            assert set(report['actual_octants']) == set(range(8))
        evidence.append(dict(file=path.name, sha256=sha(raw)))
    sources = ['megadrive/src/actors.c', 'megadrive/src/actor_data.c', 'tools/extract_actors.py',
               'tools/validate_dashing_actor.py', 'tools/validate_dashing_spawns.py',
               'tools/validate_dashing_rooms.py', 'tools/validate_bouncing_shooters.py']
    audit = dict(md_sha256=digest, source_sha256=sha(original), rom_bytes=len(data),
                 additive_checksum_valid=True, aliases_equal=True, original_unchanged=True,
                 source_dash_and_terrain_bytes_preserved=True,
                 evidence=evidence, source_files={name: sha((ROOT/name).read_bytes()) for name in sources},
                 dashing_actor_record_comparisons=count, full_game_ported=False,
                 original_rng_stream_reproduced=False, full_transition_timing_equivalence=False,
                 notes=['Collision-list descriptor bytes27/28 excluded from record comparisons',
                        'Hidden-delay and spawn RNG choices/phase explicitly controlled in fixtures',
                        'Cold-load checkpoints verify activity, not full progression or identical RNG',
                        'Eight1F test origins now prove eight distinct vectors; old origins covered six',
                        'Intro startup offsets, quests/dungeons and remaining actors are pending'])
    (ROOT/'validation/dashing_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} targeted reports bound to {digest}')


if __name__ == '__main__':
    main()
