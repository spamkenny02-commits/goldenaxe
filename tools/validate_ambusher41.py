"""Live41 reveal, partial/full two-shot allocation, and1D ballistic flight."""
import hashlib
import json
import sys
from actor_reference import ROOT
from actor_pair_validation import ActorPair
from validate_actor_ai import random_word


def main():
    pair = ActorPair('ambusher41', '--pal' in sys.argv)
    sy = pair.sy
    def record(t, state, direction=0, counter=0):
        e = bytearray(48)
        e[:5] = bytes([t, state, 6, 0x2b, counter])
        e[8:10] = bytes.fromhex('3090')
        e[10:14] = bytes([direction, 0, 2, 4])
        e[0x11], e[0x13], e[0x18] = 80, 120, 32
        return e
    sw, tw, frames = [], [], set()
    cases = [record(0x41, s, d, c) for s, c in [(0, 3), (2, 0), (2, 3), (4, 3)] for d in range(4)]
    for batch in range(2):
        f = 3102+batch
        data = b''.join(cases[batch*8:batch*8+8])+bytes(384)
        sw += [(f, 0x600, data), (f, 0x1c00, bytes(160))]
        tw += [(f, sy['world_actor_state'], data), (f, sy['scratch']+0x800, bytes(160))]
        frames.add(f)
    pair.compare(pair.execute(False, 'matrix', frames, sw), pair.execute(True, 'matrix', frames, tw), frames, range(16), 'matrix')
    print('16 deterministic41 cases OK', flush=True)

    sw, frames, fixtures = [], set(), {}
    for used in range(9):
        f = 3102+used
        data = bytearray(bytes(record(0x41, 4))+bytes(720))
        for slot in range(8, 16):
            if slot < 8+used:
                e = record(0x20, 2)
                e[3], e[6] = 0x28, 255
                data[slot*48:(slot+1)*48] = e
            else:
                data[slot*48+0x22], data[slot*48+0x26] = 37, 91
        fixtures[f] = bytes(data)
        sw.append((f, 0x600, bytes(data)))
        frames.add(f)
    a = pair.execute(False, 'pool', frames, sw)
    tw, pools = [], []
    for used, f in enumerate(sorted(frames)):
        tw.append((f, sy['world_actor_state'], fixtures[f]))
        expected = a[f][:48]
        if used <= 6:
            seed = next(n for n in range(1, 65536) if random_word(n)&15 == expected[4]-111)
            tw.append((f, sy['randbase'], seed.to_bytes(2, 'big')))
        else:
            assert expected[4] == 0
        births = [slot for slot in range(8, 16) if a[f][slot*48] == 0x1d]
        assert len(births) == min(2, 8-used)
        pools.append(dict(occupied=used, births=births, parent_counter=expected[4]))
    b = pair.execute(True, 'pool', frames, tw)
    pair.compare(a, b, frames, range(16), 'two-shot pool exhaustion')
    print('9 pool cases, opposite shot order and partial-allocation path OK', flush=True)

    data = bytearray(768)
    for slot, (direction, counter) in enumerate([(0, 0), (1, 0), (0, 3), (1, 3)], 8):
        e = record(0x1d, 0, direction, counter)
        e[0x22], e[0x26] = 37, 91
        e[0x14:0x18] = bytes([1, 0, 2, 0])
        data[slot*48:(slot+1)*48] = e
    frames = set(range(3102, 3202))
    a = pair.execute(False, 'lob-flight', frames, [(3102, 0x600, bytes(data))])
    b = pair.execute(True, 'lob-flight', frames, [(3102, sy['world_actor_state'], bytes(data))])
    pair.compare(a, b, frames, range(8, 12), '1D lob flight and landing')
    landings = [dict(slot=s, frame=next(f for f in sorted(frames) if not a[f][s*48])) for s in range(8, 12)]
    print('4 lob1D trajectories, retained fractions/common motion and landing culls OK', flush=True)

    # The new1B has a terrain-bit80 kill;1A deliberately retains its own behavior.
    sw, tw, frames = [], [], set()
    for i, (t, flag) in enumerate((t, flag) for t in [0x1a, 0x1b] for flag in [0, 0x20, 0x40, 0x80, 0xe0]):
        f = 3102+i
        e = record(t, 2, counter=3)
        data = bytes(384)+bytes(e)+bytes(336)
        tiles = bytes([0, flag])*768
        sw += [(f, 0x600, data), (f, 0x1600, tiles)]
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, tiles)]
        frames.add(f)
    a, b = pair.execute(False, 'terrain1b', frames, sw), pair.execute(True, 'terrain1b', frames, tw)
    pair.compare(a, b, frames, [8], '1B terrain distinction')
    kills = sum(not a[f][384] for f in frames)
    assert kills == 2
    print('10 terrain cases prove1B bit80 cull and unchanged1A behavior OK', flush=True)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  region=pair.options['genesis_plus_gx_region_detect'], deterministic_cases=16,
                  pool_cases=pools, lob_flight_frames=100, lob_landings=landings,
                  terrain_cases=10, terrain_kills=kills, record_comparisons=pair.comparisons,
                  collision_descriptor_bytes_excluded=[27, 28], original_rng_stream_verified=False,
                  natural_gameplay_verified=False)
    (ROOT/f'validation/ambusher41{pair.suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
