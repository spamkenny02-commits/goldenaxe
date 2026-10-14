"""Bind40/41,1B/1D assets and targeted live-core evidence to their cartridge."""
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
    base = sy['actor_projectile_templates']+8*22
    assert data[base:base+22] == original[0x40cb:0x40e1]
    base = sy['actor_lob_vectors']
    assert data[base:base+10] == original[0x4277:0x4281]
    names = ['walker40', 'walker40-pal', 'ambusher41', 'ambusher41-pal',
             'ambusher41_spawns', 'ambusher41_spawns-pal', 'actors40_41_rooms',
             'pursuit_shooters', 'hopping_actor', 'scroll_objects', 'scroll_objects-pal',
             'timing', 'timing-pal', 'title_cadence', 'title_cadence-pal']
    evidence, count = [], 0
    for name in names:
        path = ROOT/f'validation/{name}_report.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, path
        if name in ['walker40', 'walker40-pal']:
            assert report['deterministic_cases'] == 16 and report['blocked_cases'] == 24
            assert len(report['controlled_decisions']) == 192 and len(report['projectile_culls']) == 4
            assert report['record_comparisons'] == 3696
            count += report['record_comparisons']
        if name in ['ambusher41', 'ambusher41-pal']:
            assert report['deterministic_cases'] == 16 and len(report['pool_cases']) == 9
            assert len(report['lob_landings']) == 4 and report['terrain_cases'] == 10
            assert report['terrain_kills'] == 2 and report['record_comparisons'] == 586
            count += report['record_comparisons']
        if name.startswith('ambusher41_spawns'):
            assert len(report['accepted']) == 1 and len(report['rejected']) == 4
        if name == 'actors40_41_rooms':
            assert report['both_types_active_and_shoot'] and not report['ram_mutations']
            assert len(report['rows']) == 4 and all(r['projectile_births'] for r in report['rows'])
        evidence.append(dict(file=path.name, sha256=sha(raw)))
    files = ['megadrive/src/actors.c', 'megadrive/src/actor_data.c', 'tools/extract_actors.py',
             'tools/validate_walker40.py', 'tools/validate_ambusher41.py',
             'tools/validate_ambusher41_spawns.py', 'tools/validate_actors40_41_rooms.py']
    audit = dict(md_sha256=digest, source_sha256=sha(original), rom_bytes=len(data),
                 additive_checksum_valid=True, aliases_equal=True, original_unchanged=True,
                 projectile1b_and_lob_vectors_source_exact=True, evidence=evidence,
                 source_files={f: sha((ROOT/f).read_bytes()) for f in files},
                 new_actor_record_comparisons=count, full_game_ported=False,
                 original_rng_stream_reproduced=False, sprite_overflow_suppression_verified=False,
                 notes=['40 fixtures clear source overflow;495E suppression remains absent',
                        '41 uses direct4965 allocation and its partial-failure path is verified',
                        'Collision-list descriptor bytes27/28 excluded from record comparisons',
                        'Checkpoint rooms do not prove full progression or identical RNG',
                        '42/1C, quests/dungeons, intro offsets and other fidelity work remain pending'])
    (ROOT/'validation/ambusher_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} targeted reports bound to {digest}')


if __name__ == '__main__':
    main()
