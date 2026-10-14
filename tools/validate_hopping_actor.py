"""Live3F emergence, walking, jumping, four-hop sequence and retreat."""
import hashlib
import json
import sys
from actor_reference import ROOT
from actor_pair_validation import ActorPair
from validate_actor_ai import random_word


def main():
    pair = ActorPair('hopping', '--pal' in sys.argv)
    sy = pair.sy
    source = (ROOT/'input/original.sms').read_bytes()
    vectors = [source[0x8ca3+i*8:0x8cab+i*8] for i in range(8)]
    def record(state, direction=0, counter=0, height=0, remaining=4):
        e = bytearray(48)
        e[:5] = bytes([0x3f, state, 6, 0x2b if state == 14 else 0x28, counter])
        e[8:10] = bytes.fromhex('888d')
        e[10:14] = bytes([direction, 0, 2, 10])
        e[0x11], e[0x13], e[0x18], e[0x2c] = 80, 120, 32, remaining
        e[0x22:0x24], e[0x26:0x28] = bytes([37, 120]), bytes([91, 80])
        e[0x2a:0x2c], e[0x28:0x2a], e[0x2e:0x30] = height.to_bytes(2, 'little'), b'\xff\xff', b'\xe0\xff'
        return e
    def seed_for(mask, value):
        return next(n for n in range(1, 65536) if random_word(n)&mask == value)
    cases = [record(s, d, c, h, r) for s, c, h, r in
             [(0, 3, 0, 4), (2, 3, 0, 4), (6, 0, 0, 4), (8, 3, 0, 4), (10, 3, 0, 4),
              (12, 0, 1, 4), (12, 0, 0, 4), (12, 0, 0, 1), (14, 3, 0, 4)] for d in range(4)]
    sw, tw, frames = [], [], set()
    for batch in range(5):
        f = 3102+batch
        data = b''.join(cases[batch*8:batch*8+8]).ljust(768, b'\0')
        sw.append((f, 0x600, data))
        tw.append((f, sy['world_actor_state'], data))
        frames.add(f)
    pair.compare(pair.execute(False, 'matrix', frames, sw), pair.execute(True, 'matrix', frames, tw), frames, range(16), 'matrix')
    print('36 deterministic3F state/direction/arithmetic cases OK', flush=True)

    sw, frames, fixtures = [], set(), {}
    for i in range(384):
        f, state = 3102+i, [2, 4, 8, 10, 14, 8, 8, 8][i % 8]
        data = bytes(record(state))+bytes(720)
        fixtures[f] = (state, data)
        sw += [(f, 0x600, data), (f, 0x1600, bytes(1536))]
        frames.add(f)
    a = pair.execute(False, 'decisions', frames, sw)
    tw, decisions = [], []
    for f in sorted(frames):
        state, data = fixtures[f]
        e = a[f][:48]
        if state in [2, 4]:
            seed = seed_for(3, e[10])
        elif state == 8:
            seed = next(n for n in range(1, 65536)
                        if (4 if random_word(n)&15 < 2 else 10 if random_word(n)&15 == 8 else 6) == e[1])
        elif state == 10:
            index = next(i for i, v in enumerate(vectors) if v[:4] == e[0x20:0x22]+e[0x24:0x26])
            seed = seed_for(7, index)
        else:
            seed = seed_for(15, e[4]-111)
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, bytes(1536)),
               (f, sy['randbase'], seed.to_bytes(2, 'big'))]
        decisions.append(dict(state=state, next_state=e[1], direction=e[10]))
    b = pair.execute(True, 'decisions', frames, tw)
    pair.compare(a, b, frames, range(16), 'source-observed random choices')
    assert {d['next_state'] for d in decisions if d['state'] == 8} == {4, 6, 10}, sorted({d['next_state'] for d in decisions if d['state'] == 8})
    print('384 source-observed movement/jump/retreat choices OK', flush=True)

    sw, frames, fixtures = [], set(), {}
    guards = [(120, 48, 0), (120, 128, 0), (40, 80, 0), (216, 80, 0),
              (120, 80, 0x20), (120, 80, 0x40), (120, 80, 0x80), (120, 80, 0xe0)]
    for i in range(128):
        f = 3102+i
        x, y, flag = guards[i % len(guards)]
        e = record(10)
        e[0x23], e[0x27] = x, y
        data, tiles = bytes(e)+bytes(720), bytes([0, flag])*768
        fixtures[f] = (x, y, flag, data, tiles)
        sw += [(f, 0x600, data), (f, 0x1600, tiles)]
        frames.add(f)
    a = pair.execute(False, 'jump-guards', frames, sw)
    tw, guard_rejections = [], 0
    for f in sorted(frames):
        x, y, flag, data, tiles = fixtures[f]
        e = a[f][:48]
        if e[1] == 12:
            assert not flag
            index = next(i for i, v in enumerate(vectors) if v[:4] == e[0x20:0x22]+e[0x24:0x26])
        else:
            assert e[1] == 10
            guard_rejections += 1
            index = next(i for i, v in enumerate(vectors)
                         if flag or (y < 49 and v[4]&1) or (y >= 128 and v[4]&2)
                         or (x < 41 and v[4]&4) or (x >= 216 and v[4]&8))
        tw += [(f, sy['world_actor_state'], data), (f, sy['sms_vram']+0x3800, tiles),
               (f, sy['randbase'], seed_for(7, index).to_bytes(2, 'big'))]
    pair.compare(a, pair.execute(True, 'jump-guards', frames, tw), frames, range(16), 'jump guards')
    assert guard_rejections >= 64
    print('128 original-observed shadow-boundary/terrain jump guards OK', flush=True)

    # Follow a complete four-hop cycle, controlling choices only when source
    # actually requests a vector or hidden delay. All intermediate ticks run free.
    data = bytes(record(10))+bytes(720)
    frames = set(range(3102, 3402))
    a = pair.execute(False, 'cycle', frames, [(3102, 0x600, data), (3102, 0x1600, bytes(1536))])
    hidden = next(f for f in sorted(frames) if a[f][1] == 0)
    end = min(hidden+32, max(frames))
    tw = [(3102, sy['world_actor_state'], data), (3102, sy['sms_vram']+0x3800, bytes(1536))]
    jumps, rejected = [], []
    previous = data[:48]
    for f in range(3102, end+1):
        e = a[f][:48]
        if previous[1] == 10 and previous[4] == 0:
            if e[1] == 12:
                index = next(i for i, v in enumerate(vectors) if v[:4] == e[0x20:0x22]+e[0x24:0x26])
                jumps.append(dict(frame=f, vector=index))
            else:
                x, y = previous[0x23], previous[0x27]
                index = next(i for i, v in enumerate(vectors)
                             if (y < 49 and v[4]&1) or (y >= 128 and v[4]&2)
                             or (x < 41 and v[4]&4) or (x >= 216 and v[4]&8))
                rejected.append(f)
            tw.append((f, sy['randbase'], seed_for(7, index).to_bytes(2, 'big')))
        if previous[1] == 14 and previous[4] == 0:
            tw.append((f, sy['randbase'], seed_for(15, e[4]-111).to_bytes(2, 'big')))
        previous = e
    b = pair.execute(True, 'cycle', range(3102, end+1), tw)
    pair.compare(a, b, range(3102, end+1), [0], 'complete four-hop cycle')
    assert len(jumps) == 4 and a[hidden][3]&1 == 0
    print('Complete four-hop cycle,48-tick retreat and hidden delay OK', flush=True)
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(source).hexdigest(), region=pair.options['genesis_plus_gx_region_detect'],
                  deterministic_cases=36, controlled_decisions=decisions, cycle_jumps=jumps,
                  jump_guard_cases=128, jump_guard_rejections=guard_rejections,
                  rejected_vectors=rejected, hidden_frame=hidden, cycle_frames=end-3102+1,
                  record_comparisons=pair.comparisons, collision_descriptor_bytes_excluded=[27, 28],
                  original_rng_stream_verified=False, natural_gameplay_verified=False)
    (ROOT/f'validation/hopping_actor{pair.suffix}_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
