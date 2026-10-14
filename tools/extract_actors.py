"""Export ROM room lists/stats and remapped actor tiles for the native loader."""
import hashlib
import json
from actor_reference import ROOT, load_room_actors
from actor_loading_cost import resource_cost


def main():
    rom = (ROOT / 'input/original.sms').read_bytes()
    room_types = rom[0x3234e:0x3334e]
    index = bytearray(b'\xff' * 1024)
    tiles = bytearray()
    counts = bytearray(256)
    resources = []
    for actor_type in sorted(set(room_types)):
        if actor_type < 0x20:
            continue
        room = next(room for room in range(512)
                    if actor_type in room_types[room*8:room*8+8])
        _, patterns, _, _, entries = load_room_actors(rom, room)
        entry = next(item for item in entries if item['type'] == actor_type)
        index[actor_type*4:actor_type*4+4] = len(tiles).to_bytes(4, 'big')
        counts[actor_type] = entry['tile_count']
        start = 0x2000 + entry['tile_base'] * 32
        tiles.extend(patterns[start:start + entry['tile_count'] * 32])
        resources.append(entry)
    load_costs=bytearray(256*4)
    for entry in resources:
        cost=resource_cost(rom,dict(entry,tile_base=0))['foreground_graphics_tstates']
        load_costs[entry['type']*4:entry['type']*4+4]=cost.to_bytes(4,'big')
    native_tiles = bytearray()
    for offset in range(0, len(tiles), 4):
        word = 0
        for bit in range(8):
            color = sum(((tiles[offset+plane] >> bit) & 1) << plane
                        for plane in range(4))
            word |= color << (bit*4)
        native_tiles.extend(word.to_bytes(4, 'big'))
    arrays = dict(actor_room_types=room_types,
                  actor_loading_costs=load_costs,
                  actor_stats=rom[0x320ea:0x320ea + (max(room_types)-0x20+1)*4],
                  actor_pattern_index=index, actor_tile_counts=counts,
                  actor_patterns=tiles, actor_md_patterns=native_tiles,
                  actor_descriptors=rom[0x30000:0x320ea],
                  actor_ground_modes=rom[0x87c4:0x87c7],
                  actor_spawn_terrain=rom[0x586d:0x5878],
                  actor_charge_sequence=rom[0x927f:0x9290],
                  actor_dash_vectors=rom[0x93f2:0x941a],
                  actor_lob_vectors=rom[0x4277:0x4281],
                  actor_orbit_facing=rom[0x983f:0x9843],
                  actor_homing_template=rom[0x415c:0x4182],
                  actor_fixed_placement_tables=rom[0x58bc:0x5b20],
                  actor_jumping_vectors=rom[0x8ca3:0x8d23],
                  actor_water_jump_choices=rom[0x8f3a:0x8f56],
                  actor_collision_boxes=rom[0x8100:0x8200],
                  actor_drop_exceptions=rom[0x3226d:0x322ae],
                  actor_drop_choices=rom[0x322ae:0x3234e],
                  actor_loot_patterns=rom[0x13581:0x13601]+rom[0x13601:0x13681]+rom[0x13681:0x13701],
                  actor_shield_strength=rom[0x32269:0x3226d],
                  actor_projectile_types=rom[0x85d6:0x85d9],
                  actor_projectile_templates=rom[0x3e53:0x3e69]+rom[0x3e76:0x3e8c]+rom[0x3eb6:0x3ecc]+rom[0x4013:0x4029]+rom[0x3ff0:0x4006]+rom[0x4062:0x408e]+rom[0x409b:0x40b1]+rom[0x40cb:0x40e1]+rom[0x4399:0x43af],
                  actor_mobile_sequences=rom[0x85d9:0x85fb],
                  actor_flying_sine=rom[0x8000:0x8100],
                  actor_flying_acceleration=rom[0x8750:0x8756],
                  actor_flying_facing=rom[0x8727:0x872b],
                  actor_aimed_projectile_facing=rom[0x3f4f:0x3f57],
                  actor_aimed_projectile_templates=rom[0x3f57:0x3f7d]+rom[0x3fbd:0x3fe3]+rom[0x3f8a:0x3fb0]+rom[0x428e:0x42b4]+rom[0x4366:0x438c],
                  actor_ground_sequence_index=bytes(
                      {0x87cd:0,0x85d9:17}[int.from_bytes(rom[p:p+2],'little')]
                      for p in range(0x87c7,0x87cd,2)),
                  actor_ground_sequences=rom[0x87cd:0x87de]+rom[0x85d9:0x85ea])
    lines = ['#include <genesis.h>']
    for name, data in arrays.items():
        lines += [f'const u8 {name}[] = {{']
        lines += ['    ' + ','.join(f'0x{b:02x}' for b in data[p:p+16]) + ','
                  for p in range(0, len(data), 16)]
        lines += ['};']
    (ROOT / 'megadrive/src/actor_data.c').write_text('\n'.join(lines)+'\n')
    report = dict(source_sha256=hashlib.sha256(rom).hexdigest(),
                  room_count=512, pattern_offset_bytes=4, unique_graphic_types=len(resources),
                  pattern_bytes=len(tiles), resources=resources,
                  story_conditionals_ported=False, actor_simulation_ported=False)
    (ROOT / 'analysis/actor_assets.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f"{len(resources)} graphic types, {len(tiles)} ROM-derived pattern bytes")


if __name__ == '__main__':
    main()
