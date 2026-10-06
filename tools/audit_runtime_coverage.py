#!/usr/bin/env python3
"""Report dispatcher registration and remaining bridge/presentation gaps.

Registration counts do not prove behavior or rendering equivalence. The probe
runs the actual C dispatchers; no list of completed types is hardcoded here.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def words(name):
    return [int(v, 16) for v in re.findall(r'0x([0-9a-fA-F]{4})',
                                         (ROOT/'src'/name).read_text())]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, default=ROOT/'runtime_coverage_host_test')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    if not args.probe.exists():
        parser.exit(2, 'Build the registration probe with make runtime_coverage_host_test\n')
    probe = json.loads(subprocess.check_output([str(args.probe.resolve())], text=True))
    handlers = words('entity_handlers.inc')
    world = words('world_callbacks_512.inc')
    if len(handlers) != 128 or len(world) != 512:
        parser.exit(2, 'Unexpected entity/world table size\n')
    native_entities = set(probe['native_entity_types'])
    native_world = set(probe['native_world_targets'])
    remaining_entities = set(range(1, 128)) - native_entities
    remaining_world = sorted(set(world) - native_world)
    states=set(probe['native_main_states'])
    pending_states=sorted(set(range(0,0x18,2))-states)
    print(f'registered native main states: {len(states)} / 12')
    print('remaining main states: ' + ' '.join(f'{s:02X}' for s in pending_states))
    print(f'handler table entries: {len(handlers)}')
    print(f'registered high-level C entity types: {len(native_entities)} / 127')
    print(f'world callback entries: {len(world)}')
    done = sum(t in native_world for t in world)
    print(f'registered native/RET world callback entries: {done} / {len(world)}')
    print(f'world callback entries still on compatibility bridge: {len(world)-done} / {len(world)}')
    print(('remaining world targets: ' + ' '.join(f'{t:04X}' for t in remaining_world)).rstrip())
    calls = []
    for p in sorted((ROOT/'src').glob('*.c')):
        if p.name in ('recompiled.c','sms_compat.c'): continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if re.search(r'\b(?:gaw_recompiled_(?:call|world_call|entity_call)|gaw_sms_compat_indexed_call)\s*\(', line):
                calls.append(f'{p.relative_to(ROOT)}:{n}: {line.strip()}')
    print(f'remaining instruction-bridge call sites: {len(calls)}')
    for call in calls: print('  ' + call)
    stubs = []
    md = (ROOT/'md/src/platform_md.c').read_text()
    for name, body in re.findall(r'\b(gaw_platform_\w+)\([^)]*\)\s*\{([^{}]*)\}', md):
        body = re.sub(r'\(void\)\s*\w+\s*;', '', body).strip()
        if not body: stubs.append(name)
    print(f'unimplemented Mega Drive presentation hooks: {len(stubs)}')
    for name in stubs: print('  ' + name)
    print('Registration coverage is not full-game equivalence or console playability.')
    if args.require_complete and (remaining_entities or remaining_world or pending_states or calls or stubs):
        parser.exit(1, 'Full-decompilation/MD completion gate: NOT COMPLETE\n')

if __name__ == '__main__': main()
