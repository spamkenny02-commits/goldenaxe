"""Common object tail 26E5..2753; behavior/collision/damage dispatch is separate."""
from actor_reference import ROOT


def common_tick(entity):
    if not entity[0]:
        return
    if entity[6]:
        entity[6] -= 1
    else:
        # DEC A / JP M skips 00h and 81h..FFh, rather than testing !=0.
        counter = (entity[4] - 1) & 255
        if not counter & 128:
            y = (int.from_bytes(entity[0x10:0x12], 'little') +
                 int.from_bytes(entity[0x14:0x16], 'little')) & 65535
            x = (int.from_bytes(entity[0x12:0x14], 'little') +
                 int.from_bytes(entity[0x16:0x18], 'little')) & 65535
            if not counter:
                x &= 0xff00
                y &= 0xff00
            entity[4] = counter
            entity[0x10:0x12] = y.to_bytes(2, 'little')
            entity[0x12:0x14] = x.to_bytes(2, 'little')
        if entity[12]:
            phase = (entity[14]+1) & 255
            if phase >= entity[13]:
                phase = 0
            entity[14] = phase
            if not phase:
                animation = (entity[11]+1) & 255
                entity[11] = 0 if animation == entity[12] else animation
    hurt = (entity[5]-1) & 255
    if not hurt & 128:
        entity[5] = hurt
        entity[3] |= 1
        if hurt & 2:
            entity[3] &= 254


def emergence_reference():
    source = ROOT/'validation/sms-vertical-check'
    entity = bytearray((source/'ram_03101.bin').read_bytes()[0x600:0x630])
    for frame in range(3102,3149):
        common_tick(entity)
        expected = (source/f'ram_{frame:05}.bin').read_bytes()[0x600:0x630]
        assert entity == expected, ('type26 emergence', frame)
    return 47


if __name__=='__main__':
    print(f'{emergence_reference()} source emergence states exact')
