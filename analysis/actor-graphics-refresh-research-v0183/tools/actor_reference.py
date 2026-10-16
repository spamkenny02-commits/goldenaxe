"""Semantic reference for room actor loading (1780..18E2), from ROM only.

This covers the unmodified new-game room persistence mask. Conditional story
objects at 1805 and actor simulation/placement are deliberately separate.
"""
import hashlib
import json
from pathlib import Path
from extract_title import rle_planes

ROOT = Path(__file__).resolve().parents[1]


def remap_patterns(patterns, start, end, table):
    for offset in range(start, end, 4):
        source = patterns[offset:offset + 4]
        target = [0] * 4
        for bit in range(8):
            color = sum(((value >> bit) & 1) << plane
                        for plane, value in enumerate(source))
            for plane in range(4):
                target[plane] |= ((table[color] >> plane) & 1) << bit
        patterns[offset:offset + 4] = bytes(target)


def load_room_actors(rom, room, persistence=0xff):
    # 1786 clears 300h bytes; the room list initializes its first eight slots.
    entities = bytearray(0x300)
    table = 0x3234e + room * 8
    for slot, actor_type in enumerate(rom[table:table + 8]):
        offset = slot * 0x30
        entities[offset] = actor_type
        if actor_type >= 0x20:
            stats = 0x320ea + (actor_type - 0x20) * 4
            entities[offset + 0x18:offset + 0x1b] = rom[stats:stats + 3]
            entities[offset + 3] = rom[stats + 3]
        # RLCA enumerates persistence bit 7 first, down to bit 0.
        if not persistence & (0x80 >> slot):
            entities[offset:offset + 0x30] = bytes(0x30)
    patterns = bytearray(0x4000)
    resources = []
    loaded = {}
    next_tile = 0
    for slot in range(8):
        offset = slot * 0x30
        actor_type = entities[offset]
        if actor_type < 0x20:
            continue
        if actor_type in loaded:
            entities[offset + 2] = loaded[actor_type]
            continue
        entities[offset + 2] = next_tile
        loaded[actor_type] = next_tile
        descriptor = 0x825f + (actor_type - 0x20) * 3
        packed = rom[descriptor]
        address = int.from_bytes(rom[descriptor + 1:descriptor + 3], 'little')
        source = (packed & 15) * 0x4000 + (address & 0x3fff)
        start = 0x2000 + next_tile * 32
        stream_end, end = rle_planes(rom, source, patterns, start, 4)
        assert (end - start) % 32 == 0
        if packed & 0xf0:
            remap = 0x1da2 + (packed & 0xf0)
            remap_patterns(patterns, start, end, rom[remap:remap + 16])
        resources.append(dict(type=actor_type, bank=packed & 15,
                              rom_start=source, rom_end=stream_end,
                              palette_remap=packed & 0xf0,
                              tile_base=next_tile, tile_count=(end-start)//32))
        next_tile = (end >> 5) & 255
    active_count = sum(bool(entities[slot * 0x30]) for slot in range(8)) or 0x80
    return entities, patterns, next_tile, active_count, resources


def spawn_candidate(rom, entity, cells, hero_x, hero_y, frame_counter,
                    object_index, refresh_position, refresh_direction,
                    terrain_offset=0, terrain_count=4):
    """57F8..586C, with explicit inputs for the two LD A,R reads.

    The Z80 refresh register is an input, not a replacement PRNG. Failed
    attempts can already modify X/Y, so this mutates the 48-byte entity.
    """
    if frame_counter & 7 != object_index & 7:
        return False
    cell = ((refresh_position & 0x7f) + 0x10) & 255
    if ((cell - 1) & 15) >= 14:
        return False
    allowed = rom[0x586d + terrain_offset:0x586d + terrain_offset + terrain_count]
    if cells[cell] not in allowed:
        return False
    entity[0x13] = ((cell & 15) * 16 + 8) & 255
    if abs(hero_x - entity[0x13]) < 16:
        return False
    entity[0x11] = ((cell & 0xf0) + 16) & 255
    if abs(hero_y - entity[0x11]) < 16:
        return False
    entity[0x0a] = refresh_direction & 3
    entity[3] |= 3
    return True


def main():
    rom = (ROOT / 'input/original.sms').read_bytes()
    entities, patterns, allocation, count, resources = load_room_actors(rom, 0xa4)
    official = ROOT / 'validation/sms-vertical-check'
    instrumented = ROOT / 'validation/sms-vertical'
    captures = official if official.exists() else instrumented
    provenance = json.loads((captures / 'capture.json').read_text(encoding='utf-8'))
    assert provenance['rom_sha256'] == hashlib.sha256(rom).hexdigest()
    pre_graphics = (captures / 'ram_03071.bin').read_bytes()
    final = (captures / 'ram_03097.bin').read_bytes()
    vram = (captures / 'vram_03097.bin').read_bytes()
    # Loader characteristics precede tile allocation, which may span VBlanks.
    initial_entities = bytearray(entities)
    for offset in range(2, len(initial_entities), 0x30):
        initial_entities[offset] = 0
    assert initial_entities == pre_graphics[0x600:0x900]
    assert entities == final[0x600:0x900]
    assert final[0x67] == allocation and final[0xa2] == count
    end = 0x2000 + allocation * 32
    assert patterns[0x2000:end] == vram[0x2000:end]
    # Verify the first accepted placement independently of graphics loading.
    # Position refresh 78h is inferred from its candidate cell, not a claim
    # that the original Z80 instruction-driven refresh stream is reproduced.
    spawned = bytearray(entities[:0x30])
    spawn_ram = (captures / 'ram_03101.bin').read_bytes()
    assert spawn_candidate(rom, spawned, spawn_ram[0x1c00:0x1ca0],
                           spawn_ram[0x313], spawn_ram[0x311],
                           spawn_ram[0x2f], 16, 0x78, 2)
    for offset in (3, 0x0a, 0x11, 0x13):
        assert spawned[offset] == spawn_ram[0x600 + offset]
    report = dict(source_sha256=hashlib.sha256(rom).hexdigest(), room=0xa4,
                  resources=resources, actor_count=count, allocated_tiles=allocation,
                  checked_entity_bytes=len(entities), checked_pattern_bytes=end-0x2000,
                  initial_characteristics_exact=True, final_entities_exact=True,
                  final_patterns_exact=True,
                  first_spawn_with_explicit_refresh_inputs_exact=True,
                  z80_refresh_stream_reproduced=False,
                  complete_actor_simulation=False)
    report['reference_core'] = provenance['core']
    report['official_core_reference_exact'] = captures == official
    if official.exists() and instrumented.exists():
        other_meta = json.loads((instrumented / 'capture.json').read_text(encoding='utf-8'))
        assert other_meta['rom_sha256'] == provenance['rom_sha256']
        for filename in ('ram_03071.bin', 'ram_03097.bin', 'ram_03101.bin',
                         'vram_03097.bin'):
            assert (official / filename).read_bytes() == (instrumented / filename).read_bytes()
        report['instrumented_core_reference_exact'] = True
    (ROOT / 'analysis/actor_loading_reference.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
