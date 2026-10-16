"""Generated84C7 semantic state/cost/M1 composition;see generate_tone_channel_refresh.py."""
# Cost-plan SHA256: a234f114d778c594e9129d3dae283498a3f62f473835fd0ea908dee39e32fd42
from audio_note_sequence_refresh import note_sequence_refresh
from audio_pitch_refresh import pitch_refresh
from audio_envelope_refresh import adsr_refresh,table_envelope_refresh

def tone_channel_refresh(rom, state, offset=64, de=35339):
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
        raise NotImplementedError(f'Uncaptured tone RAM {a:04X}')

    def result():
        return dict(state=bytes(r), tstates=cost, unwind=False, de=de, m1_fetches=m1)
    r[offset + 10] = r[offset + 10] - 1 & 255
    cost = 23
    m1 = 2
    pitch = True
    if not r[offset + 10]:
        cost += 7 + 17
        m1 += 1 + 1
        sequence = note_sequence_refresh(rom, r, offset)
        r = bytearray(sequence['state'])
        cost += sequence['tstates']
        m1 += sequence['m1_fetches']
        de = sequence['de']
        if sequence.get('unwind', False):
            return result()
        de = int.from_bytes(r[offset + 3:offset + 5], 'little')
        for bit in [16, 4]:
            cost += 20
            m1 += 2
            if r[offset] & bit:
                cost += 11
                m1 += 1
                return result()
            cost += 5
            m1 += 1
        cost += 17 + 20
        m1 += 1 + 2
        if not r[offset + 6] & 128:
            cost += 11
            m1 += 1
        else:
            cost += 5 + 20
            m1 += 1 + 2
            if r[offset] & 2:
                cost += 11
                m1 += 1
            else:
                cost += 5 + 19 + 19 + 15 + 10 + 7 + 7 + 11 + 4 + 3 * 16 + 7 + 8 + 7 + 4 + 19 + 19 + 10
                m1 += 1 + 2 + 2 + 2 + 1 + 1 + 1 + 1 + 1 + 3 * 2 + 1 + 2 + 1 + 1 + 2 + 2 + 1
                pointer = int.from_bytes(r[offset + 16:offset + 18], 'little')
                r[offset + 20:offset + 23] = bytes((read(pointer + i) for i in range(3)))
                r[offset + 23] = read(pointer + 3) >> 1
                r[offset + 18:offset + 20] = bytes(2)
                de = 56832 + offset + 23
        cost += 17 + 20
        m1 += 1 + 2
        if not r[offset + 7] & 128:
            cost += 11
            m1 += 1
        else:
            cost += 5 + 20
            m1 += 1 + 2
            if r[offset] & 2:
                cost += 11
                m1 += 1
            else:
                cost += 5 + 20
                m1 += 1 + 2
                if r[offset + 29] & 128:
                    cost += 11
                    m1 += 1
                else:
                    r[offset + 31] = 255
                    r[offset + 29] = 16 | r[offset + 30]
                    cost += 5 + 7 + 19 + 7 + 19 + 19 + 10
                    m1 += 1 + 1 + 2 + 1 + 2 + 2 + 1
        cost += 12
        m1 += 1
    else:
        cost += 12 + 20
        m1 += 1 + 2
        if r[offset] & 4:
            cost += 11
            m1 += 1
            return result()
        cost += 5 + 19 + 4
        m1 += 1 + 2 + 1
        if not r[offset + 14]:
            cost += 12
            m1 += 1
        else:
            cost += 7 + 23
            m1 += 1 + 2
            r[offset + 14] = r[offset + 14] - 1 & 255
            if r[offset + 14]:
                cost += 10
                m1 += 1
            else:
                cost += 17 + 20
                m1 += 1 + 2
                if r[offset] & 2:
                    cost += 11
                    m1 += 1
                else:
                    cost += 5 + 20 + 10
                    m1 += 1 + 2 + 1
                    if r[offset + 7] & 128:
                        r[offset + 29] = r[offset + 29] & 15 | 128
                        cost += 19 + 7 + 7 + 19 + 10
                        m1 += 2 + 1 + 1 + 2 + 1
                    else:
                        r[offset] |= 16
                        cost += 23 + 20
                        m1 += 2 + 2
                        cost += 11 if r[offset] & 4 else 5 + 7 + 19 + 11 + 10
                        m1 += 1 if r[offset] & 4 else 1 + 1 + 2 + 1 + 1
        cost += 19 + 4
        m1 += 2 + 1
        if not r[offset + 6]:
            cost += 12
            m1 += 1
            pitch = False
        else:
            cost += 7 + 20
            m1 += 1 + 2
            if r[offset] & 32:
                cost += 12
                m1 += 1
                pitch = False
            else:
                cost += 7
                m1 += 1
    if pitch:
        cost += 20
        m1 += 2
        if r[offset] & 64:
            cost += 12
            m1 += 1
        else:
            cost += 7 + 17
            m1 += 1 + 1
            value = pitch_refresh(rom, r, offset)
            r = bytearray(value['state'])
            cost += value['tstates']
            m1 += value['m1_fetches']
            if value.get('unwind', False):
                de = value['de']
                return result()
            transpose = r[offset + 37]
            de = transpose if transpose < 128 else transpose | 65280
            cost += 7 + 19 + 4 + 10 + (4 if transpose & 128 else 0) + 4 + 11 + 19 + 7
            m1 += 1 + 2 + 1 + 1 + (1 if transpose & 128 else 0) + 1 + 1 + 2 + 1
            cost += 7 + 7 if r[offset + 1] == 224 else 12
            m1 += 1 + 1 if r[offset + 1] == 224 else 1
            cost += 4 + 4 + 7 + 4 + 11 + 4 + 7 + 4 + 4 * 4 + 11
            m1 += 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 4 * 1 + 1
    cost += 17
    m1 += 1
    envelope = adsr_refresh(r, offset, de) if r[offset + 7] & 128 else table_envelope_refresh(rom, r, offset, de)
    r = bytearray(envelope['state'])
    cost += envelope['tstates']
    m1 += envelope['m1_fetches']
    de = envelope.get('de', de)
    if envelope.get('unwind', False):
        return result()
    for bit in [4, 16]:
        cost += 20
        m1 += 2
        if r[offset] & bit:
            cost += 11
            m1 += 1
            return result()
        cost += 5
        m1 += 1
    volume = envelope['accumulator'] + r[offset + 8] & 255
    cost += 19 + 8 + (7 + 7 if volume & 16 else 12) + 19 + 7 + 11 + 10
    m1 += 2 + 2 + (1 + 1 if volume & 16 else 1) + 2 + 1 + 1 + 1
    return result()
