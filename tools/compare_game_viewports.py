#!/usr/bin/env python3
"""Compare pinned-GPGX RGB565 captures from test_md_emulator.py.

Only the shared 256x192 SMS viewport is compared. The fixed DAC conversion
accounts for the existing MD 0/2/5/7 CRAM mapping; no fitted colour mapping,
pixel tolerance, or alignment is used. Input PNGs must use RGB8/filter zero,
as emitted by the emulator harness.
"""
import argparse
from pathlib import Path
import struct
import zlib


def read_capture(path):
    data = Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Expected a PNG capture')
    offset = 8
    compressed = bytearray()
    width = height = None
    while offset < len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset+4:offset+8]
        chunk = data[offset+8:offset+8+length]
        if kind == b'IHDR':
            width, height, depth, colour, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunk)
            if (depth, colour, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise ValueError('Expected RGB8 noninterlaced harness PNG')
        elif kind == b'IDAT':
            compressed.extend(chunk)
        elif kind == b'IEND':
            break
        offset += length + 12
    if width != 256 or height not in (192, 224):
        raise ValueError('Expected a 256x192 or 256x224 harness capture')
    raw = zlib.decompress(compressed)
    pitch = 1 + width*3
    if len(raw) != pitch*height:
        raise ValueError('Truncated capture')
    rows = []
    for y in range(192):
        row = raw[y*pitch:(y+1)*pitch]
        if row[0] != 0:
            raise ValueError('Expected unfiltered harness PNG rows')
        rows.append(row[1:])
    return b''.join(rows)


def differences(md, sms):
    if len(md) != 256*192*3 or len(sms) != len(md):
        raise ValueError('Expected two 256x192 RGB viewports')
    # RGB565 quantization differs for the six-bit green channel.
    rb = dict(zip((0, 82, 172, 255), (0, 65, 172, 238)))
    green = dict(zip((0, 85, 170, 255), (0, 68, 170, 238)))
    mismatches = []
    for at in range(0, len(md), 3):
        try:
            expected = bytes((rb[sms[at]], green[sms[at+1]], rb[sms[at+2]]))
        except KeyError as error:
            raise ValueError('Unsupported SMS DAC levels; use the pinned RGB565 core') from error
        if md[at:at+3] != expected:
            mismatches.append((at//3 % 256, at//3 // 256))
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--md', type=Path, required=True)
    parser.add_argument('--sms', type=Path, required=True)
    args = parser.parse_args()
    bad = differences(read_capture(args.md), read_capture(args.sms))
    if bad:
        parser.exit(1, f'Viewport mismatch: {len(bad)}/49152 pixels; first at {bad[0]}\n')
    print('Game viewport: OK (49152 pixels, fixed SMS-to-MD DAC conversion)')


if __name__ == '__main__':
    main()
