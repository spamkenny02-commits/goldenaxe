"""Live42 sine arithmetic, firing states and1C eight-segment re-aiming."""
import hashlib
import json
import sys
from actor_reference import ROOT
from actor_pair_validation import ActorPair
from validate_actor_ai import random_word


def main():
    pair = ActorPair('orbit42', '--pal' in sys.argv)
    sy = pair.sy
    original = (ROOT/'input/original.sms').read_bytes()
    def record(t, state, counter=0, pose=0):
        e = bytearray(48)
        e[:5] = bytes([t, state, 6, 0x28, counter])
        e[8:10] = bytes.fromhex('428e')
        e[11:14] = bytes([pose, 2, 7])
        e[0x11], e[0x13], e[0x18] = 81, 128, 64
        e[0x21:0x26] = bytes([11, 22, 33, 44, 55])
        e[0x26], e[0x28] = 128, 81
        return e
    def seed_for(attack):
        return next(n for n in range(1, 65536) if (random_word(n)&127 == 127) == attack)
    cases = [record(0x42, s, c, p) for s, c, p in
             [(0, 0, 0), (2, 0, 2), (2, 0, 3), (6, 3, 0), (6, 0, 0), (8, 3, 0), (8, 0, 0)]]
    sw, tw, frames = [], [], set()
    for i, e in enumerate(cases):
        f = 3102+i
        data = bytes(e)+bytes(720)
        sw.append((f, 0x600, data))
        tw.append((f, sy['world_actor_state'], data))
        frames.add(f)
    pair.compare(pair.execute(False, 'matrix', frames, sw), pair.execute(True, 'matrix', frames, tw), frames, range(16), 'matrix')
    print('7 deterministic42 transitions and emitted1C records OK', flush=True)

    sw, frames, fixtures = [], set(), {}
    amplitudes = [(0, 0), (95, 55), (96, 56), (255, 255)]
    for i in range(1024):
        f = 3102+i
        e = record(0x42, 4)
        e[0x29] = i&255
        e[0x2a], e[0x2b] = amplitudes[i//256]
        data = bytes(e)+bytes(720)
        fixtures[f] = data
        sw.append((f, 0x600, data))
        frames.add(f)
    a = pair.execute(False, 'sine-grid', frames, sw)
    tw, attacks = [], []
    for f in sorted(frames):
        attack = a[f][1] == 6
        tw += [(f, sy['world_actor_state'], fixtures[f]),
               (f, sy['randbase'], seed_for(attack).to_bytes(2, 'big'))]
        if attack: attacks.append(f)
    pair.compare(a, pair.execute(True, 'sine-grid', frames, tw), frames, range(16), 'sine/phase/amplitude grid')
    assert attacks
    print('1024 source sine/phase/amplitude cases, including wrap and saturation OK', flush=True)

    # Find actual original attacks for the asymmetric facing thresholds.
    sw, frames, fixtures = [], set(), {}
    targets = [128, 129, 127, 81, 80, 16]
    for i in range(3072):
        f, hx = 3102+i, targets[i % len(targets)]
        e = record(0x42, 4)  # amplitude0, phase0 -> after growth X128
        data = bytes(e)+bytes(720)
        fixtures[f] = (hx, data)
        sw += [(f, 0x600, data), (f, 0x312, (hx<<8).to_bytes(2, 'little'))]
        frames.add(f)
    a = pair.execute(False, 'attack-facing', frames, sw)
    tw, facing_cases = [], []
    for f in sorted(frames):
        hx, data = fixtures[f]
        attack = a[f][1] == 6
        tw += [(f, sy['world_actor_state'], data), (f, sy['hero_x'], (hx<<8).to_bytes(2, 'big')),
               (f, sy['randbase'], seed_for(attack).to_bytes(2, 'big'))]
        if attack: facing_cases.append(dict(hero_x=hx, actor_x=a[f][0x13], direction=a[f][10]))
    pair.compare(a, pair.execute(True, 'attack-facing', frames, tw), frames, range(16), 'attack facing')
    assert {c['direction'] for c in facing_cases} == {0, 2, 3}, facing_cases
    print('3072 source-observed attack-facing samples, directions0/2/3 OK', flush=True)

    targets = [(160, 16), (192, 48), (160, 144), (192, 112),
               (96, 16), (64, 48), (96, 144), (64, 112)]
    sw, tw, frames = [], [], set()
    for i, (hx, hy) in enumerate(targets):
        f = 3102+i
        e = record(0x1c, 0)
        e[0x11] = 100
        data = bytes(384)+bytes(e)+bytes(336)
        sw += [(f, 0x600, data), (f, 0x312, (hx<<8).to_bytes(2, 'little')), (f, 0x310, (hy<<8).to_bytes(2, 'little'))]
        tw += [(f, sy['world_actor_state'], data), (f, sy['hero_x'], (hx<<8).to_bytes(2, 'big')), (f, sy['hero_y'], (hy<<8).to_bytes(2, 'big'))]
        frames.add(f)
    a, b = pair.execute(False, 'aim1c', frames, sw), pair.execute(True, 'aim1c', frames, tw)
    pair.compare(a, b, frames, [8], 'all eight1C octants')
    vectors = [original[0x4162+i*4:0x4166+i*4] for i in range(8)]
    octants = [vectors.index(a[f][384+0x16:384+0x18]+a[f][384+0x14:384+0x16]) for f in sorted(frames)]
    assert set(octants) == set(range(8)), octants

    e = record(0x1c, 0)
    e[0x11] = 100
    data = bytes(384)+bytes(e)+bytes(336)
    frames = set(range(3102, 3253))
    sw, tw = [(3102, 0x600, data)], [(3102, sy['world_actor_state'], data)]
    targets = [(240, 144), (16, 16), (240, 16), (16, 144)]
    for f in sorted(frames):
        hx, hy = targets[((f-3102)//17) % 4]
        sw += [(f, 0x312, (hx<<8).to_bytes(2, 'little')), (f, 0x310, (hy<<8).to_bytes(2, 'little'))]
        tw += [(f, sy['hero_x'], (hx<<8).to_bytes(2, 'big')), (f, sy['hero_y'], (hy<<8).to_bytes(2, 'big'))]
    a, b = pair.execute(False, 'homing-cycle', frames, sw), pair.execute(True, 'homing-cycle', frames, tw)
    pair.compare(a, b, frames, [8], 'eight homing segments with moving hero')
    starts = [f for f in sorted(frames) if a[f][384] and a[f][385] == 4 and a[f][388] == 15]
    clear = next(f for f in sorted(frames) if not a[f][384])
    assert starts == [3102+17*n for n in range(8)] and clear == 3237, (starts, clear)
    print('8 initial octants and full8-segment1C homing cycle with moving target OK', flush=True)
    guards = [(7, 80, 0, 8), (8, 80, 0, 8), (247, 80, 0, 8), (248, 80, 0, 8),
              (128, 7, 0, 8), (128, 8, 0, 8), (128, 159, 0, 8), (128, 160, 0, 8),
              (7, 160, 3, 8), (128, 80, 0, 1), (128, 80, 0, 0), (128, 80, 0, 8)]
    sw, tw, frames = [], [], set()
    for i, (x, y, counter, remaining) in enumerate(guards):
        f = 3102+i
        e = record(0x1c, 4, counter)
        e[0x13], e[0x11], e[0x20] = x, y, remaining
        data = bytes(384)+bytes(e)+bytes(336)
        sw.append((f, 0x600, data))
        tw.append((f, sy['world_actor_state'], data))
        frames.add(f)
    a, b = pair.execute(False, 'homing-guards', frames, sw), pair.execute(True, 'homing-guards', frames, tw)
    pair.compare(a, b, frames, [8], 'homing bounds only at segment boundaries')
    assert a[3110][384] == 0x1c and a[3110][388] == 2
    assert not a[3111][384] and a[3112][384+0x20] == 255
    print('12 segment-boundary/lifetime guards, including delayed bounds test and budget wrap OK', flush=True)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(original).hexdigest(), region=pair.options['genesis_plus_gx_region_detect'],
                  deterministic_cases=7, sine_cases=1024, observed_orbit_attack_frames=attacks,
                  facing_samples=3072, facing_attack_cases=facing_cases, projectile_octants=octants,
                  segment_starts=starts, projectile_clear_frame=clear, record_comparisons=pair.comparisons,
                  homing_guard_cases=len(guards),
                  collision_descriptor_bytes_excluded=[27, 28], native_attack_rng_choice_controlled=True,
                  source_rng_stream_verified=False, moving_target_is_explicit_ram_fixture=True,
                  natural_gameplay_verified=False)
    (ROOT/f'validation/orbit_actor{pair.suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
