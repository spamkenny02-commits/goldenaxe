#!/usr/bin/env python3
"""Check production 68000 video output against a ROM-free indexed-pixel oracle."""
import argparse
import ctypes as C
from pathlib import Path
import struct
import subprocess
import sys
from test_md_emulator import GameInfo, Variable, png


def expected(stage, x, y):
    colors = [0] * 32
    colors[:4] = [3 if stage else 12, 48, 60, 63]
    colors[16:20] = [12 if stage else 3, 15, 51, 60]
    colors[31] = 63
    if y >= 192:
        color = colors[16 + (0 if stage == 2 else 2)]
    else:
        row, col = y // 8, x // 8
        px, py = x % 8, y % 8
        if col & 4:
            px = 7 - px
        if col & 8:
            py = 7 - py
        bg = 1 + (row + py) % 3 if ((row + 1) >> (px % 5)) & 1 else 0
        palette = (row + col) & 1
        if stage and row == 7 and col == 5:
            palette ^= 1
        sprite = x < 64 and 50 <= y < 58
        color = colors[31] if sprite and (not (col & 2) or not bg) else colors[palette * 16 + bg]
    # The fixture deliberately uses only channel extrema; MD and SMS match exactly.
    return tuple(255 if (color >> shift) & 3 else 0 for shift in (0, 2, 4))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--rom', type=Path, default=Path('md/build/video-fixture/fixture.bin'))
    parser.add_argument('--elf', type=Path, default=Path('md/build/video-fixture/fixture.elf'))
    parser.add_argument('--nm', default='m68k-elf-nm')
    parser.add_argument('--output', type=Path, default=Path('md/build/video-fixture'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    symbols = {}
    for line in subprocess.check_output([args.nm, '-n', str(args.elf)], text=True).splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    at = symbols['gaw_video_fixture_ready'] - 0xFF0000
    lib = C.CDLL(str(args.core.resolve()))
    variables = {}
    directory = str(args.output.resolve()).encode()
    state = {'format': 0, 'image': None, 'pad': 0}

    @C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
    def environment(command, data):
        command &= ~0x10000
        if command in (9, 31):
            C.cast(data, C.POINTER(C.c_char_p))[0] = directory
            return True
        if command in (3, 17):
            C.cast(data, C.POINTER(C.c_bool))[0] = command == 3
            return True
        if command in (39, 52):
            C.cast(data, C.POINTER(C.c_uint))[0] = 0
            return True
        if command == 10:
            state['format'] = C.cast(data, C.POINTER(C.c_uint))[0]
            return state['format'] in (0, 1, 2)
        if command == 16:
            entries = C.cast(data, C.POINTER(Variable))
            i = 0
            while entries[i].key:
                variables[entries[i].key] = entries[i].value.decode().split('; ', 1)[1].split('|', 1)[0].encode()
                i += 1
            variables[b'genesis_plus_gx_region_detect'] = b'ntsc-u'
            return True
        if command == 15:
            entry = C.cast(data, C.POINTER(Variable)).contents
            if entry.key in variables:
                entry.value = variables[entry.key]
                return True
            return False
        return command in (6, 8, 11, 13, 18, 32, 34, 35, 36, 37, 42, 44)

    @C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
    def video(data, width, height, pitch):
        if data:
            state['image'] = (C.string_at(data, pitch * height), width, height, pitch)

    @C.CFUNCTYPE(None, C.c_int16, C.c_int16)
    def sample(left, right):
        pass

    @C.CFUNCTYPE(C.c_size_t, C.POINTER(C.c_int16), C.c_size_t)
    def batch(data, frames):
        return frames

    @C.CFUNCTYPE(None)
    def poll():
        pass

    @C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
    def input_state(port, device, index, button):
        return int(port == 0 and device == 1 and button == 0 and state['pad'])

    callbacks = {'environment': environment, 'video_refresh': video, 'audio_sample': sample,
                 'audio_sample_batch': batch, 'input_poll': poll, 'input_state': input_state}
    for name, callback in callbacks.items():
        setter = getattr(lib, 'retro_set_' + name)
        setter.argtypes = [type(callback)]
        setter(callback)
    lib.retro_init()
    lib.retro_load_game.argtypes = [C.POINTER(GameInfo)]
    lib.retro_load_game.restype = C.c_bool
    info = GameInfo(str(args.rom.resolve()).encode(), None, 0, None)
    assert lib.retro_load_game(C.byref(info)), 'Core rejected the standalone fixture'
    lib.retro_set_controller_port_device(0, 1)
    lib.retro_get_memory_data.argtypes = [C.c_uint]
    lib.retro_get_memory_data.restype = C.c_void_p
    lib.retro_get_memory_size.argtypes = [C.c_uint]
    lib.retro_get_memory_size.restype = C.c_size_t
    assert lib.retro_get_memory_size(2) == 0x10000, 'Fixture did not boot as Mega Drive'
    memory = (C.c_uint8 * 0x10000).from_address(lib.retro_get_memory_data(2))
    swap = int(sys.byteorder == 'little')
    def ready():
        return (memory[at ^ swap] << 8) | memory[(at + 1) ^ swap]
    try:
        for _ in range(120):
            lib.retro_run()
            if ready() == 0:
                break
        else:
            raise AssertionError('Fixture failed to reach its frame barrier')
        for stage in range(3):
            if stage:
                state['pad'] = 1
                for _ in range(8):
                    lib.retro_run()
                state['pad'] = 0
            for _ in range(8):
                lib.retro_run()
            assert ready() == stage, (stage, ready())
            pixels, width, height, pitch = state['image']
            assert (width, height) == (256, 224), (width, height)
            png(args.output / ('stage%d.png' % stage), pixels, width, height, pitch, state['format'])
            for y in range(height):
                for x in range(width):
                    if state['format'] == 1:
                        value = struct.unpack_from('=I', pixels, y * pitch + x * 4)[0]
                        actual = ((value >> 16) & 255, (value >> 8) & 255, value & 255)
                    else:
                        value = struct.unpack_from('=H', pixels, y * pitch + x * 2)[0]
                        if state['format'] == 2:
                            actual = (value >> 11, (value >> 5) & 63, value & 31)
                            actual = (actual[0] * 255 // 31, actual[1] * 255 // 63, actual[2] * 255 // 31)
                        else:
                            actual = tuple(((value >> shift) & 31) * 255 // 31 for shift in (10, 5, 0))
                    want = expected(stage, x, y)
                    assert actual == want, ('pixel', stage, x, y, actual, want)
            print('Native video stage %d: 57344 pixels match (palette zero, sprite priority, viewport)' % stage)
    finally:
        lib.retro_unload_game()
        lib.retro_deinit()
    print('ROM-free MD video hardware tests: OK (172032 pixels)')


if __name__ == '__main__':
    main()
