#!/usr/bin/env python3
"""Check production MD save menus and SRAM-only process restarts.

Requires the private game build and pinned Genesis Plus GX core. Service
arrival is injected by the runner; save/continue menus use controller input.
No CPU savestates or work RAM snapshots are imported.
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
    parser.add_argument('--output', type=Path, default=Path('md/build/save-cycles'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    runner = Path(__file__).with_name('test_md_emulator.py')
    results = []

    def run(name, source=None, slot=None, expected=None):
        output = args.output/name
        output.mkdir(parents=True, exist_ok=True)
        target = output/'sram.bin'
        command = [sys.executable, str(runner), '--core', str(args.core), '--rom', str(args.rom),
                   '--elf', str(args.elf), '--nm', args.nm, '--output', str(output), '--sram-out', str(target)]
        if source:
            command += ['--sram-in', str(source)]
        if slot is not None:
            command += ['--save-slot', str(slot)]
        if expected is not None:
            command += ['--expect-save-slot', str(expected)]
        with (output/'run.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        result = json.loads((output/'result.json').read_text())
        after = target.read_bytes()
        if source:
            before = source.read_bytes()
            # Production scene entry uses $1000-$149F as mapper SRAM scratch.
            for i in range(0x8000):
                if 0x1000 <= i < 0x14A0:
                    continue
                if slot is not None and (i == 0x30 or 0x400*(slot+1) <= i < 0x400*(slot+1)+0x250):
                    continue
                assert after[i] == before[i], f'{name}: unrelated SRAM byte {i:04X} changed'
        results.append({'case': name, 'sram': result['sram'], 'play_ticks': result['play_ticks']})
        print(name+': OK', flush=True)
        return target

    previous = None
    for slot in range(3):
        previous = run(f'save_{slot}', previous, slot, slot-1 if slot else None)
    previous = run('reload_2', previous, expected=2)
    previous = run('overwrite_0', previous, slot=0, expected=2)
    previous = run('reload_overwrite_0', previous, expected=0)
    # Invalid signature must start a new game and clear only $0010-$1FFE.
    corrupted = bytearray(previous.read_bytes())
    corrupted[0x10] ^= 0x80
    damaged = args.output/'invalid_signature.bin'
    damaged.write_bytes(corrupted)
    cleared = run_invalid(args, runner, damaged)
    assert cleared[:0x10] == corrupted[:0x10]
    assert cleared[0x1FFF:] == corrupted[0x1FFF:]
    assert cleared[0x30] == 0
    assert cleared[0x400:0xE50] == bytes(0xA50)
    print('invalid_signature: OK', flush=True)
    (args.output/'result.json').write_text(json.dumps({'cycles': results, 'invalid_signature': 'passed'}, indent=2)+'\n')


def run_invalid(args, runner, damaged):
    output = args.output/'invalid_signature'
    output.mkdir(parents=True, exist_ok=True)
    target = output/'sram.bin'
    command = [sys.executable, str(runner), '--core', str(args.core), '--rom', str(args.rom),
               '--elf', str(args.elf), '--nm', args.nm, '--output', str(output),
               '--sram-in', str(damaged), '--sram-out', str(target)]
    with (output/'run.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = json.loads((output/'result.json').read_text())
    assert any(stage['state'] == '12' for stage in result['stages']), 'Bad signature did not enter new-game name entry'
    return target.read_bytes()


if __name__ == '__main__':
    main()
