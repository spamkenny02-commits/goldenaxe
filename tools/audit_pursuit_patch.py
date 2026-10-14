"""Bind3D/3E and1A targeted evidence to the final native cartridge."""
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
    base = sy['actor_projectile_templates']+7*22
    assert data[base:base+22] == original[0x409b:0x40b1]
    names = ['pursuit_shooters', 'pursuit_shooters-pal', 'pursuit_rooms', 'dashing_actor',
             'scroll_objects', 'scroll_objects-pal', 'timing', 'timing-pal',
             'title_cadence', 'title_cadence-pal']
    evidence, count = [], 0
    for name in names:
        path = ROOT/f'validation/{name}_report.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, path
        if name.startswith('pursuit_shooters'):
            assert report['deterministic_cases'] == 32 and report['blocked_cases'] == 48
            assert len(report['controlled_decisions']) == 192
            assert len(report['projectile_culls']) == 4 and report['projectile_frames'] == 132
            assert report['source_sprite_overflow_status_cleared_in_decision_fixtures']
            assert not report['sprite_overflow_suppression_verified']
            assert report['record_comparisons'] == 3760
            count += report['record_comparisons']
        if name == 'pursuit_rooms':
            assert report['both_types_pursue_in_at_least_one_room'] and not report['ram_mutations']
            assert len(report['rows']) == 4 and all(row['projectile_births'] for row in report['rows'])
        evidence.append(dict(file=path.name, sha256=sha(raw)))
    sources = ['megadrive/src/actors.c', 'megadrive/src/actor_data.c', 'tools/extract_actors.py',
               'tools/validate_pursuit_shooters.py', 'tools/validate_pursuit_rooms.py']
    audit = dict(md_sha256=digest, source_sha256=sha(original), rom_bytes=len(data),
                 additive_checksum_valid=True, aliases_equal=True, original_unchanged=True,
                 projectile1a_template_source_exact=True, evidence=evidence,
                 source_files={name: sha((ROOT/name).read_bytes()) for name in sources},
                 pursuit_actor_record_comparisons=count, full_game_ported=False,
                 sprite_overflow_suppression_verified=False, original_rng_stream_reproduced=False,
                 notes=['Decision fixtures clear source C01B overflow; source495E suppression is still missing',
                        'Collision-list descriptor bytes27/28 excluded from record comparisons',
                        'Cold-load checkpoints verify activity/shots, not full progression or identical RNG',
                        'Intro startup offsets, quests/dungeons and remaining actors are pending'])
    (ROOT/'validation/pursuit_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} targeted reports bound to {digest}')


if __name__ == '__main__':
    main()
