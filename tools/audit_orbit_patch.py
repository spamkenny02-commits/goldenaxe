"""Bind orbit enemy evidence and scrolling regressions to the released ROM."""
import hashlib
import json
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
    assert sha(original) == '852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    sy = {m[2].split('.lto_priv.')[0]: int(m[1], 16)
          for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
          if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    for symbol, start, end in [('actor_orbit_facing', 0x983f, 0x9843),
                               ('actor_homing_template', 0x415c, 0x4182)]:
        base = sy[symbol]
        assert data[base:base+end-start] == original[start:end]
    names = ['orbit_actor', 'orbit_actor-pal', 'orbit_rooms', 'burst_walkers',
             'bouncing_shooters', 'scroll_objects', 'scroll_objects-pal',
             'timing', 'timing-pal', 'title_cadence', 'title_cadence-pal']
    evidence, count, scroll_frames = [], 0, 0
    for name in names:
        path = ROOT/f'validation/{name}_report.json'
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, path
        if name.startswith('orbit_actor'):
            assert report['deterministic_cases'] == 7 and report['sine_cases'] == 1024
            assert report['projectile_octants'] == list(range(8))
            assert report['segment_starts'] == [3102+17*n for n in range(8)]
            assert report['projectile_clear_frame'] == 3237
            assert report['homing_guard_cases'] == 12
            assert report['record_comparisons'] == 65819
            count += report['record_comparisons']
        if name == 'orbit_rooms':
            assert report['two_orbit_rooms_verified'] and not report['ram_mutations']
            assert report['checkpoint_health'] == 80
            assert len(report['rows']) == 4 and all(r['projectile_births'] for r in report['rows'])
        if name.startswith('scroll_objects'):
            assert {c['direction'] for c in report['cases']} == {'left', 'right', 'up', 'down'}
            for case in report['cases']:
                check = case['checks']['md']
                assert check['nonhero_sprite_errors'] == 0
                assert check['old_object_flags_cleared'] and check['primary_living_mask_preserved']
                assert check['hero_sprite_frames'] == check['checked_transition_frames']
                assert check['gameplay_resumes']
                scroll_frames += check['checked_transition_frames']
        evidence.append(dict(file=path.name, sha256=sha(raw)))
    audit = dict(md_sha256=digest, source_sha256=sha(original), rom_bytes=len(data),
                 additive_checksum_valid=True, aliases_equal=True,
                 orbit_assets_source_exact=True, evidence=evidence,
                 orbit_record_comparisons=count, clean_scroll_frames=scroll_frames,
                 full_game_ported=False, source_rng_stream_verified=False,
                 sprite_overflow_suppression_verified=False,
                 notes=['Orbit attack RNG choices are controlled in deterministic tests',
                        'Moving projectile targets use explicit RAM fixtures',
                        'Room checkpoints have 80 HP; cartridge balance is unchanged',
                        'Quests/dungeons, intro offsets and full progression remain pending'])
    (ROOT/'validation/orbit_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} reports, {scroll_frames} clean scroll frames: {digest}')


if __name__ == '__main__':
    main()
