"""Original41 terrain3F spawn and three explicitly controlled random choices."""
import contextlib
import hashlib
import io
import json
import re
import sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word


def main():
    suffix = '-pal' if '--pal' in sys.argv else ''
    options = {'genesis_plus_gx_region_detect': 'pal' if suffix else 'auto'}
    sy = {m[2].split('.lto_priv.')[0]: int(m[1], 16) & 65535
          for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
          if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    accepted, rejected = [], []
    for t in [0x41]:
        e = bytearray(768)
        e[0], e[2], e[3], e[4], e[0x18] = t, 6, 0x28, 3, 32
        data = bytes(e)
        for terrain in [0x3f, 3, 0x19, 0x57, 8]:
            label = f'{t:02x}-{terrain:02x}{suffix}'
            a, b = [ROOT/f'validation/{m}-ambusher41-spawn-{label}' for m in ['sms', 'md']]
            frames = set(range(3102, 3166)) if terrain == 0x3f else {3102}
            cells = bytes([terrain])*160
            sw = [w for f in sorted(frames) for w in
                  [(f, 0x600, data), (f, 0x1c00, cells), (f, 0x2f, b'\x07')]]
            with contextlib.redirect_stdout(io.StringIO()):
                run(ROOT/'input/original.sms', max(frames), a, frames, [(200, 220, 0)]+PRESSES,
                    ram_writes=sw, core_options=options)
            if terrain == 0x3f:
                match = None
                for f in sorted(frames):
                    expected = (a/f'ram_{f:05}.bin').read_bytes()[0x600:0x630]
                    if expected[1] != 2: continue
                    cell = ((expected[0x11]-16)&240) | (expected[0x13]>>4)
                    seed = next((n for n in range(1, 65536) if random_word(n)&127 == cell-16
                                 and random_word(random_word(n))&3 == expected[10]
                                 and random_word(random_word(random_word(n)))&15 == expected[4]-111), None)
                    if seed is not None:
                        match = f, seed
                        break
                assert match is not None, 'No representable three-choice source spawn observed'
                chosen, seed = match
            else:
                chosen, seed = 3102, 1
                expected = (a/'ram_03102.bin').read_bytes()[0x600:0x630]
                assert expected[1] == 0
            tw = [w for f in range(3102, chosen+1) for w in
                  [(f, sy['world_actor_state'], data), (f, sy['scratch']+0x800, cells),
                   (f, sy['vtimer'], (7).to_bytes(4, 'big')),
                   (f, sy['world_clock_shift'], bytes(4)),
                   (f, sy['randbase'], seed.to_bytes(2, 'big'))]]
            with contextlib.redirect_stdout(io.StringIO()):
                run(ROOT/'gaw-megadrive.bin', chosen, b, {chosen}, PRESSES,
                    ram_writes=tw, core_options=options)
            raw = native(b, chosen)
            actual = raw[sy['world_actor_state']:sy['world_actor_state']+48]
            assert actual[:27]+actual[29:] == expected[:27]+expected[29:], (
                label, [(n, x, y) for n, (x, y) in enumerate(zip(expected, actual)) if x != y])
            item = dict(type=t, terrain=terrain, source_frame=chosen, native_rng_and_clock_controlled=True)
            (accepted if terrain == 0x3f else rejected).append(item)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  region=options['genesis_plus_gx_region_detect'], accepted=accepted, rejected=rejected,
                  original_rng_stream_verified=False, collision_descriptor_bytes_excluded=[27, 28])
    (ROOT/f'validation/ambusher41_spawns{suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('1 three-choice appearance and4 terrain refusals OK', flush=True)


if __name__ == '__main__':
    main()
