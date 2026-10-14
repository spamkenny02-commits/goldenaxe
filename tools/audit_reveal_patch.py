"""Bind first-scene reveal and intro/title/scroll regressions to a cartridge."""
import hashlib
import json
from actor_reference import ROOT
from finalize_md_rom import md_checksum


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    data = (ROOT/'gaw-megadrive.bin').read_bytes()
    digest = sha(data)
    assert len(data) == 524288
    assert int.from_bytes(data[0x18e:0x190], 'big') == md_checksum(data)
    for alias in ['gaw-title-megadrive.bin', 'megadrive/out/release/rom.bin']:
        assert (ROOT/alias).read_bytes() == data
    paths = ['analysis/intro_reveal_profile.json']
    paths += [f'validation/{name}_report.json' for name in
              ['intro', 'intro-pal', 'title_cadence', 'title_cadence-pal',
               'title_cadence-natural', 'title_cadence-pal-natural',
               'scroll_objects', 'scroll_objects-pal', 'timing', 'timing-pal']]
    evidence = []
    for name in paths:
        raw = (ROOT/name).read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == digest, name
        if 'intro_reveal_profile' in name:
            for region, systems in report['regions'].items():
                assert systems['comparison']['completed_pass_patterns_exact']
                assert systems['comparison']['pass_cadence_frames'] == 5
                for tag in ['sms', 'md']:
                    assert len(systems[tag]['passes']) == 8
        if name in ['validation/intro_report.json', 'validation/intro-pal_report.json']:
            assert len(report['story_lines']) == 65
            assert report['title_returns_after_intro'] and report['no_accumulating_text_delay']
        if 'scroll_objects' in name:
            assert len(report['cases']) == 4
            assert all(c['checks']['md']['nonhero_sprite_errors'] == 0 for c in report['cases'])
        evidence.append(dict(file=name, sha256=sha(raw)))
    audit = dict(md_sha256=digest, rom_bytes=len(data), aliases_equal=True,
                 additive_checksum_valid=True, evidence=evidence,
                 source_files={name:sha((ROOT/name).read_bytes()) for name in
                    ['megadrive/src/intro.inc', 'tools/profile_intro_reveal.py']},
                 first_scene_reveal_cadence_verified=True,
                 partial_frame_patterns_exact=False, absolute_intro_timing_exact=False,
                 other_scene_reveal_cadence_verified=False, full_game_ported=False)
    (ROOT/'validation/reveal_patch_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'{len(evidence)} reports bound to {digest}')


if __name__ == '__main__':
    main()
