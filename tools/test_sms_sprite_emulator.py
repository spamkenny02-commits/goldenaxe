#!/usr/bin/env python3
"""Run generated Z80 fixtures in a pinned SMS II core; check collision at every Y.
No original cartridge input or portable sprite-status implementation is used.
"""
import argparse
import ctypes as C
from pathlib import Path
import tempfile
from test_md_emulator import GameInfo, Variable


def fixture(y, mode):
    code = bytearray()
    labels, fixups = {}, []
    def emit(*data):
        code.extend(data)
    def label(name):
        labels[name] = len(code) + 0x100
    def jump(opcode, name):
        emit(opcode, 0, 0)
        fixups.append((len(code) - 2, name))
    def write(port, value):
        emit(0x3E, value, 0xD3, port)
    def reg(index, value):
        write(0xBF, value)
        write(0xBF, 0x80 | index)
    def address(at):
        write(0xBF, at & 255)
        write(0xBF, 0x40 | (at >> 8))

    emit(0xF3, 0x31, 0xF0, 0xDF)  # DI; LD SP,DFF0
    emit(0xAF, 0x32, 0x10, 0xC0, 0x32, 0x11, 0xC0)
    write(0xBF, 0)  # Consume a complete harmless VRAM-address command.
    write(0xBF, 0x40)
    for index, value in enumerate((4, mode, 14, 255, 255, 127, 0, 0, 0, 0, 255)):
        reg(index, value)
    address(0)
    emit(0x01, 0, 0x40)  # BC=16384 bytes
    label('clear')
    emit(0xAF, 0xD3, 0xBE, 0x0B, 0x78, 0xB1)
    jump(0xC2, 'clear')  # JP NZ,clear
    address(64)  # Fully opaque patterns 2 and 3.
    emit(0x06, 64, 0x3E, 255)
    emit(0xD3, 0xBE, 0x10, 0xFC)  # OUT (BE),A; DJNZ -4
    address(0x3F00)
    for value in (y, y, 0xD0):
        write(0xBE, value)
    address(0x3F80)
    for value in (24, 3, 24, 2):
        write(0xBE, value)
    reg(1, 0x40 | mode)
    emit(0x3E, 0x5A, 0x32, 0x12, 0xC0, 0x16, 0)  # Started marker; D=0
    label('poll')
    emit(0xDB, 0xBF, 0x5F, 0xE6, 0x60, 0xB2, 0x57, 0x7B, 0xE6, 0x80)
    jump(0xCA, 'poll')  # OR all collision/overflow bits until VBlank.
    emit(0x7A, 0x32, 0x10, 0xC0)
    emit(0x3A, 0x11, 0xC0, 0x3C, 0x32, 0x11, 0xC0, 0x16, 0)
    jump(0xC3, 'poll')
    for offset, name in fixups:
        code[offset:offset + 2] = labels[name].to_bytes(2, 'little')
    rom = bytearray(0x8000)
    rom[:3] = bytes((0xC3, 0, 1))
    rom[0x100:0x100 + len(code)] = code
    rom[0x7FF0:0x7FF8] = b'TMR SEGA'
    rom[0x7FFF] = 0x4C  # Export SMS, 32 KiB.
    return rom


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    args = parser.parse_args()
    lib = C.CDLL(str(args.core.resolve()))
    variables = {}
    with tempfile.TemporaryDirectory(prefix='gaw-sms-fixture-') as temporary:
        directory = temporary.encode()
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
                return C.cast(data, C.POINTER(C.c_uint))[0] in (0, 1, 2)
            if command == 16:
                entries = C.cast(data, C.POINTER(Variable))
                i = 0
                while entries[i].key:
                    variables[entries[i].key] = entries[i].value.decode().split('; ', 1)[1].split('|', 1)[0].encode()
                    i += 1
                variables[b'genesis_plus_gx_system_hw'] = b'master system II'
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
            pass

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
            return 0

        callbacks = {'environment': environment, 'video_refresh': video, 'audio_sample': sample,
                     'audio_sample_batch': batch, 'input_poll': poll, 'input_state': input_state}
        for name, callback in callbacks.items():
            setter = getattr(lib, 'retro_set_' + name)
            setter.argtypes = [type(callback)]
            setter(callback)
        lib.retro_init()
        lib.retro_load_game.argtypes = [C.POINTER(GameInfo)]
        lib.retro_load_game.restype = C.c_bool
        lib.retro_get_memory_data.argtypes = [C.c_uint]
        lib.retro_get_memory_data.restype = C.c_void_p
        lib.retro_get_memory_size.argtypes = [C.c_uint]
        lib.retro_get_memory_size.restype = C.c_size_t
        rom = Path(temporary) / 'fixture.sms'
        comparisons = 0
        try:
            for mode in range(4):
                for y in range(256):
                    rom.write_bytes(fixture(y, mode))
                    info = GameInfo(str(rom).encode(), None, 0, None)
                    assert lib.retro_load_game(C.byref(info)), 'Core rejected the generated SMS fixture'
                    try:
                        lib.retro_set_controller_port_device(0, 1)
                        assert lib.retro_get_memory_size(2) == 0x2000, 'Fixture is not SMS'
                        memory = (C.c_uint8 * 0x2000).from_address(lib.retro_get_memory_data(2))
                        for _ in range(80):
                            lib.retro_run()
                        assert memory[0x12] == 0x5A and memory[0x11] >= 3, ('fixture boot', mode, y, memory[0x11])
                        top = y + 1 - (256 if y > 208 else 0)
                        height = (16 if mode & 2 else 8) * (2 if mode & 1 else 1)
                        want = 0x20 if y != 208 and top < 192 and top + height > 0 else 0
                        got = memory[0x10]
                        assert got == want, ('SMS collision', mode, y, got, want)
                        comparisons += 1
                    finally:
                        lib.retro_unload_game()
                print('SMS II collision mode %d: all 256 Y values match' % mode)
        finally:
            lib.retro_deinit()
        print('Independent SMS sprite collision tests: OK (%d generated Z80 fixtures)' % comparisons)


if __name__ == '__main__':
    main()
