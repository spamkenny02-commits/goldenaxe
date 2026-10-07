#!/usr/bin/env python3
"""Reach the village/save service using only pad input, then restart from SRAM.

Optional --reference-rom repeats the pad route on SMS and compares the settled
viewport using the pinned core's fixed DAC conversion. Private ROMs and captures
remain local. No work RAM edits or emulator savestates are used in this route.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--rom', type=Path, default=Path('md/build/gaw_md.bin'))
    parser.add_argument('--elf', type=Path, default=Path('md/build/gaw_md.elf'))
    parser.add_argument('--nm', default='m68k-elf-nm')
    parser.add_argument('--reference-rom', type=Path)
    parser.add_argument('--output', type=Path, default=Path('md/build/sanctuary-test'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tools = Path(__file__).resolve().parent
    scenario = tools.parent/'tests/scenarios/sanctuary_save.json'
    shared = [sys.executable, str(tools/'test_md_emulator.py'), '--core', str(args.core)]
    md = ['--rom', str(args.rom), '--elf', str(args.elf), '--nm', args.nm]

    def run(name, extra):
        output = args.output/name
        output.mkdir(parents=True, exist_ok=True)
        with (output/'run.log').open('w') as log:
            subprocess.run(shared+extra+['--output', str(output)], stdout=log, stderr=subprocess.STDOUT, check=True)
        return json.loads((output/'result.json').read_text())

    cartridge = args.output/'saved_sram.bin'
    route = run('route', md+['--play-inputs', str(scenario), '--sram-out', str(cartridge)])
    cells = [entry['cell'] for entry in route['world_transitions']]
    assert cells == [0x95, 0x94, 0], f'Wrong pad route: {cells}'
    saves = [entry for entry in route['input_steps'] if 'saved_slot' in entry]
    assert len(saves) == 1 and saves[0]['saved_slot'] == 0
    assert saves[0]['saved_return_cell'] == 0x94
    assert any(entry['state'] == '16' for entry in route['stages']), 'Save service was not reached'
    print('Controller route and production save: OK', flush=True)

    reloaded = args.output/'reloaded_sram.bin'
    restart = run('restart', md+['--sram-in', str(cartridge), '--sram-out', str(reloaded), '--expect-save-slot', '0'])
    assert restart['sram']['restore_checked']
    assert restart['world_cell'] == 0x94
    assert restart['player_hp'] == saves[0]['saved_hp']
    before, after = cartridge.read_bytes(), reloaded.read_bytes()
    assert len(before) == len(after) == 0x8000
    for i in range(0x8000):
        if not 0x1000 <= i < 0x14A0:
            assert before[i] == after[i], f'Restart changed persistent SRAM byte {i:04X}'
    print('SRAM-only process restart and continue: OK', flush=True)

    comparison = None
    if args.reference_rom:
        steps = json.loads(scenario.read_text())
        for step in steps:
            step.pop('expect_saved_slot', None)  # MD odd-byte cartridge layout assertion
        sms_inputs = args.output/'sms_inputs.json'
        sms_inputs.write_text(json.dumps(steps, indent=2)+'\n')
        reference = run('sms', ['--reference-sms', '--rom', str(args.reference_rom), '--play-inputs', str(sms_inputs)])
        assert [entry['cell'] for entry in reference['world_transitions']] == cells
        assert [(entry['state'], entry['game_frame']) for entry in reference['stages']] == [
            (entry['state'], entry['game_frame']) for entry in route['stages']]
        assert reference['player_hp'] == route['player_hp']
        assert reference['input_steps'][-1]['position'] == route['input_steps'][-1]['position']
        subprocess.run([sys.executable, str(tools/'compare_game_viewports.py'),
                        '--md', str(args.output/'route/final.png'), '--sms', str(args.output/'sms/final.png')], check=True)
        comparison = {'pixels': 49152, 'stage_game_frames': 'matched'}
    (args.output/'result.json').write_text(json.dumps({
        'route': {'cells': cells, 'saved_slot': 0, 'return_cell': 0x94, 'hp': saves[0]['saved_hp'],
                  'physical_frames': route['emulator_frames'], 'play_frames': route['play_frames']},
        'restart': {'cell': restart['world_cell'], 'hp': restart['player_hp'],
                    'play_frames': restart['play_frames'], 'restore_bytes': 592},
        'reference': comparison}, indent=2)+'\n')


if __name__ == '__main__':
    main()
