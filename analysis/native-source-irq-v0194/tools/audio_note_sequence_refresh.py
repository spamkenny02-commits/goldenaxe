"""Generated8357 semantic state/cost/M1 model;see generate_note_sequence_refresh.py."""
# Cost-plan SHA256: 9d221240da595448c0e70d23f0f44475ccf23fdbecc93f98761cc880f8e482f8
from audio_dispatch_cost import POINTER_COST
POINTER_M1=9
def _duration_m1(scale):return 4 if scale==1 else 6+2*((scale-1)&255)

def note_sequence_refresh(rom, state, offset=64):
    r = bytearray(state)
    assert len(r) == 400

    def read(a):
        a &= 65535
        if a < 32768:
            return rom[a]
        if a < 49152:
            return rom[98304 + (a & 16383)]
        if 56832 <= a < 57232:
            return r[a - 56832]
        raise NotImplementedError(f'Uncaptured stream RAM {a:04X}')

    def word(n):
        return int.from_bytes(r[offset + n:offset + n + 2], 'little')

    def setword(n, value):
        r[offset + n:offset + n + 2] = (value & 65535).to_bytes(2, 'little')

    def multiply(value):
        scale = r[offset + 2]
        return (value * scale & 255, 34 if scale == 1 else 37 + 17 * (scale - 1 & 255), _duration_m1(scale))
    cursor = word(3)
    r[offset] &= ~18
    cost = 23 + 23 + 19 + 19
    m1 = 2 + 2 + 2 + 2
    for guard in range(256):
        note = read(cursor)
        cursor = cursor + 1 & 65535
        cost += 7 + 6 + 7 + 10
        m1 += 1 + 1 + 1 + 1
        if note < 224:
            break
        supported = [224, 225, 226, 228, 229, 230, 231, 232, 233, 234, 235, 237, 238, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253]
        if note not in supported:
            raise NotImplementedError(f'Command {note:02X}')
        if note in [241, 242]:
            if r[14]:
                raise NotImplementedError(f'Command {note:02X} restoration8211')
            cost += sum([10, 11, 7, 10, 4, 4, 7, 11, 7, 6, 7, 4, 7, 4])
            m1 += sum([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
            if note == 241:
                r[18] = 128
                cost += 7 + 13
                m1 += 1 + 1
            channel = r[offset + 1]
            cost += 19 + 7
            m1 += 2 + 1
            if channel == 160:
                cost += 12 + 10
                m1 += 1 + 1
                background = 112
            else:
                cost += 7 + 7
                m1 += 1 + 1
                if channel == 192:
                    cost += 12 + 10 + 12
                    m1 += 1 + 1 + 1 + 1
                    if r[352] & 128:
                        cost += 12
                        m1 += 1
                        background = 352
                    else:
                        cost += 7 + 10 + 12
                        m1 += 1 + 1 + 1
                        background = 160
                else:
                    cost += 7 + 20
                    m1 += 1 + 2
                    if r[offset] & 64:
                        cost += 12
                        m1 += 1
                    else:
                        cost += 7 + 10 + 12 + 10
                        m1 += 1 + 1 + 1 + 1 + 1
                        if not r[304] & 128:
                            cost += 10 + 15 + 15 + 15 + 10 + 10
                            m1 += 1 + 2 + 2 + 2 + 1 + 1
                            r[160] = r[160] & ~68 | 16
                            r[304] = 0
                    cost += 10 + 12
                    m1 += 1 + 1
                    background = 208
            r[background] = r[background] & ~4 | 16
            r[17] = 0
            r[offset] = 0
            cost += 15 + 15 + 7 + 11 + 4 + 13 + 19 + 13 + 4 + 12 + 10 + 10 + 10
            m1 += 2 + 2 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 1 + 1 + 1
            return dict(state=bytes(r), tstates=cost, unwind=True, de=cursor, m1_fetches=m1)
        cost += sum([10, 11, 7, 10, 4, 4, 7, 11, 7, 6, 7, 4, 7, 4]) + 6 + 10
        m1 += sum([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]) + 1 + 1
        value = read(cursor)
        if note in [224, 233]:
            r[offset + 7] = 128
            r[offset + 32:offset + 37] = bytes((read(cursor + i) for i in range(5)))
            cursor = cursor + 5 & 65535
            cost += 19 + 15 + 10 + 7 + 7 + 11 + 4 + 5 * 16 + 4 + 6 + 10
            m1 += 2 + 2 + 1 + 1 + 1 + 1 + 1 + 5 * 2 + 1 + 1 + 1
        elif note in [225, 238, 244, 245, 250]:
            index = {225: 37, 238: 28, 244: 6, 245: 7, 250: 2}[note]
            r[offset + index] = value
            cursor = cursor + 1 & 65535
            cost += 19 + 10
            m1 += 2 + 1
        elif note == 226:
            old = r[offset + 38]
            mask = value ^ 255
            r[offset + 38] = value
            channel = r[offset + 1]
            cost += 19 + 19 + 4 + 4 + 19 + 7
            m1 += 2 + 2 + 1 + 1 + 2 + 1
            for tone in [128, 160, 192]:
                if channel == tone:
                    cost += 12
                    m1 += 1
                    break
                cost += 7 + 8 + 8
                m1 += 1 + 2 + 2
                old = (old << 1 | old >> 7) & 255
                mask = (mask << 1 | mask >> 7) & 255
                if tone != 192:
                    cost += 7
                    m1 += 1
            r[18] = (r[18] | old) & mask
            cursor = cursor + 1 & 65535
            cost += 10 + 7 + 4 + 4 + 7 + 11 + 10
            m1 += 1 + 1 + 1 + 1 + 1 + 1 + 1
        elif note == 228:
            r[24] = r[24] + value & 15
            cursor = cursor + 1 & 65535
            cost += 4 + 13 + 4 + 7 + 13 + 10
            m1 += 1 + 1 + 1 + 1 + 1 + 1
        elif note == 229:
            r[offset + 30] = 8 if value else 0
            cursor = cursor + 1 & 65535
            cost += 4 + (7 + 7 if value else 12) + 19 + 10
            m1 += 1 + (1 + 1 if value else 1) + 2 + 1
        elif note == 230:
            cost += 4 + 13 + 4
            m1 += 1 + 1 + 1
            if r[11]:
                cost += 11
                m1 += 1
            else:
                cost += 5 + 4 + 19 + 7 + 19 + 10
                m1 += 1 + 1 + 2 + 1 + 2 + 1
                r[offset + 8] = r[offset + 8] + value & 15
            cursor = cursor + 1 & 65535
        elif note == 232:
            duration, work, work_m1 = multiply(value)
            r[offset + 14] = r[offset + 15] = duration
            cursor = cursor + 1 & 65535
            cost += 17 + work + 19 + 19 + 10
            m1 += 1 + work_m1 + 2 + 2 + 1
        elif note == 234:
            cost += 8
            m1 += 2
            if value & 128:
                r[offset] |= 1
                r[offset + 24] = value
                cursor = cursor + 1 & 65535
                r[offset + 25] = r[offset + 26] = read(cursor)
                cost += 7 + 23 + 19 + 6 + 7 + 19 + 19 + 10
                m1 += 1 + 2 + 2 + 1 + 1 + 2 + 2 + 1
            else:
                r[offset] &= ~1
                r[offset + 26] = 0
                cost += 12 + 23 + 19 + 6 + 10
                m1 += 1 + 2 + 2 + 1 + 1
                cursor = cursor + 1 & 65535
            cursor = cursor + 1 & 65535
        elif note in [235, 252]:
            cursor = cursor + 1 & 65535
            cost += 10
            m1 += 1
        elif note == 237:
            r[1] = r[2] = value
            cursor = cursor + 1 & 65535
            cost += 13 + 13 + 10
            m1 += 1 + 1 + 1
        elif note == 240:
            setword(16, cursor)
            r[offset + 6] = 128
            cursor = cursor + 4 & 65535
            cost += 19 + 19 + 19 + 6 + 6 + 6 + 10
            m1 += 2 + 2 + 2 + 1 + 1 + 1 + 1
        elif note == 243:
            cost += 4 + 13 + 4 + 10
            m1 += 1 + 1 + 1 + 1
            if not r[15] & 128:
                cost += 4 + 7 + 4
                m1 += 1 + 1 + 1
                if value & 3 != 3:
                    cost += 12
                    m1 += 1
                else:
                    cost += 7 + 10 + 12
                    m1 += 1 + 1 + 1 + 1
                    if not r[304] & 128:
                        cost += 12
                        m1 += 1
                    else:
                        cost += 7 + 10 + 15 + 15 + 4 + 19 + 4 + 11 + 13 + 10 + 10 + 10 - 16
                        m1 += 1 + 1 + 2 + 2 + 1 + 2 + 1 + 1 + 1 + 1 + 1 + 1 - 2
                        r[208] = r[208] & ~4 | 16
                        r[offset] = 0
                        r[15] = 255
                        return dict(state=bytes(r), tstates=cost, unwind=True, de=cursor, m1_fetches=m1)
            cost += 7 + 11 + 10 + 14 + 7 + 4
            m1 += 1 + 1 + 1 + 2 + 1 + 1
            if value & 3 == 3:
                cost += 7 + 7 + 11 + 23 + 15 + 23 + 10
                m1 += 1 + 1 + 1 + 2 + 2 + 2 + 1
                r[offset] &= ~64
                r[160] |= 4
                r[304] |= 4
            else:
                cost += 12 + 23 + 20
                m1 += 1 + 2 + 2
                r[offset] |= 64
                if r[304] & 128:
                    cost += 12 + 23 + 10
                    m1 += 1 + 2 + 1
                    r[304] &= ~4
                else:
                    cost += 7 + 15 + 10
                    m1 += 1 + 2 + 1
                    r[160] &= ~4
            cursor = cursor + 1 & 65535
        elif note == 246:
            cursor = read(cursor) | read(cursor + 1) << 8
            cost += 4 + 7 + 6 + 7 + 6 + 10
            m1 += 1 + 1 + 1 + 1 + 1 + 1
        elif note == 251:
            r[offset + 5] = r[offset + 5] + value & 255
            cursor = cursor + 1 & 65535
            cost += 19 + 19 + 10
            m1 += 2 + 2 + 1
        elif note == 253:
            r[offset] = r[offset] & ~8 | (8 if value == 1 else 0)
            cursor = cursor + 1 & 65535
            cost += 7 + (7 if value == 1 else 12) + 23 + 10
            m1 += 1 + (1 if value == 1 else 1) + 2 + 1
        elif note == 231:
            cost += 23 + 6 + 10
            m1 += 2 + 1 + 1
            r[offset] |= 2
        elif note == 247:
            index = read(cursor) + 39 & 255
            cursor = cursor + 1 & 65535
            assert offset + index < 400
            cost += 6 + 7 + 4 + 7 + 15 + 10 + 11 + 7 + 4
            m1 += 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 1
            if r[offset + index]:
                cost += 12
                m1 += 1
            else:
                cost += 7 + 7 + 7
                m1 += 1 + 1 + 1
                r[offset + index] = read(cursor)
            cursor = cursor + 1 & 65535
            r[offset + index] = r[offset + index] - 1 & 255
            cost += 6 + 11 + 10
            m1 += 1 + 1 + 1
            if r[offset + index]:
                cost += 4 + 7 + 6 + 7 + 6 + 10
                m1 += 1 + 1 + 1 + 1 + 1 + 1
                cursor = read(cursor) | read(cursor + 1) << 8
            else:
                cost += 6 + 10
                m1 += 1 + 1
                cursor = cursor + 2 & 65535
        elif note == 248:
            target = read(cursor) | read(cursor + 1) << 8
            stack = r[offset + 9] - 2 & 255
            assert offset + stack + 1 < 400
            setword(stack, cursor + 1)
            r[offset + 9] = stack
            cursor = target
            cost += sum([4, 6, 7, 4, 11, 15, 10, 23, 19, 23, 7, 11, 7, 6, 7, 10, 6, 10])
            m1 += sum([1, 1, 1, 1, 1, 2, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1])
        else:
            stack = r[offset + 9]
            assert offset + stack + 1 < 400
            cursor = word(stack) + 1 & 65535
            r[offset + 9] = stack + 2 & 255
            cost += 15 + 10 + 19 + 7 + 11 + 7 + 6 + 7 + 23 + 23 + 10
            m1 += 2 + 1 + 2 + 1 + 1 + 1 + 1 + 1 + 2 + 2 + 1
    else:
        raise ValueError('Tie command loop')
    cost += 20 + 10
    m1 += 2 + 1
    if r[offset] & 8:
        low = read(cursor)
        cursor = cursor + 1 & 65535
        frequency = note << 8 | low
        cost += 4 + 7 + 6 + 4 + 4
        m1 += 1 + 1 + 1 + 1 + 1
        if not frequency:
            cost += 12
            m1 += 1
        else:
            cost += 7 + 7 + 19 + 4 + 4 + 10 + (4 if r[offset + 5] & 128 else 0) + 11
            m1 += 1 + 1 + 2 + 1 + 1 + 1 + (1 if r[offset + 5] & 128 else 0) + 1
            transpose = r[offset + 5]
            frequency += transpose - 256 if transpose & 128 else transpose
        setword(11, frequency)
        cost += 19 + 19 + 7 + 6 + 10
        m1 += 2 + 2 + 1 + 1 + 1
        duration = read(cursor)
        cursor = cursor + 1 & 65535
        duration, work, work_m1 = multiply(duration)
        cost += 17 + work + 19 + 19
        m1 += 1 + work_m1 + 2 + 2
        r[offset + 10] = r[offset + 13] = duration
    else:
        cost += 7
        m1 += 1
        if note < 128:
            cost += 12
            m1 += 1
            duration, work, work_m1 = multiply(note)
            cost += 17 + work + 19 + 19
            m1 += 1 + work_m1 + 2 + 2
            r[offset + 10] = r[offset + 13] = duration
        else:
            cost += 7
            m1 += 1
            if note == 128:
                cost += 12 + 17 + 20
                m1 += 1 + 1 + 2
                if r[offset] & 2:
                    cost += 11
                    m1 += 1
                else:
                    cost += 5 + 20 + 10
                    m1 += 1 + 2 + 1
                    if r[offset + 7] & 128:
                        cost += 19 + 7 + 7 + 19 + 10
                        m1 += 2 + 1 + 1 + 2 + 1
                        r[offset + 29] = r[offset + 29] & 15 | 128
                    else:
                        cost += 23 + 20
                        m1 += 2 + 2
                        r[offset] |= 16
                        cost += 11 if r[offset] & 4 else 5 + 7 + 19 + 11 + 10
                        m1 += 1 if r[offset] & 4 else 1 + 1 + 2 + 1 + 1
                cost += 12
                m1 += 1
            else:
                cost += 7 + 4 + 19 + 7 + 19 + 4 + 17 + 7 + 19 + 10 + POINTER_COST + 19 + 19
                m1 += 1 + 1 + 2 + 1 + 2 + 1 + 1 + 1 + 2 + 1 + POINTER_M1 + 2 + 2
                r[offset + 29] &= 127
                index = (note & 127) + r[offset + 5] & 255
                address = 33853 + index * 2
                setword(11, read(address) | read(address + 1) << 8)
            duration = read(cursor)
            cursor = cursor + 1 & 65535
            cost += 7 + 6 + 4 + 10
            m1 += 1 + 1 + 1 + 1
            if duration & 128:
                r[offset + 10] = r[offset + 13]
                cursor = cursor - 1 & 65535
                cost += 19 + 19 + 6 + 12
                m1 += 2 + 2 + 1 + 1
            else:
                duration, work, work_m1 = multiply(duration)
                cost += 17 + work + 19 + 19
                m1 += 1 + work_m1 + 2 + 2
                r[offset + 10] = r[offset + 13] = duration
    setword(3, cursor)
    cost += 19 + 19 + 20
    m1 += 2 + 2 + 2
    if r[offset] & 2:
        return dict(state=bytes(r), tstates=cost + 11, de=cursor, m1_fetches=m1 + 1)
    cost += 5 + 20
    m1 += 1 + 2
    if r[offset] & 64:
        cost += 12
        m1 += 1
    else:
        cost += 7 + 23
        m1 += 1 + 2
        r[offset] &= ~32
    cost += 19 + 19 + 4 + 19 + 20
    m1 += 2 + 2 + 1 + 2 + 2
    r[offset + 14] = r[offset + 15]
    r[offset + 21] = 0
    if r[offset + 7] & 128:
        cost += 11
        m1 += 1
    else:
        cost += 5 + 19 + 10
        m1 += 1 + 2 + 1
        r[offset + 31] = 0
    return dict(state=bytes(r), tstates=cost, de=cursor, m1_fetches=m1)
