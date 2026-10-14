"""Live3D/3E and1A comparisons; fixtures explicitly clear source overflow status."""
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
    def record(t, state, d=0, counter=0, pose=0):
        e = bytearray(48)
        e[:5] = bytes([t, state, 6, 0x28, counter])
        e[8:10] = bytes.fromhex('aa8c')
        e[10:14] = bytes([d, pose, 2, 10])
        e[0x11], e[0x13], e[0x18] = 80, 120, 32
        return e
    def execute(md, label, frames, writes):
        samples = {}
        base = sy['world_actor_state'] if md else 0x600
        def observe(f, ram):
            if f in frames:
                samples[f] = bytes(ram[(base+n)^1] for n in range(768)) if md else ram[base:base+768]
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'), max(frames),
                ROOT/f"validation/{'md' if md else 'sms'}-pursuit-{label}{suffix}", set(),
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
    cases = [record(t, s, d, c, pose) for t in [0x3d, 0x3e]
             for s, c, pose in [(2, 0, 2), (6, 0, 0), (8, 3, 0), (10, 3, 0)] for d in range(4)]
    sw, tw, frames = [], [], set()
    for batch in range(4):
        f = 3102+batch
        data = b''.join(cases[batch*8:batch*8+8])+bytes(384)
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536)), (f, 0x1b, b'\0')]
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536))]
        frames.add(f)
    compare(execute(False, 'matrix', frames, sw), execute(True, 'matrix', frames, tw), frames, range(16), 'matrix')
    print('32 deterministic3D/3E cases OK', flush=True)

    sw, tw, frames = [], [], set()
    blocked = [record(t, s, d) for t in [0x3d, 0x3e] for s in [4, 8, 10] for d in range(4)]
    for fi, flag in enumerate([0x20, 0x80]):
        tiles = bytes([0, flag])*768
        for batch in range(3):
            f = 3102+fi*3+batch
            data = b''.join(blocked[batch*8:batch*8+8])+bytes(384)
            sw += [(f, 0x600, data), (f, 0x1600, tiles)]
            tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, tiles)]
            frames.add(f)
    compare(execute(False, 'blocked', frames, sw), execute(True, 'blocked', frames, tw), frames, range(16), 'blocked')
    print('48 blocked-terrain cases OK', flush=True)

    targets = [(120, 32), (120, 144), (32, 80), (216, 80), (200, 32), (120, 80)]
    fixtures, sw, frames = {}, [], set()
    for i in range(192):
        f, t, state = 3102+i, [0x3d, 0x3e][i % 2], [2, 4, 8, 10][(i//2) % 4]
        hx, hy = targets[(i//8) % 6]
        data = bytes(record(t, state, pose=3 if state == 2 else 0))+bytes(720)
        fixtures[f] = t, state, hx, hy, data
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536)), (f, 0x1b, b'\0'),
               (f, 0x312, (hx<<8).to_bytes(2, 'little')), (f, 0x310, (hy<<8).to_bytes(2, 'little'))]
        frames.add(f)
    a = execute(False, 'decisions', frames, sw)
    tw, decisions = [], []
    for f in sorted(frames):
        t, state, hx, hy, data = fixtures[f]
        e = a[f][:48]
        aligned = (hx&240) == 112 or (hy&240) == 80
        if state in [2, 4]:
            valid = lambda q: q&3 == e[10]
        elif state == 8:
            valid = lambda q: (4 if q&15 < 4 else 6 if q&15 < 10 or not aligned else 10) == e[1]
        else:
            valid = lambda q: (4 if q&15 < 4 else 6) == e[1]
        seed = next(n for n in range(1, 65536) if valid(random_word(n)))
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536)),
               (f, sy['hero_x'], (hx<<8).to_bytes(2, 'big')), (f, sy['hero_y'], (hy<<8).to_bytes(2, 'big')),
               (f, sy['randbase'], seed.to_bytes(2, 'big'))]
        decisions.append(dict(type=t, state=state, next_state=e[1], direction=e[10], shot=a[f][384] == 0x1a))
    b = execute(True, 'decisions', frames, tw)
    compare(a, b, frames, range(16), 'controlled choices and emissions')
    assert {d['next_state'] for d in decisions if d['state'] == 8} == {4, 6, 10}
    assert any(d['shot'] for d in decisions)
    print('192 original-observed decisions and emissions OK', flush=True)

    # Four independently initialized straight shots evolve freely until cleared.
    data = bytes(384)+b''.join(record(0x1a, 0, d) for d in range(4))+bytes(192)
    frames = set(range(3102, 3234))
    a = execute(False, 'flight', frames, [(3102, 0x600, data)])
    b = execute(True, 'flight', frames, [(3102, sy['world_actor_state'], data)])
    compare(a, b, frames, range(8, 12), '1A free flight')
    deaths = [dict(slot=s, frame=next(f for f in sorted(frames) if not a[f][s*48])) for s in range(8, 12)]
    print('4 straight1A trajectories through original culls OK', flush=True)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  region=options['genesis_plus_gx_region_detect'], deterministic_cases=32, blocked_cases=48,
                  controlled_decisions=decisions, projectile_frames=132, projectile_culls=deaths,
                  record_comparisons=comparisons, collision_descriptor_bytes_excluded=[27, 28],
                  source_sprite_overflow_status_cleared_in_decision_fixtures=True,
                  sprite_overflow_suppression_verified=False, original_rng_stream_verified=False,
                  natural_gameplay_verified=False)
    (ROOT/f'validation/pursuit_shooters{suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
