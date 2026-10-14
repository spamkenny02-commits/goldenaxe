"""Bind3F translation, four-hop sequence and regression evidence to its ROM."""
import hashlib
import json
import re
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
    sy = {m[2].split('.lto_priv.')[0]: int(m[1], 16)
          for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
          if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    base = sy['actor_jumping_vectors']
    assert data[base:base+64] == original[0x8ca3:0x8ce3]
    base = sy['actor_mobile_sequences']+17
    assert data[base:base+17] == original[0x85ea:0x85fb]
    names = ['hopping_actor', 'hopping_actor-pal', 'hopping_spawns', 'hopping_spawns-pal',
             'hopping_rooms', 'pursuit_shooters', 'scroll_objects', 'scroll_objects-pal',
             'timing', 'timing-pal', 'title_cadence', 'title_cadence-pal']
    evidence, count = [], 0
    for name in names:
        path = ROOT/f'validation/{name}_report.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, path
        if name.startswith('hopping_actor'):
            assert report['deterministic_cases'] == 36 and report['jump_guard_cases'] == 128
            assert len(report['controlled_decisions']) == 384 and len(report['cycle_jumps']) == 4
            assert report['jump_guard_rejections'] >= 64
            assert report['record_comparisons'] == 80+384*16+128*16+report['cycle_frames']
            count += report['record_comparisons']
        if name.startswith('hopping_spawns'):
            assert len(report['accepted']) == 1 and len(report['rejected']) == 4
        if name == 'hopping_rooms':
            assert report['actor_hops_in_at_least_one_room'] and not report['ram_mutations']
            assert len(report['rows']) == 4
        evidence.append(dict(file=path.name, sha256=sha(raw)))
    sources = ['megadrive/src/actors.c', 'tools/validate_hopping_actor.py',
               'tools/actor_pair_validation.py', 'tools/validate_hopping_spawns.py',
               'tools/validate_hopping_rooms.py']
    audit = dict(md_sha256=digest, source_sha256=sha(original), rom_bytes=len(data),
                 additive_checksum_valid=True, aliases_equal=True, original_unchanged=True,
                 jump_and_walk_vectors_source_exact=True, evidence=evidence,
                 source_files={name: sha((ROOT/name).read_bytes()) for name in sources},
                 hopping_actor_record_comparisons=count, full_game_ported=False,
                 original_rng_stream_reproduced=False, sprite_overflow_suppression_verified=False,
                 notes=['Random choices and IRQ phase are controlled only in explicit test fixtures',
                        'Collision-list descriptor bytes27/28 excluded from record comparisons',
                        'Cold-load checkpoints verify activity, not natural progression or identical RNG',
                        'Intro startup offsets, overflow495E, quests/dungeons and remaining actors are pending'])
    (ROOT/'validation/hopping_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} targeted reports bound to {digest}')


if __name__ == '__main__':
    main()
