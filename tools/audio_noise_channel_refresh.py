"""Generated864F semantic state/cost/M1 composition;see generate_noise_channel_refresh.py."""
# Cost-plan SHA256: 0f5c3aad31c5cf57a8f1de409d6adaed5d1d5ff53d2d0da30d2a85ea13fa644a
from audio_noise_note_refresh import noise_note_refresh
from audio_envelope_refresh import adsr_refresh,table_envelope_refresh
from audio_note_sequence_refresh import _duration_m1

def noise_channel_refresh(rom, state, offset=208, de=35339):
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
        raise NotImplementedError(f'Uncaptured noise RAM {a:04X}')

    def result():
        return dict(state=bytes(r), tstates=cost, unwind=False, de=de, m1_fetches=m1)
    r[offset + 10] = r[offset + 10] - 1 & 255
    cost = 23 + 10
    m1 = 2 + 1
    if r[offset + 10]:
        cost += 17
        m1 += 1
        envelope = adsr_refresh(r, offset, de) if r[offset + 7] & 128 else table_envelope_refresh(rom, r, offset, de)
        r = bytearray(envelope['state'])
        cost += envelope['tstates']
        m1 += envelope['m1_fetches']
        de = envelope.get('de', de)
        if envelope.get('unwind', False):
            return result()
        cost += 20
        m1 += 2
        if r[offset] & 4:
            cost += 11
            m1 += 1
            return result()
        cost += 5 + 20
        m1 += 1 + 2
        if r[offset] & 16:
            cost += 11
            m1 += 1
            return result()
        volume = envelope['accumulator'] + r[offset + 8] & 255
        cost += 5 + 19 + 8
        m1 += 1 + 2 + 2
        cost += 7 + 7 if volume & 16 else 12
        m1 += 1 + 1 if volume & 16 else 1
        cost += 19 + 7 + 11 + 10
        m1 += 2 + 1 + 1 + 1
        return result()
    r[offset] &= ~16
    cost += 23 + 19 + 19
    m1 += 2 + 2 + 2
    cursor = int.from_bytes(r[offset + 3:offset + 5], 'little')
    for guard in range(256):
        note = read(cursor)
        cursor = cursor + 1 & 65535
        cost += 7 + 6 + 7
        m1 += 1 + 1 + 1
        if note < 224:
            break
        if note not in [246, 247]:
            raise NotImplementedError(f'Noise command {note:02X}')
        cost += 12 + 109 + 18
        m1 += 1 + 15 + 2
        if note == 246:
            cursor = read(cursor) | read(cursor + 1) << 8
            cost += 4 + 7 + 6 + 7 + 6 + 10
            m1 += 1 + 1 + 1 + 1 + 1 + 1
        else:
            index = read(cursor) + 39 & 255
            cursor = cursor + 1 & 65535
            assert offset + index < 400
            cost += 6 + 7 + 4 + 7 + 15 + 10 + 11 + 7 + 4
            m1 += 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 1
            if r[offset + index]:
                cost += 12
                m1 += 1
            else:
                r[offset + index] = read(cursor)
                cost += 7 + 7 + 7
                m1 += 1 + 1 + 1
            cursor = cursor + 1 & 65535
            r[offset + index] = r[offset + index] - 1 & 255
            cost += 6 + 11 + 10
            m1 += 1 + 1 + 1
            if r[offset + index]:
                cursor = read(cursor) | read(cursor + 1) << 8
                cost += 4 + 7 + 6 + 7 + 6 + 10
                m1 += 1 + 1 + 1 + 1 + 1 + 1
            else:
                cursor = cursor + 2 & 65535
                cost += 6 + 10
                m1 += 1 + 1
    else:
        raise ValueError('Noise command loop')
    cost += 7 + 7 + 10
    m1 += 1 + 1 + 1
    if note >= 128:
        helper = noise_note_refresh(r, note, offset)
        r = bytearray(helper['state'])
        cost += 17 + helper['tstates'] + 10
        m1 += 1 + helper['m1_fetches'] + 1
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
            scale = r[offset + 2]
            r[offset + 10] = r[offset + 13] = duration * scale & 255
            cost += 17 + (34 if scale == 1 else 37 + 17 * (scale - 1 & 255)) + 19 + 19
            m1 += 1 + _duration_m1(scale) + 2 + 2
    else:
        scale = r[offset + 2]
        r[offset + 10] = r[offset + 13] = note * scale & 255
        cost += 17 + (34 if scale == 1 else 37 + 17 * (scale - 1 & 255)) + 19 + 19
        m1 += 1 + _duration_m1(scale) + 2 + 2
    de = cursor
    r[offset + 3:offset + 5] = cursor.to_bytes(2, 'little')
    cost += 19 + 19 + 20
    m1 += 2 + 2 + 2
    if r[offset] & 2:
        cost += 11
        m1 += 1
        return result()
    cost += 5 + 20
    m1 += 1 + 2
    if r[offset] & 64:
        cost += 12
        m1 += 1
    else:
        r[offset] &= ~32
        cost += 7 + 23
        m1 += 1 + 2
    r[offset + 14] = r[offset + 15]
    r[offset + 21] = 0
    cost += 19 + 19 + 4 + 19 + 20
    m1 += 2 + 2 + 1 + 2 + 2
    if r[offset + 7] & 128:
        cost += 11
        m1 += 1
    else:
        r[offset + 31] = 0
        cost += 5 + 19 + 10
        m1 += 1 + 2 + 1
    return result()
