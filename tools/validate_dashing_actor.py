"""Live-core3C comparisons with test-only fixtures, collected directly from RAM."""
import contextlib
import hashlib
import io
import json
import re
import sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_actor_ai import random_word


def main():
    suffix = '-pal' if '--pal' in sys.argv else ''
    options = {'genesis_plus_gx_region_detect': 'pal' if suffix else 'auto'}
    sy = {m[2].split('.lto_priv.')[0]: int(m[1], 16) & 65535
          for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
          if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    comparisons = 0
    def record(state, direction=0, counter=0, pose=0, x=120, y=80):
        e = bytearray(48)
        e[:5] = bytes([0x3c, state, 6, 0x28, counter])
        e[8:10] = bytes.fromhex('ef8b')
        e[10:14] = bytes([direction, pose, 2, 10])
        e[0x11], e[0x13], e[0x18] = y, x, 32
        return e
    def run_one(md, label, frames, writes):
        samples = {}
        base = sy['world_actor_state'] if md else 0x600
        def observe(f, ram):
            if f not in frames:
                return
            samples[f] = bytes(ram[(base+n)^1] for n in range(768)) if md else ram[base:base+768]
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'), max(frames),
                ROOT/f"validation/{'md' if md else 'sms'}-dashing-{label}{suffix}", set(),
                PRESSES if md else [(200, 220, 0)]+PRESSES, ram_writes=writes,
                ram_observer=observe, core_options=options)
        assert set(samples) == set(frames)
        return samples
    def compare(a, b, frames, slots, label):
        nonlocal comparisons
        for f in sorted(frames):
            for slot in slots:
                x, y = a[f][slot*48:(slot+1)*48], b[f][slot*48:(slot+1)*48]
                assert x[:27]+x[29:] == y[:27]+y[29:], (
                    label, f, slot, [(n, p, q) for n, (p, q) in enumerate(zip(x, y)) if p != q])
                comparisons += 1
    cases = [record(s, d, c, pose) for s, c, pose in
             [(0, 3, 0), (2, 0, 2), (6, 0, 0), (8, 3, 0),
              (10, 3, 0), (10, 0, 0), (12, 0, 0), (14, 3, 0)] for d in range(4)]
    sw, tw, frames = [], [], set()
    for batch in range(4):
        f = 3102+batch
        data = b''.join(cases[batch*8:batch*8+8])+bytes(384)
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536))]
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536))]
        frames.add(f)
    a, b = run_one(False, 'matrix', frames, sw), run_one(True, 'matrix', frames, tw)
    compare(a, b, frames, range(16), 'deterministic matrix')
    print('32 deterministic3C cases OK', flush=True)

    frames, sw, fixtures = set(), [], {}
    for i in range(192):
        f, state = 3102+i, (2, 4, 8)[i % 3]
        data = bytes(record(state, pose=3 if state == 2 else 0))+bytes(720)
        fixtures[f] = (state, data)
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536))]
        frames.add(f)
    a = run_one(False, 'decisions', frames, sw)
    tw, decisions = [], []
    for f in sorted(frames):
        state, data = fixtures[f]
        expected = a[f][:48]
        if state in (2, 4):
            seed = next(n for n in range(1, 65536) if random_word(n)&3 == expected[10])
        else:
            seed = next(n for n in range(1, 65536)
                        if (4 if random_word(n)&15 < 2 else 10 if random_word(n)&15 == 8 else 6) == expected[1])
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536)),
               (f, sy['randbase'], seed.to_bytes(2, 'big'))]
        decisions.append(dict(state=state, next_state=expected[1], direction=expected[10]))
    b = run_one(True, 'decisions', frames, tw)
    compare(a, b, frames, range(16), 'source-observed random choices')
    assert {d['next_state'] for d in decisions if d['state'] == 8} == {4, 6, 10}
    print('192 source-observed emergence/walk/dash decisions OK', flush=True)

    targets = [(120, 16), (120, 144), (48, 80), (208, 80),
               (48, 16), (208, 16), (88, 144), (208, 144), (120, 80), (116, 76), (124, 84)]
    trajectories = []
    for i, (hx, hy) in enumerate(targets):
        frames = set(range(3102, 3212))
        data = bytes(record(12))+bytes(720)
        sw = [(3102, 0x600, data), (3102, 0x312, (hx<<8).to_bytes(2, 'little')),
              (3102, 0x310, (hy<<8).to_bytes(2, 'little'))]
        a = run_one(False, f'flight-{i}', frames, sw)
        hidden = next(f for f in sorted(frames) if a[f][1] == 0)
        # Control only the source-observed hidden-delay choice at its real event.
        seed = next(n for n in range(1, 65536) if random_word(n)&15 == a[hidden][4]-112)
        tw = [(3102, sy['world_actor_state'], data),
              (3102, sy['hero_x'], (hx<<8).to_bytes(2, 'big')),
              (3102, sy['hero_y'], (hy<<8).to_bytes(2, 'big')),
              (hidden, sy['randbase'], seed.to_bytes(2, 'big'))]
        b = run_one(True, f'flight-{i}', frames, tw)
        compare(a, b, frames, [0], 'free aimed dash and hidden countdown')
        octant = (0 if hy < 80 else 2) | (4 if hx < 120 else 0)
        if abs(hy-80) < abs(hx-120):
            octant += 1
        trajectories.append(dict(hero=[hx, hy], octant=octant, frames=110, hidden_frame=hidden,
                                 hidden_counter=a[hidden][4], native_delay_choice_controlled=True))
    assert {t['octant'] for t in trajectories} == set(range(8))
    print('11 free trajectories cover all8 octants, ties, zero vector and hidden countdowns OK', flush=True)

    # All screen bounds and the lifetime-zero path execute the same reset.
    boundaries = [(7, 80, 3), (8, 80, 3), (247, 80, 3), (248, 80, 3),
                  (120, 7, 3), (120, 8, 3), (120, 151, 3), (120, 152, 3), (120, 80, 0)]
    frames, sw, fixtures = set(), [], {}
    for i, (x, y, counter) in enumerate(boundaries):
        f = 3102+i
        data = bytes(record(14, counter=counter, x=x, y=y))+bytes(720)
        fixtures[f] = data
        sw.append((f, 0x600, data))
        frames.add(f)
    a = run_one(False, 'bounds', frames, sw)
    tw, resets = [], []
    for f in sorted(frames):
        tw.append((f, sy['world_actor_state'], fixtures[f]))
        if a[f][1] == 0:
            seed = next(n for n in range(1, 65536) if random_word(n)&15 == a[f][4]-112)
            tw.append((f, sy['randbase'], seed.to_bytes(2, 'big')))
            resets.append(f)
    b = run_one(True, 'bounds', frames, tw)
    compare(a, b, frames, [0], 'bounds/lifetime reset')
    assert len(resets) == 5
    print('9 boundary/lifetime cases OK', flush=True)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  region=options['genesis_plus_gx_region_detect'], deterministic_cases=32,
                  controlled_decisions=decisions, trajectories=trajectories, boundary_cases=9,
                  record_comparisons=comparisons, collision_descriptor_bytes_excluded=[27, 28],
                  original_rng_stream_verified=False, natural_gameplay_verified=False)
    (ROOT/f'validation/dashing_actor{suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
