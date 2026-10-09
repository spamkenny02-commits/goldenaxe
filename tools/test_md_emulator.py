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

from dungeon_driver import DungeonDriver
from emulator_report import console_summary


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
    parser.add_argument('--boss-arena', type=int, choices=(99,100,101,103,104,105,106,107,108,109), help='Controlled equipped checkpoint in a real boss room; fight and collect reward using controller input only')
    parser.add_argument('--late-boss-controller', action='store_true', help='Exercise the large-boss spacing controller in an isolated real arena')
    parser.add_argument('--boss-weapon', choices=('axe','sword'), default='axe', help='Initial weapon for the controlled boss checkpoint')
    parser.add_argument('--boss-weapon-probe', action='store_true', help='Run a bounded sword-immunity probe without requiring boss defeat')
    parser.add_argument('--complete-ending', action='store_true', help='Continue final-boss combat through credits, confirmation and return to title')
    parser.add_argument('--dungeon', type=int, choices=range(1,11), help='Traverse a dungeon from its overworld entry checkpoint, defeat the boss and return outside (or play the final ending)')
    parser.add_argument('--dungeon-start-room', type=lambda v:int(v,16), choices=(0x13C,0x14B,0x15A), help='Separate dungeon10 suffix test from an equipped room checkpoint; never a full-entry proof')
    parser.add_argument('--miniboss-spacing', action='store_true', help='Dungeon10 controller probe: approach type123 from checked left axe reach')
    parser.add_argument('--adaptive-miniboss', action='store_true', help='Dungeon10 controller probe: use a reachable alternate mini-boss flank and avoid its attack phases')
    parser.add_argument('--weapon-speed-equipment', action='store_true', help='Dungeon10 entrance fixture: include the original C0EE weapon-speed equipment')
    parser.add_argument('--shield-first', action='store_true', help='Dungeon10 controller probe: prioritize active shields in17D and18A')
    parser.add_argument('--late-shield-first', action='store_true', help='Dungeon10 controller probe: prioritize active shields only in18A')
    parser.add_argument('--late-ice', action='store_true', help='Dungeon10 controller probe: freeze type81 in13C before melee')
    parser.add_argument('--caster-ice', action='store_true', help='Dungeon10 controller probe: freeze curse casters before melee')
    parser.add_argument('--late-retreat', action='store_true', help='Dungeon10 controller probe: retreat from invulnerable enemies in 13C')
    parser.add_argument('--caster-room-retreat', action='store_true', help='Dungeon10 controller probe: retreat from flashing enemies in 14A')
    parser.add_argument('--late-retreat-window', type=int, choices=(0,8), default=0, help='Hero flash threshold for --late-retreat (0: wait until vulnerable; 8: preemptive retreat)')
    parser.add_argument('--live-targets', action='store_true', help='Dungeon10 controller: do not pursue actors whose spawn position is still zero')
    parser.add_argument('--late-live-targets', action='store_true', help='Dungeon10 controller: apply spawn-position filtering in13C and15C')
    parser.add_argument('--collect-before-exit', action='store_true', help='Dungeon10 controller: wait for enemy death animations and collect real health/magic drops')
    parser.add_argument('--potion-first', action='store_true', help='Dungeon10 controller probe: conserve magic by using the potion before healing spells')
    parser.add_argument('--final-magic-reserve', type=int, choices=(0,8,16,24), default=0, help='Dungeon10 controller probe: reserve MP after13C for the ice-trigger passage in15B')
    parser.add_argument('--caster-axe-margin', type=int, choices=(2,4), default=4, help='Dungeon10 controller probe: body margin for low-magic caster melee in14A')
    parser.add_argument('--late-terrain-awareness', action='store_true', help='Dungeon10 controller probe: penalize damaging terrain in14A')
    parser.add_argument('--flash-ice', action='store_true', help='Dungeon10 controller probe: allow close ice shots in13C during hero invulnerability')
    parser.add_argument('--late-melee-geometry', action='store_true', help='Dungeon10 controller probe: avoid unsafe81/96 body approaches in13C before hero flash expires')
    parser.add_argument('--boss-projectile-window', type=int, choices=(0,4,8,12,16), default=0, help='Late boss controller probe: anticipate projectile danger before hero flash expires')
    parser.add_argument('--boss-projectile-distance', type=int, choices=(32,48,64), default=48, help='Late boss controller probe: distance at which an active projectile triggers retreat')
    parser.add_argument('--invulnerable-boss-wait', action='store_true', help='Late boss controller probe: hold attack reach while hero flash outlasts boss flash')
    parser.add_argument('--patient-boss', action='store_true', help='Late-dungeon controller probe: wait for stationary boss phases and use a wider body margin')
    args = parser.parse_args()
    if args.dungeon_start_room is not None and args.dungeon!=10:
        parser.error('--dungeon-start-room requires dungeon 10')
    dungeon_route = None
    if args.dungeon is not None:
        if args.boss_arena is not None or args.boss_weapon_probe:
            parser.error('--dungeon selects its own boss')
        dungeon_route = next(r for r in json.loads((Path(__file__).resolve().parent.parent/'tests/scenarios/dungeon_routes.json').read_text()) if r['index']==args.dungeon)
        args.boss_arena = dungeon_route['boss']['type']
        args.complete_ending = args.dungeon==10
        if args.patient_boss:dungeon_route['patient_boss']=True
        if args.miniboss_spacing:dungeon_route['miniboss_spacing']=True
        if args.adaptive_miniboss:
            dungeon_route['miniboss_spacing']=True
            dungeon_route['adaptive_miniboss']=True
        if args.shield_first:dungeon_route['shield_cells']=(0x17D,0x18A)
        if args.late_shield_first:dungeon_route['shield_cells']=(0x18A,)
        if args.late_ice:dungeon_route['late_ice']=True
        if args.caster_ice:dungeon_route['caster_ice']=True
        if args.late_retreat:
            dungeon_route['late_retreat']=True
            dungeon_route['late_retreat_window']=args.late_retreat_window
        if args.caster_room_retreat:dungeon_route['caster_room_retreat']=True
        if args.live_targets:dungeon_route['live_targets']=True
        if args.late_live_targets:dungeon_route['late_live_targets']=True
        if args.collect_before_exit:dungeon_route['collect_before_exit']=True
        if args.final_magic_reserve:dungeon_route['final_magic_reserve']=args.final_magic_reserve
        if args.caster_axe_margin!=4:dungeon_route['caster_axe_margin']=args.caster_axe_margin
        if args.late_terrain_awareness:dungeon_route['damage_terrain_cells']=(0x14A,)
        if args.flash_ice:dungeon_route['flash_ice']=True
        if args.late_melee_geometry:dungeon_route['late_melee_geometry']=True
        if args.boss_projectile_window:dungeon_route['boss_projectile_window']=args.boss_projectile_window
        if args.boss_projectile_distance!=48:dungeon_route['boss_projectile_distance']=args.boss_projectile_distance
        if args.invulnerable_boss_wait:dungeon_route['invulnerable_boss_wait']=True
        if args.dungeon_start_room is not None:
            start=next(i for i,e in enumerate(dungeon_route['outbound']) if e['from']==args.dungeon_start_room)
            dungeon_route['outbound']=dungeon_route['outbound'][start:]
    if (args.miniboss_spacing or args.adaptive_miniboss) and args.dungeon!=10:
        parser.error('--miniboss-spacing requires dungeon 10')
    if args.weapon_speed_equipment and args.dungeon!=10:
        parser.error('--weapon-speed-equipment requires dungeon 10')
    if (args.shield_first or args.late_shield_first or args.late_ice or args.caster_ice or args.late_retreat or args.caster_room_retreat or args.live_targets or args.late_live_targets or args.collect_before_exit) and args.dungeon!=10:
        parser.error('Late controller probes require dungeon 10')
    if args.potion_first and args.dungeon!=10:
        parser.error('--potion-first requires dungeon 10')
    if args.final_magic_reserve and args.dungeon!=10:
        parser.error('--final-magic-reserve requires dungeon 10')
    if args.caster_axe_margin!=4 and args.dungeon!=10:
        parser.error('--caster-axe-margin requires dungeon 10')
    if args.late_terrain_awareness and args.dungeon!=10:
        parser.error('--late-terrain-awareness requires dungeon 10')
    if args.flash_ice and args.dungeon!=10:
        parser.error('--flash-ice requires dungeon 10')
    if args.late_melee_geometry and args.dungeon!=10:
        parser.error('--late-melee-geometry requires dungeon 10')
    if args.boss_projectile_window and args.dungeon not in (9,10):
        parser.error('--boss-projectile-window requires dungeon 9 or 10')
    if args.boss_projectile_distance!=48 and args.dungeon not in (9,10):
        parser.error('--boss-projectile-distance requires dungeon 9 or 10')
    if args.invulnerable_boss_wait and args.dungeon not in (9,10):
        parser.error('--invulnerable-boss-wait requires dungeon 9 or 10')
    if args.patient_boss and args.dungeon not in (9,10):
        parser.error('--patient-boss requires dungeon 9 or 10')
    if args.late_boss_controller and args.boss_arena not in (108,109):
        parser.error('--late-boss-controller requires boss 108 or 109')
    if args.reference_sms and any((args.sram_in, args.sram_out, args.save_slot is not None, args.expect_save_slot is not None)):
        parser.error('SRAM scenarios currently require the native MD image')
    if args.expect_save_slot is not None and not args.sram_in:
        parser.error('--expect-save-slot requires --sram-in')
    if args.save_slot is not None and args.play_inputs:
        parser.error('--save-slot and --play-inputs are separate scenarios')
    if args.profile and args.reference_sms:
        parser.error('--profile requires the native 68000 image')
    if args.boss_weapon_probe and (args.boss_arena!=109 or args.boss_weapon!='sword'):
        parser.error('--boss-weapon-probe requires --boss-arena 109 --boss-weapon sword')
    if args.boss_arena is not None and any((args.play_inputs,args.save_slot is not None,args.sram_in,args.sram_out)):
        parser.error('--boss-arena is a separate controlled checkpoint scenario')
    if args.complete_ending and (args.boss_arena!=109 or args.boss_weapon_probe):
        parser.error('--complete-ending requires the final axe boss scenario')
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
        assert args.boss_arena is None or not boss_prepared, 'Work RAM writes after boss fixture are forbidden'
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
    combat = {'attacks': [], 'player_hits': [], 'enemy_hits': [], 'enemy_deaths': [], 'encounters': [], 'ready_encounters': [], 'projectiles': [], 'curse_changes': [], 'resource_changes': []}
    def resource_snapshot():
        return {'hp':read(0xC318),'mp':read(0xC0DB),'item':read(0xC0DF),
                'environment':read(0xC041),'player_state':read(0xC301),
                'position':[read(0xC313),read(0xC311)]}
    previous_combat = None
    previous_curse = None
    ready_cell = None
    def combat_snapshot():
        return [{'slot': slot, 'type': read(0xC300+slot*48), 'state': read(0xC301+slot*48),
                 'flags': read(0xC303+slot*48), 'saved_type': read(0xC307+slot*48),
                 'hp': read(0xC318+slot*48), 'flash': read(0xC305+slot*48),
                 'attack': read(0xC319+slot*48), 'defense': read(0xC31A+slot*48),
                 'direction':read(0xC30A+slot*48),
                 'hitbox_source':read(0xC31B+slot*48),'hitbox_target':read(0xC31C+slot*48),
                 'position': [read(0xC313+slot*48), read(0xC311+slot*48)]}
                for slot in range(32)]
    arenas=json.loads((Path(__file__).resolve().parent.parent/'tests/scenarios/boss_arenas.json').read_text())
    arena=next((entry for entry in arenas if entry['type']==args.boss_arena),None)
    boss_index=arena['index'] if arena else None
    boss_weapon=1 if args.boss_weapon=='axe' else 0
    boss_run = {'fixture': None, 'phases': [], 'hits': [], 'deaths': [], 'projectiles': [], 'reward_spawned': False, 'reward_collected': False, 'heals': [], 'satellites_spawned': [], 'satellites_killed': [], 'parts_spawned': []}
    boss_prepared = False
    dungeon = DungeonDriver(dungeon_route,read,buttons) if dungeon_route else None
    if args.dungeon_start_room is not None:dungeon.stage='outbound'
    arena_driver= DungeonDriver({'index':9,'avoid':{}},read,buttons) if args.late_boss_controller else None
    previous_boss = None
    previous_aux = None
    boss_done = False
    ending = {'started': False, 'credits_started': False, 'credits_finished': False, 'returned_to_title': False, 'scroll_values': [], 'crystal_slots': [], 'audio_commands': []}
    boss_heal_stage = 'fight'
    boss_inventory_goal = None
    boss_heal_mp = None
    def drive_boss():
        nonlocal boss_heal_stage,boss_inventory_goal,boss_heal_mp
        def pulse(name,mask):
            return 0 if read(0xC020)&mask else 1<<buttons[name]
        if state==0x10:
            goal=boss_inventory_goal
            if read(0xC0DF)==goal:
                return pulse('button1',16)
            cursor=read(0xC0A0)
            if cursor==goal:return pulse('button2',32)
            if cursor//4!=goal//4:
                return pulse('down' if cursor//4<goal//4 else 'up',2 if cursor//4<goal//4 else 1)
            return pulse('right' if cursor%4<goal%4 else 'left',8 if cursor%4<goal%4 else 4)
        if args.complete_ending and ending['returned_to_title'] and state==0:
            return pulse('button2',32)
        if state==0x0E and args.complete_ending:
            return pulse('button2',32) if ending['credits_finished'] else 0
        if state!=0x0C:return 0
        desired_weapon=dungeon.desired_item() if dungeon and dungeon.stage!='boss' else boss_weapon
        if boss_heal_stage=='fight' and read(0xC0DF)!=desired_weapon:
            boss_inventory_goal=desired_weapon;boss_heal_stage='select_weapon'
        heal_cost=24 if not dungeon or args.dungeon in (9,10) else 32
        heal_reserve=dungeon.magic_reserve() if dungeon else 0
        can_heal=read(0xC0E7) and read(0xC0DB)>=heal_cost+heal_reserve
        if boss_heal_stage=='fight' and read(0xC318)<=24 and (read(0xC600)==args.boss_arena or dungeon):
            goal=7 if dungeon and can_heal else 8 if read(0xC0E8) else 7 if can_heal else None
            if args.potion_first and read(0xC0E8):goal=8
            if goal is not None:
                boss_inventory_goal=goal;boss_heal_mp=read(0xC0DB);boss_heal_stage='select_heal'
        if boss_heal_stage=='select_heal':
            if read(0xC0DF)==boss_inventory_goal:boss_heal_stage='cast_heal'
            else:return pulse('button1',16)
        if boss_heal_stage=='cast_heal':
            consumed=(boss_inventory_goal==8 and not read(0xC0E8)) or (boss_inventory_goal==7 and read(0xC0DB)<boss_heal_mp)
            if consumed:
                boss_inventory_goal=desired_weapon;boss_heal_stage='select_weapon'
            else:return pulse('button2',32) if read(0xC301)==1 else 0
        if boss_heal_stage=='select_weapon':
            if read(0xC0DF)==desired_weapon:boss_heal_stage='fight'
            else:return pulse('button1',16)
        if dungeon and not dungeon.done:
            pad = dungeon.drive(state,boss_done)
            if pad is not None:return pad
        # Decisions inspect live positions, but apply only joypad buttons.
        kind = read(0xC600)
        if kind==0 and read(0xC0CE+boss_index)==0x80:
            return pulse('button2',32)  # Confirm the production reward dialogue (SMS).
        if kind == 7 or kind == 0:
            return 0
        px,py = read(0xC313),read(0xC311)
        tx,ty = read(0xC613),read(0xC611)
        if args.boss_arena == 101 and kind == 101:
            children = [(read(0xC313+slot*48),read(0xC311+slot*48)) for slot in range(24,32) if read(0xC300+slot*48)==102 and read(0xC303+slot*48)&2]
            if children:
                tx,ty = min(children,key=lambda v:abs(v[0]-px)+abs(v[1]-py))
        dx,dy = tx-px,ty-py
        if kind in (108,109) and (args.dungeon in (9,10) or arena_driver):
            return (dungeon or arena_driver).boss_melee()
        if abs(dx)>abs(dy):
            direction='right' if dx>0 else 'left'
        else:
            direction='down' if dy>0 else 'up'
        facing={'up':0,'down':1,'left':2,'right':3}[direction]
        melee_range=40 if args.dungeon in (9,10) else 16 if dungeon else 28
        if dungeon and abs(dx)+abs(dy)>melee_range:
            return dungeon.navigate([round(tx/8)*8,round(ty/8)*8])
        pad=0 if kind!=15 and abs(dx)+abs(dy)<=melee_range and read(0xC30A)==facing else 1<<buttons[direction]
        if kind != 15 and abs(dx)+abs(dy)<(48 if args.dungeon in (9,10) else 42) and read(0xC020)&32==0:
            pad |= 1<<buttons['button2']
        return pad
    for frame in range(args.frames):
        current['frame'] = frame
        state = read(0xC01D)
        if args.boss_arena is not None and state == 0x0C and not boss_prepared:
            # One-time fixture: resume/scene loader constructs the real encounter.
            cell=args.dungeon_start_room if args.dungeon_start_room is not None else dungeon_route['outside_cell'] if dungeon else arena['cell']
            for at in (0xC0C0,0xC0C4):
                write(at,cell&255);write(at+1,cell>>8)
            write(0xC037,0 if dungeon and args.dungeon_start_room is None else boss_index)
            write(0xC0DA,128);write(0xC318,128)
            write(0xC0E0,3);write(0xC0E1,2);write(0xC0DF,0 if dungeon else boss_weapon)
            write(0xC0F1,3);write(0xC0F2,3)
            write(0xC0E7,1);write(0xC0E8,1);write(0xC0DC,120);write(0xC0DB,120)
            if dungeon:
                write(0xC0DE,20);write(0xC0DC,128);write(0xC0DB,128)
                write(0xC0E2,1)  # One ordinary antidote in the equipped checkpoint.
                write(0xC0E7,2)
                write(0xC0E4,2);write(0xC0E5,2);write(0xC0E6,2)
                write(0xC0EC,1);write(0xC0ED,1);write(0xC0F0,1 if args.dungeon in (6,9) else 0)
                if args.weapon_speed_equipment:write(0xC0EE,1)
                for index in range(1,args.dungeon):write(0xC0CE+index,0x80)
            write(0xC01D,6);state=6;boss_prepared=True
            boss_run['fixture']={'cell':cell,'type':args.boss_arena,'index':boss_index,'hp':128,'item':0 if dungeon else boss_weapon,'axe_level':2,'armor_level':3,'shield_level':3,'heal_magic_level':2 if dungeon else 1,'potion':1,'antidote':1 if dungeon else 0,'mp':128 if dungeon else 120}
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
        elif args.boss_arena is not None and boss_prepared:
            current['pad'] = drive_boss()
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
        resources_before=resource_snapshot() if args.combat else None
        lib.retro_run()
        state = read(0xC01D)
        if args.combat:
            resources_after=resource_snapshot()
            if resources_after['mp']!=resources_before['mp'] or resources_after['hp']!=resources_before['hp']:
                combat['resource_changes'].append({'emulator_frame':frame,
                    'cell':read(0xC0B9)|(read(0xC0BA)<<8),'state':state,
                    'before':resources_before,'after':resources_after})
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
        if args.boss_arena is not None and boss_prepared and state==0x0C and (not dungeon or cell==arena['cell']):
            snapshot=combat_snapshot();boss=snapshot[16]
            if (not boss_run['phases'] or (boss_run['phases'][-1]['type'],boss_run['phases'][-1]['state'])!=(boss['type'],boss['state'])):
                boss_run['phases'].append({'emulator_frame':frame,**boss})
            if previous_boss is not None:
                if previous_boss['type']==args.boss_arena and boss['hp']<previous_boss['hp']:
                    boss_run['hits'].append({'emulator_frame':frame,'before':previous_boss['hp'],'after':boss['hp'],'type':boss['type'],'flash':boss['flash']})
                if previous_boss['type']==args.boss_arena and boss['type']==7:
                    boss_run['deaths'].append({'emulator_frame':frame,'before':previous_boss['hp'],'after':boss['hp']})
            if previous_aux is not None:
                for entity,old in zip(snapshot[24:],previous_aux):
                    if old['type']==0 and entity['type']==102:
                        boss_run['satellites_spawned'].append({'emulator_frame':frame,**entity})
                    if old['type']==102 and entity['type']==1 and entity['saved_type']==102:
                        boss_run['satellites_killed'].append({'emulator_frame':frame,**entity})
                    if old['type']==0 and 112<=entity['type']<=119:
                        boss_run['projectiles'].append({'emulator_frame':frame,**entity})
            if args.boss_arena==103 and not boss_run['parts_spawned'] and all(e['type']==103 for e in snapshot[17:22]):
                boss_run['parts_spawned']=snapshot[17:22]
            if boss['type']==15:boss_run['reward_spawned']=True
            if read(0xC0CE+boss_index)==0x80:
                boss_run['reward_collected']=True
                if read(0xC301)==0:boss_run['reward_acknowledged']=True
                boss_done = boss_run['reward_spawned'] and boss_run.get('reward_acknowledged',False) and boss['type']==0 and read(0xC301)==1 and read(0xC318)==read(0xC0DA)
            if previous_boss is not None and previous_boss['type']==args.boss_arena and read(0xC318)>boss_run.get('last_hp',read(0xC318)):
                boss_run['heals'].append({'emulator_frame':frame,'before':boss_run['last_hp'],'after':read(0xC318),'mp':read(0xC0DB),'item':read(0xC0DF)})
            boss_run['last_hp']=read(0xC318)
            previous_boss=boss;previous_aux=snapshot[24:]
        if args.boss_arena is not None and boss_prepared and boss_index==10 and state==0x0E:
            boss_run['ending_handoff']=True;boss_done=not args.complete_ending
        if args.complete_ending and boss_run.get('ending_handoff'):
            if not ending['started']:
                ending['started']=True;ending['start_frame']=frame
            cmd=read(0xC065)
            if not ending['audio_commands'] or ending['audio_commands'][-1]!=cmd:ending['audio_commands'].append(cmd)
            for slot in range(16,25):
                if read(0xC300+slot*48)==6 and read(0xC303+slot*48)&1 and slot not in ending['crystal_slots']:ending['crystal_slots'].append(slot)
            ptr=read(0xDCC6)|(read(0xDCC7)<<8)
            if state==0x0E and 0xC900<ptr<0xCE00:
                ending['credits_started']=True
                y=read(0xC019)
                if y not in ending['scroll_values']:ending['scroll_values'].append(y)
            if state==0x0E and ending['credits_started']:
                if read(0xDCC1)==1:
                    ending['credits_finished']=True
                    if 'finish_frame' not in ending:ending['finish_frame']=frame
            if ending['credits_finished'] and state in (0,0x12):
                ending['returned_to_title']=True
                if 'return_frame' not in ending:ending['return_frame']=frame
                if state==0x12:ending['title_confirmed']=True;boss_done=True
        if args.combat:
            snapshot = combat_snapshot()
            curse=read(0xC0BF)
            if previous_curse is not None and curse!=previous_curse:
                combat['curse_changes'].append({'emulator_frame':frame,'cell':cell,
                    'before':previous_curse,'after':curse,'state':state,
                    'antidotes':read(0xC0E2),'player':snapshot[0],
                    'casters':[e for e in snapshot[16:24] if e['type']==83]})
            previous_curse=curse
            if state == 0x0C:
                stamp = {'emulator_frame': frame, 'game_frame': read(0xC02F), 'cell': cell}
                if ready_cell!=cell and snapshot[0]['hitbox_source'] and any(
                        e['type']>=32 and e['flags']&2 and e['hitbox_source'] for e in snapshot[16:24]):
                    combat['ready_encounters'].append({**stamp,'entities':snapshot})
                    ready_cell=cell
                if previous_combat is None or previous_combat[0] != cell:
                    combat['encounters'].append({**stamp, 'entities': snapshot})
                else:
                    previous = previous_combat[1]
                    player, old_player = snapshot[0], previous[0]
                    if player['state'] in (3, 5) and player['state'] != old_player['state']:
                        combat['attacks'].append({**stamp, 'pose': player['state'], 'position': player['position'],
                                                  'direction':player['direction'],'hitbox_target':player['hitbox_target']})
                    if player['type'] == old_player['type'] == 2 and player['hp'] < old_player['hp']:
                        related = read(0xC31E)|(read(0xC31F)<<8)
                        attacker_slot = (related-0xC300)//48 if 0xC300 <= related < 0xC900 and (related-0xC300)%48 == 0 else None
                        attacker = previous[attacker_slot] if attacker_slot is not None else None
                        if attacker and not attacker['type']:attacker=None
                        combat['player_hits'].append({**stamp, 'before': old_player['hp'], 'after': player['hp'], 'flash': player['flash'],
                                                      'environment':read(0xC041),
                                                      'attacker_slot': attacker_slot,
                                                      'attacker_type': attacker['type'] if attacker else None,
                                                      'attacker_attack': attacker['attack'] if attacker else None,
                                                      'player_direction':player['direction'],'player_position':player['position'],
                                                      'attacker_direction':attacker['direction'] if attacker else None,
                                                      'attacker_position':attacker['position'] if attacker else None,
                                                      'player_before':{'position':old_player['position'],
                                                          'direction':old_player['direction'],'defense':old_player['defense'],
                                                          'hitbox_source':old_player['hitbox_source']},
                                                      'attacker_hitbox_target':attacker['hitbox_target'] if attacker else None})
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
            if dungeon:print({'dungeon':args.dungeon,'route_stage':dungeon.stage,'edge':dungeon.edge,'cell':f'{cell:03X}','xy':[read(0xC313),read(0xC311)],'hp':read(0xC318),'mp':read(0xC0DB),'item':read(0xC0DF),'requested_item':dungeon.desired_item(),'curse':read(0xC0BF),'antidotes':read(0xC0E2),'keys':read(0xC0DE)},flush=True)
            print({'emulator_frame': frame, 'state': f'{state:02X}', 'game_ticks': ticks,
                   'audio_peak': current['audio_peak'],
                   'pc': f'{lib.m68k_get_reg(16):06X}' if not args.reference_sms and hasattr(lib, 'm68k_get_reg') else None}, flush=True)
            if current['image']:
                png(args.output/'latest.png', *current['image'], pixel_format)
        if dungeon and boss_prepared and read(0xC318)==0:
            break  # Preserve the first fatal frame instead of idling to the cap.
        if (boss_done and (not dungeon or dungeon.done or ending.get('title_confirmed',False))) or (args.boss_arena is None and play_frames >= 300 and input_step == len(inputs)):
            break
    if current['image']:
        png(args.output/'final.png', *current['image'], pixel_format)
    memory_copy = bytes(memory[i^byte_swap] for i in range(memory_size))
    (args.output/'work_ram.bin').write_bytes(memory_copy)
    result = {'emulator_frames': frame+1, 'game_ticks': ticks, 'stages': stages,
              'play_frames': play_frames, 'play_ticks': play_ticks, 'audio_frames': current['audio_frames'],
              'audio_peak': current['audio_peak'], 'world_cell': read(0xC0B9)|(read(0xC0BA)<<8),
              'player_hp': read(0xC318), 'audio_timing_mode': read(0xDE03),
              'world_transitions': world_transitions, 'final_state': f'{read(0xC01D):02X}',
              'controller': {'potion_first':args.potion_first,'final_magic_reserve':args.final_magic_reserve,'patient_boss':args.patient_boss,'miniboss_spacing':args.miniboss_spacing,'shield_first':args.shield_first,'late_shield_first':args.late_shield_first,'late_ice':args.late_ice,'late_retreat':args.late_retreat,'live_targets':args.live_targets,'late_live_targets':args.late_live_targets,'collect_before_exit':args.collect_before_exit}}
    if args.boss_arena is not None:
        boss_run['final_item']=read(0xC0DF);boss_run['final_mp']=read(0xC0DB);boss_run['potion_remaining']=read(0xC0E8)
        boss_run['final_entities']=combat_snapshot();boss_run['progress']=read(0xC0CE+boss_index) if boss_prepared else None
        result['boss']=boss_run
        if args.complete_ending:result['ending']=ending
        if dungeon:result['dungeon']={'index':args.dungeon,'start_room':args.dungeon_start_room,'stage':dungeon.stage,'edge':dungeon.edge,'visits':dungeon.visits,'events':dungeon.events,'done':dungeon.done,'keys_remaining':read(0xC0DE),'route':dungeon_route}
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
    print(json.dumps(console_summary(result, args.output/'result.json')), flush=True)
    lib.retro_unload_game()
    lib.retro_deinit()
    if not args.observe_only and not args.boss_weapon_probe:
        if args.save_slot is not None:
            assert save_completed, 'Save service did not finish'
        if args.expect_save_slot is not None:
            assert restore_checked, 'Continue restoration was not observed'
        if args.boss_arena is not None:
            assert boss_done, 'Boss fight/reward did not finish'
            if args.complete_ending:
                assert ending['credits_started'] and ending['credits_finished'] and ending.get('title_confirmed'), 'Ending did not complete'
                assert set(ending['crystal_slots'])==set(range(16,25)), 'Nine ending crystals were not shown'
                assert len(ending['scroll_values'])>150, 'Credit scroll stalled'
            assert boss_run['hits'] and boss_run['deaths'], 'No genuine boss damage/death observed'
            assert result['player_hp']>0, 'Player died in boss encounter'
            if dungeon:assert dungeon.done or ending['returned_to_title'], 'Dungeon traversal did not finish'
            assert boss_run['reward_collected'] or boss_run.get('ending_handoff'), 'Missing reward/ending handoff'
            return
        assert play_frames >= 300, 'Did not reach stable gameplay'
        assert play_ticks >= 24, 'Gameplay did not advance'
        assert result['final_state'] == '0C', 'Scenario did not finish in gameplay'
        assert current['audio_peak'] > 1024, 'No audible PSG output beyond boot noise'
        assert input_step == len(inputs), 'Controller scenario did not finish'
        if result.get('play_irqs'):
            assert result['play_irqs']['vblank'] >= 295, 'Hardware VBlank servicing stalled during gameplay'


if __name__ == '__main__':
    main()
