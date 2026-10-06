#!/usr/bin/env python3
"""Run a private native ROM in a libretro core without a graphical frontend.

Requires a locally built Genesis Plus GX .so and the corresponding MD ELF.
No game input or screenshots are downloaded or distributed by this script.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib


class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p),
                ('size', C.c_size_t), ('meta', C.c_char_p)]


class Variable(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]


def png(path, pixels, width, height, pitch, pixel_format):
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data))
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            if pixel_format == 1:  # XRGB8888
                value = struct.unpack_from('=I', pixels, y*pitch+x*4)[0]
                r, g, b = (value>>16)&255, (value>>8)&255, value&255
            else:
                value = struct.unpack_from('=H', pixels, y*pitch+x*2)[0]
                if pixel_format == 2:  # RGB565
                    r, g, b = (value >> 11)*255//31, ((value >> 5)&63)*255//63, (value&31)*255//31
                else:  # XRGB1555
                    r, g, b = ((value >> 10)&31)*255//31, ((value >> 5)&31)*255//31, (value&31)*255//31
            rows.extend((r, g, b))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))+
                     chunk(b'IDAT', zlib.compress(rows))+chunk(b'IEND', b''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--rom', type=Path, default=Path('md/build/gaw_md.bin'))
    parser.add_argument('--elf', type=Path, default=Path('md/build/gaw_md.elf'))
    parser.add_argument('--nm', default='m68k-elf-nm')
    parser.add_argument('--frames', type=int, default=6000)
    parser.add_argument('--output', type=Path, default=Path('md/build/emulator'))
    parser.add_argument('--observe-only', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    symbols = {}
    for line in subprocess.check_output([args.nm, '-n', str(args.elf)], text=True).splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    base = symbols['gaw_ram']-0xFF0000
    lib = C.CDLL(str(args.core.resolve()))
    variables = {}
    directory = str(args.output.resolve()).encode()
    pixel_format = 0
    current = {'frame': 0, 'pad': 0, 'image': None, 'audio_frames': 0, 'audio_peak': 0}

    @C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
    def environment(command, data):
        nonlocal pixel_format
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
            pixel_format = C.cast(data, C.POINTER(C.c_uint))[0]
            return pixel_format in (0, 1, 2)
        if command == 16:
            entries = C.cast(data, C.POINTER(Variable))
            i = 0
            while entries[i].key:
                value = entries[i].value.decode().split('; ', 1)[1].split('|', 1)[0].encode()
                variables[entries[i].key] = value
                i += 1
            return True
        if command == 15:
            entry = C.cast(data, C.POINTER(Variable)).contents
            if entry.key in variables:
                entry.value = variables[entry.key]
                return True
            return False
        if command in (6, 8, 11, 13, 18, 32, 34, 35, 36, 37, 42, 44):
            return True
        return False

    @C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
    def video(data, width, height, pitch):
        if data:
            current['image'] = (C.string_at(data, pitch*height), width, height, pitch)

    @C.CFUNCTYPE(None, C.c_int16, C.c_int16)
    def sample(left, right):
        current['audio_frames'] += 1
        current['audio_peak'] = max(current['audio_peak'], abs(left), abs(right))

    @C.CFUNCTYPE(C.c_size_t, C.POINTER(C.c_int16), C.c_size_t)
    def batch(data, frames):
        current['audio_frames'] += frames
        if frames:
            values = (C.c_int16*(frames*2)).from_address(C.addressof(data.contents))
            current['audio_peak'] = max(current['audio_peak'], max(abs(v) for v in values))
        return frames

    @C.CFUNCTYPE(None)
    def poll():
        pass

    @C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
    def input_state(port, device, index, button):
        return int(port == 0 and device == 1 and bool(current['pad'] & (1 << button)))

    callbacks = {'environment': environment, 'video_refresh': video, 'audio_sample': sample,
                 'audio_sample_batch': batch, 'input_poll': poll, 'input_state': input_state}
    for name, callback in callbacks.items():
        setter = getattr(lib, 'retro_set_'+name)
        setter.argtypes = [type(callback)]
        setter(callback)
    lib.retro_init()
    lib.retro_load_game.argtypes = [C.POINTER(GameInfo)]
    lib.retro_load_game.restype = C.c_bool
    info = GameInfo(str(args.rom.resolve()).encode(), None, 0, None)
    assert lib.retro_load_game(C.byref(info)), 'Core rejected the ROM'
    lib.retro_set_controller_port_device(0, 1)
    lib.retro_get_memory_data.argtypes = [C.c_uint]
    lib.retro_get_memory_data.restype = C.c_void_p
    lib.retro_get_memory_size.argtypes = [C.c_uint]
    lib.retro_get_memory_size.restype = C.c_size_t
    assert lib.retro_get_memory_size(2) == 0x10000, 'Expected MD 64KB work RAM'
    memory = (C.c_uint8*0x10000).from_address(lib.retro_get_memory_data(2))
    # Genesis Plus GX stores 68000 words in host byte order on little-endian hosts.
    byte_swap = int(sys.byteorder == 'little')
    def read(at):
        return memory[(base+at-0xC000)^byte_swap]
    stages = []
    last_state = None
    play_frames = 0
    play_ticks = 0
    ticks = 0
    old_tick = None
    for frame in range(args.frames):
        current['frame'] = frame
        state = read(0xC01D)
        if not args.observe_only and state != 0x0C:
            current['pad'] = 1 << 8 if read(0xC020) == 0 else 0  # MD C = SMS button 2
        else:
            current['pad'] = 0
        lib.retro_run()
        state = read(0xC01D)
        if state != last_state:
            entry = {'emulator_frame': frame, 'state': f'{state:02X}', 'game_frame': read(0xC02F)}
            stages.append(entry)
            print(entry, flush=True)
            last_state = state
            if current['image']:
                png(args.output/f'state_{state:02x}_{frame}.png', *current['image'], pixel_format)
        tick = read(0xC02F)
        if old_tick is not None:
            ticks += (tick-old_tick)&255
            if state == 0x0C:
                play_ticks += (tick-old_tick)&255
        old_tick = tick
        if state == 0x0C:
            play_frames += 1
        if frame % 600 == 599:
            print({'emulator_frame': frame, 'state': f'{state:02X}', 'game_ticks': ticks,
                   'audio_peak': current['audio_peak'],
                   'pc': f'{lib.m68k_get_reg(16):06X}' if hasattr(lib, 'm68k_get_reg') else None}, flush=True)
            if current['image']:
                png(args.output/'latest.png', *current['image'], pixel_format)
        if play_frames >= 300:
            break
    if current['image']:
        png(args.output/'final.png', *current['image'], pixel_format)
    memory_copy = bytes(memory[i^byte_swap] for i in range(0x10000))
    (args.output/'work_ram.bin').write_bytes(memory_copy)
    result = {'emulator_frames': frame+1, 'game_ticks': ticks, 'stages': stages,
              'play_frames': play_frames, 'play_ticks': play_ticks, 'audio_frames': current['audio_frames'],
              'audio_peak': current['audio_peak'], 'world_cell': read(0xC0B9)|(read(0xC0BA)<<8),
              'player_hp': read(0xC318)}
    (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)
    lib.retro_unload_game()
    lib.retro_deinit()
    if not args.observe_only:
        assert play_frames >= 300, 'Did not reach stable gameplay'
        assert play_ticks >= 24, 'Gameplay did not advance'
        assert current['audio_peak'] > 1024, 'No audible PSG output beyond boot noise'


if __name__ == '__main__':
    main()
