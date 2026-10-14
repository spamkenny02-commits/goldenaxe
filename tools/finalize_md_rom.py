"""Write the Mega Drive additive checksum after cartridge padding."""
import argparse
from pathlib import Path
import struct


def md_checksum(data):
    if len(data) < 0x200 or len(data) % 2:
        raise ValueError('Expected an even-sized Mega Drive cartridge image')
    return sum(word[0] for word in struct.iter_unpack('>H', data[0x200:])) & 0xffff


def finalize(path):
    data = bytearray(path.read_bytes())
    if not data[0x100:0x110].startswith(b'SEGA MEGA DRIVE'):
        raise ValueError('Missing Mega Drive header')
    if int.from_bytes(data[0x1a4:0x1a8], 'big') != len(data) - 1:
        raise ValueError('Header ROM end does not match the padded image')
    checksum = md_checksum(data)
    data[0x18e:0x190] = checksum.to_bytes(2, 'big')
    path.write_bytes(data)
    print(f'Mega Drive additive checksum: {checksum:04X}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    finalize(parser.parse_args().rom)
