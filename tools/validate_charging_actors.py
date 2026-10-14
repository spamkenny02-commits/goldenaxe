"""Compare live Z80/native3A/3B state machines; fixtures remain test-only."""
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
    comparisons = 0
    def record(t, state, direction=0, counter=0, remaining=32):
        e = bytearray(48)
        e[:5] = bytes([t, state, 6, 0x28, counter])
        e[8:10] = bytes.fromhex('1f8b' if state < 10 else 'af8b')
        e[10:14] = bytes([direction, 0, 2, 10 if state < 10 else 8])
        e[0x11], e[0x13], e[0x18], e[0x2c] = 80, 120, 32, remaining
        return e
    def run_one(md, name, frames, writes):
        out = ROOT/f"validation/{'md' if md else 'sms'}-charging-{name}{suffix}"
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'), max(frames),
                out, frames, PRESSES if md else [(200, 220, 0)]+PRESSES,
                ram_writes=writes, core_options=options)
        return out
    def pair(name, frames, sw, tw):
        return run_one(False, name, frames, sw), run_one(True, name, frames, tw)
    def actors(out, f, md):
        if md:
            raw = native(out, f)
            return raw[sy['world_actor_state']:sy['world_actor_state']+768]
        return (out/f'ram_{f:05}.bin').read_bytes()[0x600:0x900]
    def compare(a, b, frames, slots, label):
        nonlocal comparisons
        for f in sorted(frames):
            src, dst = actors(a, f, False), actors(b, f, True)
            for slot in slots:
                x, y = src[slot*48:(slot+1)*48], dst[slot*48:(slot+1)*48]
                assert x[:27]+x[29:] == y[:27]+y[29:], (
                    label, f, slot, [(n, p, q) for n, (p, q) in enumerate(zip(x, y)) if p != q])
                comparisons += 1
    cases = [record(t, s, d, c, r) for t in (0x3a, 0x3b)
             for s, c, r in [(2, 3, 32), (2, 0, 32), (6, 0, 32), (8, 3, 32),
                             (10, 0, 32), (12, 3, 32), (12, 0, 32), (12, 0, 1), (12, 0, 0)]
             for d in range(4)]
    sw, tw, frames = [], [], set()
    for batch in range(9):
        f = 3102+batch
        data = b''.join(cases[batch*8:batch*8+8])+bytes(384)
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536))]
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536))]
        frames.add(f)
    a, b = pair('matrix', frames, sw, tw)
    compare(a, b, frames, range(16), 'deterministic matrix')
    print('72 deterministic charging actor cases OK', flush=True)

    blocked_cases = [record(t, s, d, remaining=3) for t in (0x3a, 0x3b)
                     for s in (4, 8, 12) for d in range(4)]
    sw, tw, frames = [], [], set()
    for flag_index, flag in enumerate([0x20, 0x80]):
        tiles = bytes([0, flag])*768
        for batch in range(3):
            f = 3102+flag_index*3+batch
            data = b''.join(blocked_cases[batch*8:batch*8+8])+bytes(384)
            sw += [(f, 0x600, data), (f, 0x1600, tiles)]
            tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, tiles)]
            frames.add(f)
    a, b = pair('blocked', frames, sw, tw)
    compare(a, b, frames, range(16), 'terrain-blocked direction/walk/charge')
    print('48 blocked-terrain cases, charge budget preserved on obstacle OK', flush=True)

    fixtures, frames, sw = {}, set(), []
    targets = [(120, 32), (120, 144), (32, 80), (216, 80), (200, 32), (120, 80)]
    for i in range(192):
        f = 3102+i
        t, state = (0x3a, 0x3b)[i % 2], (4, 8)[(i//2) % 2]
        hx, hy = targets[(i//4) % len(targets)]
        data = bytes(record(t, state))+bytes(720)
        fixtures[f] = (t, state, hx, hy, data)
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536)),
               (f, 0x312, (hx<<8).to_bytes(2, 'little')), (f, 0x310, (hy<<8).to_bytes(2, 'little'))]
        frames.add(f)
    a = run_one(False, 'decisions', frames, sw)
    tw, decisions = [], []
    for f in sorted(frames):
        t, state, hx, hy, data = fixtures[f]
        expected = actors(a, f, False)[:48]
        aligned = (hx & 240) == 112 or (hy & 240) == 80
        if state == 4:
            seed = next(n for n in range(1, 65536) if random_word(n) & 3 == expected[10])
        else:
            seed = next(n for n in range(1, 65536)
                        if (4 if random_word(n) & 15 < 4 else
                            6 if random_word(n) & 15 < 10 or not aligned else 10) == expected[1])
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536)),
               (f, sy['randbase'], seed.to_bytes(2, 'big')),
               (f, sy['hero_x'], (hx<<8).to_bytes(2, 'big')), (f, sy['hero_y'], (hy<<8).to_bytes(2, 'big'))]
        decisions.append(dict(type=t, state=state, next_state=expected[1], direction=expected[10], hero=[hx, hy]))
    b = run_one(True, 'decisions', frames, tw)
    compare(a, b, frames, range(16), 'source-observed random decisions')
    assert {d['next_state'] for d in decisions if d['state'] == 8} == {4, 6, 10}
    assert {d['direction'] for d in decisions if d['next_state'] == 10} == {0, 1, 2, 3}
    print('192 source-observed choices, four charge directions and unaligned hero OK', flush=True)

    data = b''.join(record(t, 10, d, remaining=32) for t in (0x3a, 0x3b) for d in range(4))+bytes(384)
    frames = set(range(3102, 3392))
    a, b = pair('motion', frames,
                [(3102, 0x600, data), (3102, 0x1600, bytes(1536))],
                [(3102, sy['world_actor_state'], data), (3102, sy['sms_vram']+0x3800, bytes(1536))])
    ends = []
    for slot in range(8):
        end = next(f for f in sorted(frames) if actors(a, f, False)[slot*48+1] == 4)
        compare(a, b, range(3102, end+1), [slot], 'free charge until stop')
        ends.append(dict(slot=slot, stop_frame=end))
    print('8 free charges through original obstacle/boundary stops OK', flush=True)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  region=options['genesis_plus_gx_region_detect'], deterministic_cases=len(cases),
                  blocked_terrain_cases=48,
                  controlled_decisions=decisions, charge_stops=ends, record_comparisons=comparisons,
                  collision_descriptor_bytes_excluded=[27, 28], original_rng_stream_verified=False,
                  natural_gameplay_verified=False)
    (ROOT/f'validation/charging_actors{suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
