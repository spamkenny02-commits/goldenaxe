#!/usr/bin/env python3
"""Run a private native ROM in a libretro core without a graphical frontend.

Requires a locally built Genesis Plus GX .so and the corresponding MD ELF.
No game input or screenshots are downloaded or distributed by this script.
"""
import argparse
import bisect
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
    parser.add_argument('--reference-sms', action='store_true', help='Run an original SMS ROM as a hardware reference')
    parser.add_argument('--play-inputs', type=Path, help='JSON list of {ticks, buttons} controller steps after entering gameplay')
    parser.add_argument('--combat', action='store_true', help='Record observed attacks, HP losses and enemy deaths during gameplay')
    parser.add_argument('--profile', action='store_true', help='Profile gameplay instructions using a locally instrumented core')
    parser.add_argument('--sram-in', type=Path, help='Import logical 32 KiB SRAM before boot (native MD only)')
    parser.add_argument('--sram-out', type=Path, help='Export logical 32 KiB SRAM after the run (native MD only)')
    parser.add_argument('--save-slot', type=int, choices=range(3), help='Activate the save service from gameplay, then drive its menus with controller input')
    parser.add_argument('--expect-save-slot', type=int, choices=range(3), help='Check boot selection and restored save payload before scene entry')
    args = parser.parse_args()
    if args.reference_sms and any((args.sram_in, args.sram_out, args.save_slot is not None, args.expect_save_slot is not None)):
        parser.error('SRAM scenarios currently require the native MD image')
    if args.expect_save_slot is not None and not args.sram_in:
        parser.error('--expect-save-slot requires --sram-in')
    if args.save_slot is not None and args.play_inputs:
        parser.error('--save-slot and --play-inputs are separate scenarios')
    if args.profile and args.reference_sms:
        parser.error('--profile requires the native 68000 image')
    args.output.mkdir(parents=True, exist_ok=True)
    buttons = {'up': 4, 'down': 5, 'left': 6, 'right': 7, 'button1': 0, 'button2': 8, 'pause': 3}
    inputs = json.loads(args.play_inputs.read_text()) if args.play_inputs else []
    for step in inputs:
        assert isinstance(step['ticks'], int) and step['ticks'] > 0
        if 'expect_cell' in step:
            assert isinstance(step['expect_cell'], int) and 0 <= step['expect_cell'] < 0x200
        if 'expect_state' in step:
            assert isinstance(step['expect_state'], int) and 0 <= step['expect_state'] < 256
        if 'pulse' in step:
            assert isinstance(step['pulse'], bool)
        if 'pulse_buttons' in step:
            assert isinstance(step['pulse_buttons'], list) and step['pulse_buttons']
            assert all(name in ('button1', 'button2') for name in step['pulse_buttons'])
            step['pulse_pad'] = sum(1 << buttons[name] for name in set(step['pulse_buttons']))
            step['pulse_held'] = sum({'button1': 16, 'button2': 32}[name] for name in set(step['pulse_buttons']))
        if 'expect_saved_slot' in step:
            assert isinstance(step['expect_saved_slot'], int) and 0 <= step['expect_saved_slot'] < 3
            if args.reference_sms:
                parser.error('Logical SRAM assertions currently require the native MD image')
        step['pad'] = sum(1 << buttons[name] for name in set(step['buttons']))
    symbols = {}
    code_symbols = []
    if not args.reference_sms:
        for line in subprocess.check_output([args.nm, '-n', str(args.elf)], text=True).splitlines():
            fields = line.split()
            if len(fields) == 3:
                symbols[fields[2]] = int(fields[0], 16)
                if fields[1] in ('t', 'T'):
                    code_symbols.append((int(fields[0], 16), fields[2]))
    base = 0 if args.reference_sms else symbols['gaw_ram']-0xFF0000
    lib = C.CDLL(str(args.core.resolve()))
    if args.profile:
        for name in ('gaw_profile_begin', 'gaw_profile_end', 'gaw_profile_get_cycles'):
            if not hasattr(lib, name):
                parser.error('Profiler unavailable: run tools/instrument_gpgx.py and rebuild the core')
        lib.gaw_profile_get_cycles.restype = C.POINTER(C.c_uint64)
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
    memory_size = lib.retro_get_memory_size(2)
    assert memory_size == (0x2000 if args.reference_sms else 0x10000), 'Unexpected work RAM size'
    memory = (C.c_uint8*memory_size).from_address(lib.retro_get_memory_data(2))
    sram = None
    loaded_save = None
    if args.sram_in or args.sram_out or args.save_slot is not None or any('expect_saved_slot' in step for step in inputs):
        assert lib.retro_get_memory_size(0) == 0x10000, 'Expected Genesis Plus GX SRAM backing'
        sram = (C.c_uint8*0x10000).from_address(lib.retro_get_memory_data(0))
        if args.sram_in:
            logical = args.sram_in.read_bytes()
            assert len(logical) == 0x8000, 'Logical SRAM must contain exactly 32768 bytes'
            # The pinned core byte handlers index SRAM by physical address,
            # unlike its word-swapped 68000 work RAM. Our cartridge uses odd bytes.
            for offset, value in enumerate(logical):
                sram[offset*2+1] = value
            if args.expect_save_slot is not None:
                assert logical[0x30] == args.expect_save_slot+1, 'Unexpected last-save slot'
                at = 0x400*(args.expect_save_slot+1)
                loaded_save = logical[at:at+0x250]
                assert loaded_save[0], 'Expected an occupied save slot'
    # Genesis Plus GX stores 68000 words in host byte order on little-endian hosts.
    byte_swap = int(sys.byteorder == 'little' and not args.reference_sms)
    def read(at):
        return memory[(base+at-0xC000)^byte_swap]
    def write(at, value):
        memory[(base+at-0xC000)^byte_swap] = value
    save_started = save_completed = restore_checked = False
    save_metadata = None
    def irq_counts():
        result = {}
        for name in ('vblank', 'async_vblank', 'line'):
            symbol = 'gaw_md_'+name+'_count'
            if symbol in symbols:
                at = symbols[symbol]-0xFF0000
                result[name] = int.from_bytes(bytes(memory[(at+i)^byte_swap] for i in range(4)), 'big')
        return result
    stages = []
    last_state = None
    play_frames = 0
    play_ticks = 0
    ticks = 0
    old_tick = None
    play_irq_start = None
    input_step = 0
    input_ticks = 0
    input_started = False
    input_log = []
    world_transitions = []
    last_cell = None
    profiling = False
    combat = {'attacks': [], 'player_hits': [], 'enemy_hits': [], 'enemy_deaths': [], 'encounters': [], 'projectiles': []}
    previous_combat = None
    def combat_snapshot():
        return [{'slot': slot, 'type': read(0xC300+slot*48), 'state': read(0xC301+slot*48),
                 'flags': read(0xC303+slot*48), 'saved_type': read(0xC307+slot*48),
                 'hp': read(0xC318+slot*48), 'flash': read(0xC305+slot*48),
                 'attack': read(0xC319+slot*48), 'defense': read(0xC31A+slot*48),
                 'position': [read(0xC313+slot*48), read(0xC311+slot*48)]}
                for slot in range(32)]
    for frame in range(args.frames):
        current['frame'] = frame
        state = read(0xC01D)
        if args.save_slot is not None and state == 0x0C and not save_started:
            # Controlled integration entry: service arrival is injected; every
            # confirmation, slot selection and SRAM write runs in production code.
            write(0xC036, args.save_slot+1)
            write(0xC0A7, 0)
            write(0xC0BB, read(0xC0B9))
            write(0xC0BC, read(0xC0BA))
            write(0xC01D, 0x16)
            state = 0x16
            save_started = True
            save_metadata = {'slot': args.save_slot, 'hp': read(0xC318),
                             'cell': read(0xC0BB)|(read(0xC0BC)<<8),
                             'currency': read(0xC0DD), 'name': [read(0xC0B0+i) for i in range(8)]}
        if args.save_slot is not None and save_started and not save_completed:
            current['pad'] = 1 << 8 if read(0xC020) == 0 else 0
        elif inputs and (input_started or state == 0x0C):
            input_started = True
            current['pad'] = inputs[input_step]['pad'] if input_step < len(inputs) else 0
            if input_step < len(inputs) and inputs[input_step].get('pulse') and read(0xC020):
                current['pad'] = 0
            elif input_step < len(inputs) and 'pulse_buttons' in inputs[input_step]:
                step = inputs[input_step]
                if read(0xC020) & step['pulse_held']:
                    current['pad'] &= ~step['pulse_pad']
        elif not args.observe_only and state != 0x0C:
            current['pad'] = 1 << 8 if read(0xC020) == 0 else 0  # MD C = SMS button 2
        else:
            current['pad'] = 0
        if args.profile and not profiling and state == 0x0C:
            lib.gaw_profile_begin()
            profiling = True
        lib.retro_run()
        state = read(0xC01D)
        if save_started and state == 0x0C and not save_completed:
            save_completed = True
            at = 0x400*(args.save_slot+1)
            block = bytes(sram[2*(at+i)+1] for i in range(0x250))
            assert sram[0x30*2+1] == args.save_slot+1, 'Save service did not persist the selected slot'
            assert list(block[:8]) == save_metadata['name'], 'Saved name differs'
            assert block[0x29] == save_metadata['hp'], 'Saved HP differs'
            assert int.from_bytes(block[0x12:0x14], 'little') == save_metadata['cell'], 'Saved return cell differs'
            assert block[0x2D] == save_metadata['currency'], 'Saved currency differs'
        if loaded_save is not None and state == 6 and not restore_checked:
            restored = bytes(read(0xC0B0+i) for i in range(0x250))
            expected = bytearray(loaded_save)
            expected[0x10:0x12] = expected[0x12:0x14]  # continue restores position metadata
            assert restored == expected, 'Continue did not restore the complete 592-byte save payload'
            assert read(0xC318) == loaded_save[0x29], 'Continue did not restore HP'
            assert read(0xC036) == args.expect_save_slot+1, 'Continue selected the wrong slot'
            restore_checked = True
        cell = read(0xC0B9)|(read(0xC0BA)<<8)
        if state == 0x0C or last_cell is not None:
            if cell != last_cell:
                world_transitions.append({'emulator_frame': frame, 'cell': cell, 'state': f'{state:02X}'})
                last_cell = cell
        if args.combat:
            snapshot = combat_snapshot()
            if state == 0x0C:
                stamp = {'emulator_frame': frame, 'game_frame': read(0xC02F), 'cell': cell}
                if previous_combat is None or previous_combat[0] != cell:
                    combat['encounters'].append({**stamp, 'entities': snapshot})
                else:
                    previous = previous_combat[1]
                    player, old_player = snapshot[0], previous[0]
                    if player['state'] in (3, 5) and player['state'] != old_player['state']:
                        combat['attacks'].append({**stamp, 'pose': player['state'], 'position': player['position']})
                    if player['type'] == old_player['type'] == 2 and player['hp'] < old_player['hp']:
                        related = read(0xC31E)|(read(0xC31F)<<8)
                        attacker_slot = (related-0xC300)//48 if 0xC300 <= related < 0xC900 and (related-0xC300)%48 == 0 else None
                        attacker = previous[attacker_slot] if attacker_slot is not None else None
                        combat['player_hits'].append({**stamp, 'before': old_player['hp'], 'after': player['hp'], 'flash': player['flash'],
                                                      'attacker_slot': attacker_slot,
                                                      'attacker_type': attacker['type'] if attacker else None,
                                                      'attacker_attack': attacker['attack'] if attacker else None})
                    for entity, old in zip(snapshot[1:], previous[1:]):
                        if entity['slot'] >= 24 and old['type'] == 0 and 16 <= entity['type'] <= 23:
                            combat['projectiles'].append({**stamp, 'slot': entity['slot'], 'type': entity['type'], 'attack': entity['attack']})
                        if old['type'] < 32 or not old['flags'] & 0x20:
                            continue
                        if entity['type'] == old['type'] and entity['hp'] < old['hp']:
                            combat['enemy_hits'].append({**stamp, 'slot': entity['slot'], 'type': old['type'],
                                                         'before': old['hp'], 'after': entity['hp']})
                        if entity['type'] == 1 and entity['hp'] == 0 and entity['saved_type'] == old['type']:
                            combat['enemy_hits'].append({**stamp, 'slot': entity['slot'], 'type': old['type'],
                                                         'before': old['hp'], 'after': 0})
                            combat['enemy_deaths'].append({**stamp, 'slot': entity['slot'], 'type': old['type'], 'before': old['hp']})
                previous_combat = (cell, snapshot)
            else:
                previous_combat = None  # Scene teardown must not count as damage/death.
        if state != last_state:
            entry = {'emulator_frame': frame, 'state': f'{state:02X}', 'game_frame': read(0xC02F)}
            stages.append(entry)
            print(entry, flush=True)
            last_state = state
            if current['image']:
                png(args.output/f'state_{state:02x}_{frame}.png', *current['image'], pixel_format)
        tick = read(0xC02F)
        if old_tick is not None:
            elapsed = (tick-old_tick)&255
            ticks += elapsed
            if state == 0x0C:
                play_ticks += elapsed
            if input_started and input_step < len(inputs):
                input_ticks += elapsed
                if input_ticks >= inputs[input_step]['ticks']:
                    input_log.append({'step': input_step, 'emulator_frame': frame, 'state': f'{state:02X}',
                                      'position': [read(0xC313), read(0xC311)], 'player_state': read(0xC301),
                                      'world_cell': cell,
                                      'held': read(0xC020), 'pressed': read(0xC021)})
                    if 'expect_cell' in inputs[input_step]:
                        expected = inputs[input_step]['expect_cell']
                        assert cell == expected, f'Controller step {input_step}: cell {cell:03X}, expected {expected:03X}'
                    step = inputs[input_step]
                    if 'expect_state' in step:
                        assert state == step['expect_state'], f'Controller step {input_step}: state {state:02X}, expected {step["expect_state"]:02X}'
                    if 'expect_saved_slot' in step:
                        slot = step['expect_saved_slot']
                        at = 0x400*(slot+1)
                        block = bytes(sram[2*(at+i)+1] for i in range(0x250))
                        assert sram[0x30*2+1] == slot+1, 'Controller route did not save to the expected slot'
                        assert block[0], 'Controller route saved an empty name'
                        assert list(block[:8]) == [read(0xC0B0+i) for i in range(8)], 'Controller route saved the wrong name'
                        assert block[0x29] == read(0xC318), 'Controller route saved the wrong HP'
                        assert block[0x2D] == read(0xC0DD), 'Controller route saved the wrong currency'
                        assert block[0x12:0x14] == bytes((read(0xC0BB), read(0xC0BC))), 'Controller route saved the wrong return cell'
                        input_log[-1]['saved_slot'] = slot
                        input_log[-1]['saved_hp'] = block[0x29]
                        input_log[-1]['saved_return_cell'] = int.from_bytes(block[0x12:0x14], 'little')
                    if current['image']:
                        png(args.output/f'input_{input_step:02d}.png', *current['image'], pixel_format)
                    input_step += 1
                    input_ticks = 0
        old_tick = tick
        if state == 0x0C:
            if play_irq_start is None:
                play_irq_start = irq_counts()
            play_frames += 1
        if frame % 600 == 599:
            print({'emulator_frame': frame, 'state': f'{state:02X}', 'game_ticks': ticks,
                   'audio_peak': current['audio_peak'],
                   'pc': f'{lib.m68k_get_reg(16):06X}' if not args.reference_sms and hasattr(lib, 'm68k_get_reg') else None}, flush=True)
            if current['image']:
                png(args.output/'latest.png', *current['image'], pixel_format)
        if play_frames >= 300 and input_step == len(inputs):
            break
    if current['image']:
        png(args.output/'final.png', *current['image'], pixel_format)
    memory_copy = bytes(memory[i^byte_swap] for i in range(memory_size))
    (args.output/'work_ram.bin').write_bytes(memory_copy)
    result = {'emulator_frames': frame+1, 'game_ticks': ticks, 'stages': stages,
              'play_frames': play_frames, 'play_ticks': play_ticks, 'audio_frames': current['audio_frames'],
              'audio_peak': current['audio_peak'], 'world_cell': read(0xC0B9)|(read(0xC0BA)<<8),
              'player_hp': read(0xC318), 'audio_timing_mode': read(0xDE03),
              'world_transitions': world_transitions, 'final_state': f'{read(0xC01D):02X}'}
    if args.combat:
        combat['final_entities'] = combat_snapshot()
        result['combat'] = combat
    if irq_counts():
        result['hardware_irqs'] = irq_counts()
        if play_irq_start is not None:
            result['play_irqs'] = {name: count-play_irq_start[name] for name, count in irq_counts().items()}
    if sram is not None:
        logical = bytes(sram[2*i+1] for i in range(0x8000))
        if args.sram_out:
            args.sram_out.write_bytes(logical)
        result['sram'] = {'save_completed': save_completed, 'restore_checked': restore_checked,
                          'last_slot': logical[0x30], 'save_metadata': save_metadata}
    if inputs:
        result['input_steps'] = input_log
    if profiling:
        lib.gaw_profile_end()
        counters = lib.gaw_profile_get_cycles()
        code_symbols.sort()
        addresses = [at for at, name in code_symbols]
        costs = {}
        instructions = []
        for pc in range(0, min(args.rom.stat().st_size, 0x100000), 2):
            cost = counters[pc >> 1]
            if cost:
                instructions.append((pc, cost))
                index = bisect.bisect_right(addresses, pc)-1
                name = code_symbols[index][1] if index >= 0 else 'before_first_symbol'
                costs[name] = costs.get(name, 0)+cost
        total = sum(costs.values())
        result['instruction_profile'] = {
            'master_cycles': total,
            'functions': [{'name': name, 'cycles': cost, 'percent': round(cost*100/total, 3)}
                          for name, cost in sorted(costs.items(), key=lambda entry: -entry[1])],
            'instructions': [{'pc': f'{pc:06X}', 'cycles': cost, 'percent': round(cost*100/total, 3)}
                             for pc, cost in sorted(instructions, key=lambda entry: -entry[1])[:64]]
        }
    (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result)
    lib.retro_unload_game()
    lib.retro_deinit()
    if not args.observe_only:
        if args.save_slot is not None:
            assert save_completed, 'Save service did not finish'
        if args.expect_save_slot is not None:
            assert restore_checked, 'Continue restoration was not observed'
        assert play_frames >= 300, 'Did not reach stable gameplay'
        assert play_ticks >= 24, 'Gameplay did not advance'
        assert result['final_state'] == '0C', 'Scenario did not finish in gameplay'
        assert current['audio_peak'] > 1024, 'No audible PSG output beyond boot noise'
        assert input_step == len(inputs), 'Controller scenario did not finish'
        if result.get('play_irqs'):
            assert result['play_irqs']['vblank'] >= 295, 'Hardware VBlank servicing stalled during gameplay'


if __name__ == '__main__':
    main()
