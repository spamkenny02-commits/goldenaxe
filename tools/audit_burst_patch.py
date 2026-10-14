"""Bind the targeted36/37 milestone to its final cartridge and reports."""
import hashlib
import json
from pathlib import Path
from actor_reference import ROOT
from finalize_md_rom import md_checksum


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    data = (ROOT / 'gaw-megadrive.bin').read_bytes()
    digest = sha(data)
    assert len(data) == 524288
    assert int.from_bytes(data[0x18e:0x190], 'big') == md_checksum(data)
    assert int.from_bytes(data[0x1a4:0x1a8], 'big') == len(data) - 1
    for name in ['gaw-title-megadrive.bin', 'megadrive/out/release/rom.bin']:
        assert (ROOT / name).read_bytes() == data
    source = (ROOT / 'input/original.sms').read_bytes()
    assert sha(source) == '852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    assert source == Path(r'D:\Cartmod\GoldenAxeWarrior\chat\Golden Axe Warrior (USA, Europe).sms').read_bytes()
    reports = []
    for name in ['burst_walkers', 'burst_pool', 'burst_rooms', 'trap_walker',
                 'flying_actors', 'ranged', 'mobile_actors', 'water_jump',
                 'jumping_actors', 'house_dialogue']:
        path = ROOT / f'validation/{name}_report.json'
        raw = path.read_bytes()
        assert json.loads(raw)['md_sha256'] == digest, path
        reports.append(dict(file=path.name, sha256=sha(raw)))
    code = {name: sha((ROOT / name).read_bytes()) for name in
            ['megadrive/src/actors.c', 'megadrive/src/actor_data.c',
             'tools/extract_actors.py', 'tools/version_rom.py', 'build.ps1']}
    audit = dict(md_sha256=digest, bytes=len(data), md_additive_checksum=md_checksum(data),
                 reports=reports, source_sha256=sha(source), original_unchanged=True,
                 aliases_identical=True, source_files=code,
                 full_regression_rerun=False, full_game_ported=False,
                 known_limits=['Sprite-overflow suppression495E absent',
                               'Original RNG/clock and absolute room timing differ',
                               'Isolated record comparisons exclude collision descriptors27/28',
                               'Checkpoints do not prove complete natural progression',
                               'Remaining actors, quests, dungeons, dialogues, effects and rendering incomplete'])
    (ROOT / 'validation/burst_patch_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(f'{len(reports)} targeted reports bound to {digest}')


if __name__ == '__main__':
    main()
