#!/usr/bin/env python3
"""Validate controller-only combat on the native game and optional SMS reference.

Requires private ROM data. Combatants are reached through normal screen travel;
no work RAM edits, spawned test enemies or savestates are used. Native hardware
entropy differs from the original Z80 refresh register, so this checks combat
outcomes independently rather than demanding identical random trajectories.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def validate(result):
    assert result['final_state'] == '0C' and result['world_cell'] == 0x93
    assert 0 < result['player_hp'] < 24, 'Combat did not exercise player damage and survival'
    combat = result['combat']
    assert [e['cell'] for e in combat['encounters']] == [0x95, 0x94, 0x93]
    initial = [e for e in combat['encounters'][-1]['entities'] if e['type'] >= 32 and e['flags'] & 0x20]
    assert sorted(e['type'] for e in initial) == [32, 38, 38, 38, 38]
    assert len(combat['attacks']) >= 10, 'Attack animation/input stalled'
    assert combat['player_hits'] and all(e['before'] > e['after'] and e['flash'] for e in combat['player_hits'])
    assert combat['enemy_hits'], 'No enemy damage observed'
    assert combat['enemy_deaths'], 'No enemy death observed'
    assert combat['projectiles'], 'Ranged enemy did not spawn a projectile'
    assert all(e['cell'] == 0x93 and e['before'] > e['after'] for e in combat['enemy_hits'])
    deaths = {(e['slot'], e['type']) for e in combat['enemy_deaths']}
    assert len(deaths) == len(combat['enemy_deaths']), 'Duplicate enemy deaths'
    for slot, kind in deaths:
        assert any(e['slot'] == slot and e['type'] == kind and e['after'] == 0 for e in combat['enemy_hits'])
        assert combat['final_entities'][slot]['type'] == 0, 'Enemy death animation did not clear its slot'
    remaining = [e for e in combat['final_entities'][16:24] if e['type'] >= 32 and e['flags'] & 0x20]
    assert len(remaining)+len(deaths) == len(initial), 'Encounter teardown was counted as a kill'
    return {'attacks': len(combat['attacks']), 'player_hits': len(combat['player_hits']),
            'enemy_hits': len(combat['enemy_hits']), 'enemy_deaths': len(deaths),
            'projectiles': len(combat['projectiles']), 'hp': result['player_hp'],
            'physical_frames': result['emulator_frames'],
            'final_position': result['input_steps'][-1]['position']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--rom', type=Path, default=Path('md/build/gaw_md.bin'))
    parser.add_argument('--elf', type=Path, default=Path('md/build/gaw_md.elf'))
    parser.add_argument('--nm', default='m68k-elf-nm')
    parser.add_argument('--reference-rom', type=Path)
    parser.add_argument('--output', type=Path, default=Path('md/build/combat-test'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tools = Path(__file__).resolve().parent
    scenario = tools.parent/'tests/scenarios/combat_field.json'
    shared = [sys.executable, str(tools/'test_md_emulator.py'), '--core', str(args.core),
              '--combat', '--play-inputs', str(scenario)]
    results = {}
    runs = [('md', ['--rom', str(args.rom), '--elf', str(args.elf), '--nm', args.nm])]
    if args.reference_rom:
        runs.append(('sms', ['--reference-sms', '--rom', str(args.reference_rom)]))
    for name, extra in runs:
        output = args.output/name
        output.mkdir(parents=True, exist_ok=True)
        with (output/'run.log').open('w') as log:
            subprocess.run(shared+extra+['--output', str(output)], stdout=log, stderr=subprocess.STDOUT, check=True)
        result = json.loads((output/'result.json').read_text())
        results[name] = validate(result)
        print(name+': '+json.dumps(results[name]), flush=True)
    (args.output/'result.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    main()
