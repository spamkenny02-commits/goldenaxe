"""Live SMS/MD comparison of walkers38/39 and parabolic projectile1F.

Fixtures are injected once per independent case, never linked into the ROM.
Only collision-list indices27/28, allocated by different renderers, are omitted.
"""
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
    def record(t, state, direction=0, counter=0):
        e = bytearray(48)
        e[0:5] = bytes([t, state, 6, 0x28, counter])
        e[8:10] = bytes.fromhex('e189')
        e[10:14] = bytes([direction, 0, 2, 16])
        e[0x11], e[0x13], e[0x18] = 80, 120, 30
        return e

    comparisons = 0
    def compare(a, b, frames, slots, label):
        nonlocal comparisons
        for f in sorted(frames):
            src = (a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900]
            raw = native(b, f)
            dst = raw[sy['world_actor_state']:sy['world_actor_state']+768]
            for slot in slots:
                x, y = src[slot*48:(slot+1)*48], dst[slot*48:(slot+1)*48]
                assert x[:27]+x[29:] == y[:27]+y[29:], (
                    label, f, slot, [(n, p, q) for n, (p, q) in enumerate(zip(x, y)) if p != q])
                comparisons += 1

    def pair(name, frames, sw, tw):
        a, b = [ROOT/f'validation/{machine}-bouncing-{name}{suffix}' for machine in ('sms', 'md')]
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'input/original.sms', max(frames), a, frames,
                [(200, 220, 0)]+PRESSES, ram_writes=sw, core_options=options)
            run(ROOT/'gaw-megadrive.bin', max(frames), b, frames,
                PRESSES, ram_writes=tw, core_options=options)
        return a, b

    cases = [record(t, state, direction, counter)
             for t in (0x38, 0x39)
             for state, counter in ((2, 0), (6, 0), (8, 3), (10, 3), (10, 0),
                                    (12, 0), (12, 3), (14, 0), (14, 3))
             for direction in range(4)]
    sw, tw, frames = [], [], set()
    for batch in range((len(cases)+7)//8):
        f = 3102+batch
        data = b''.join(cases[batch*8:batch*8+8]).ljust(768, b'\0')
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536))]
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536))]
        frames.add(f)
    a, b = pair('matrix', frames, sw, tw)
    compare(a, b, frames, range(16), 'walkers')
    print(f'{len(cases)} deterministic shooter cases OK', flush=True)

    # Observe the original R-driven choices, then control only the equivalent
    # native choice. This does not assert that the games share an RNG stream.
    sw, frames, fixtures = [], set(), {}
    for i in range(192):
        f = 3102+i
        t, state = (0x38, 0x39)[i % 2], (2, 4, 8)[(i//2) % 3]
        e = record(t, state)
        e[11] = 3 if state == 2 else 0
        data = bytes(e)+bytes(720)
        fixtures[f] = (t, state, data)
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536))]
        frames.add(f)
    a = ROOT/f'validation/sms-bouncing-decisions{suffix}'
    with contextlib.redirect_stdout(io.StringIO()):
        run(ROOT/'input/original.sms', max(frames), a, frames,
            [(200, 220, 0)]+PRESSES, ram_writes=sw, core_options=options)
    tw, decisions = [], []
    for f in sorted(frames):
        t, state, data = fixtures[f]
        expected = (a/f'ram_{f:05}.bin').read_bytes()[0x600:0x630]
        if state in (2, 4):
            seed = next(n for n in range(1, 65536) if random_word(n) & 3 == expected[10])
        else:
            seed = next(n for n in range(1, 65536)
                        if (4 if random_word(n) & 15 < 4 else
                            6 if random_word(n) & 15 < 14 else 10) == expected[1])
        tw += [(f, sy['world_actor_state'], data),
               (f, sy['sms_vram']+0x3800, bytes(1536)),
               (f, sy['randbase'], seed.to_bytes(2, 'big'))]
        decisions.append(dict(type=t, state=state, next_state=expected[1], direction=expected[10]))
    b = ROOT/f'validation/md-bouncing-decisions{suffix}'
    with contextlib.redirect_stdout(io.StringIO()):
        run(ROOT/'gaw-megadrive.bin', max(frames), b, frames, PRESSES, ram_writes=tw, core_options=options)
    compare(a, b, frames, range(16), 'controlled random choices')
    assert {d['next_state'] for d in decisions if d['state'] == 8} == {4, 6, 10}
    print('192 source-observed decisions, all three walk/pause/aim outcomes OK', flush=True)

    # Occupied auxiliary slots remain intact; source4965 also preserves stale
    # fractional coordinates in the first free record when emitting a shot.
    sw, tw, frames = [], [], set()
    for used in range(9):
        f = 3102+used
        data = bytearray(bytes(record(0x38, 10))+bytes(720))
        for slot in range(8, 16):
            if slot < 8+used:
                e = record(0x20, 2)
                e[6] = 255  # Freeze a valid actor without an invalid dispatch.
                data[slot*48:(slot+1)*48] = e
            else:
                data[slot*48+0x22], data[slot*48+0x26] = 37, 91
        sw.append((f, 0x600, bytes(data)))
        tw.append((f, sy['world_actor_state'], bytes(data)))
        frames.add(f)
    a, b = pair('pool', frames, sw, tw)
    compare(a, b, frames, range(16), 'transient pool')
    print('9 projectile-pool occupancy cases OK', flush=True)

    boundary_cases = []
    for x, y, counter in [(7, 80, 5), (8, 80, 5), (247, 80, 5), (248, 80, 5),
                          (120, 7, 5), (120, 8, 5), (120, 159, 5), (120, 160, 5),
                          (120, 80, 0), (120, 80, 1)]:
        e = record(0x1f, 6, counter=counter)
        e[0x13], e[0x11] = x, y
        boundary_cases.append(e)
    # Direct states2/4, a height underflow and a fractional ground carry.
    for state, height, momentum in [(2, 0, 0), (4, 0, 0), (6, 1, 0xffff), (6, 511, 1)]:
        e = record(0x1f, state, counter=5)
        for offset, word in [(0x22, 0x78ff), (0x26, 0x50ff), (0x20, 2),
                             (0x24, 3), (0x28, momentum), (0x2a, height), (0x2e, 0xffd8)]:
            e[offset:offset+2] = word.to_bytes(2, 'little')
        boundary_cases.append(e)
    sw, tw, frames = [], [], set()
    for i, e in enumerate(boundary_cases):
        f = 3102+i
        data = bytes(384)+bytes(e)+bytes(336)
        sw.append((f, 0x600, data))
        tw.append((f, sy['world_actor_state'], data))
        frames.add(f)
    a, b = pair('bounds', frames, sw, tw)
    compare(a, b, frames, [8], 'bounds and ballistic arithmetic')
    print('14 boundary, state-entry and fixed-point arithmetic cases OK', flush=True)

    # Eight octants in parallel; each actor begins at a different origin.
    origins = [(96, 120), (64, 120), (96, 40), (64, 40),
               (160, 120), (192, 120), (160, 40), (192, 40)]
    data = bytearray(768)
    for slot, (x, y) in enumerate(origins, 8):
        e = record(0x1f, 0)
        e[0x13], e[0x11] = x, y
        e[0x22], e[0x26] = 37, 91  # Fractional ground positions must survive initialization.
        data[slot*48:(slot+1)*48] = e
    f = 3102
    frames = set(range(f, f+150))
    sw = [(f, 0x600, bytes(data)), (f, 0x312, (128<<8).to_bytes(2, 'little')),
          (f, 0x310, (80<<8).to_bytes(2, 'little'))]
    tw = [(f, sy['world_actor_state'], bytes(data)), (f, sy['hero_x'], (128<<8).to_bytes(2, 'big')),
          (f, sy['hero_y'], (80<<8).to_bytes(2, 'big'))]
    a, b = pair('octants', frames, sw, tw)
    compare(a, b, frames, range(8, 16), 'projectile1F')
    source = (ROOT/'input/original.sms').read_bytes()
    vectors = [source[0x436c+n*4:0x4370+n*4] for n in range(8)]
    first = (a/'ram_03102.bin').read_bytes()
    actual_octants = []
    for slot in range(8, 16):
        e = first[0x600+slot*48:0x630+slot*48]
        actual_octants.append(vectors.index(e[0x16:0x18]+e[0x14:0x16]))
    assert set(actual_octants) == set(range(8)), actual_octants
    bounces, clears = [], []
    for slot in range(8, 16):
        previous = None
        for f in sorted(frames):
            e = (a/f'ram_{f:05}.bin').read_bytes()[0x600+slot*48:0x630+slot*48]
            if previous is not None:
                if previous[1] == 4 and e[1] == 6:
                    bounces.append(dict(slot=slot, frame=f))
                if previous[0] and not e[0]:
                    clears.append(dict(slot=slot, frame=f))
            previous = e
    assert bounces, 'No repeated bounce exercised'
    assert len(clears) == 8, ('Projectile lifetimes not fully exercised', clears)
    print('8 octants, repeated hops and culls OK', flush=True)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  deterministic_shooter_cases=len(cases), record_comparisons=comparisons,
                  controlled_decisions=decisions, projectile_pool_cases=9,
                  boundary_and_arithmetic_cases=len(boundary_cases),
                  octants=origins, actual_octants=actual_octants,
                  free_trajectory_frames=150, bounces=bounces, clears=clears,
                  collision_descriptor_bytes_excluded=[27, 28],
                  region=options['genesis_plus_gx_region_detect'],
                  original_rng_stream_verified=False, natural_gameplay_verified=False)
    (ROOT/f'validation/bouncing_shooters{suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
