"""09EE: indirect actor descriptors, cumulative coordinates and tile bases."""
import hashlib
import json
from actor_reference import ROOT


def descriptor(rom, entity):
    def word(address):
        offset = 0x30000 + (address & 0x3fff)
        return int.from_bytes(rom[offset:offset+2], 'little')
    table = int.from_bytes(entity[8:10], 'little')
    directions = word(table + entity[10]*2)
    frame_address = word(directions + entity[11]*2)
    start = 0x30000 + (frame_address & 0x3fff)
    count = rom[start] & 0x7f
    assert 0 < count <= 16
    return rom[start:start+3+count*3], frame_address


def entity_sprites(rom, entity):
    frame, address = descriptor(rom, entity)
    count = frame[0] & 127
    x, y = entity[0x13], entity[0x11]
    tile_base = 0 if frame[0] & 128 else entity[2]
    sprites = []
    for index in range(count):
        y = (y + frame[3+index]) & 255
        x = (x + frame[3+count+index*2]) & 255
        tile = (tile_base + frame[4+count+index*2]) & 255
        sprites.append((x, y, tile))
    return sprites, frame[1:3], address


def main():
    rom = (ROOT / 'input/original.sms').read_bytes()
    captures = ROOT / 'validation/sms-vertical-check'
    if not captures.exists():
        captures = ROOT / 'validation/sms-vertical'
    capture = json.loads((captures / 'capture.json').read_text())
    assert capture['rom_sha256'] == hashlib.sha256(rom).hexdigest()
    checked = 0
    addresses = set()
    for number in range(3101,3161):
        ram = (captures / f'ram_{number:05}.bin').read_bytes()
        entities = [ram[0x300+n*0x30:0x330+n*0x30] for n in range(32)]
        active = [n for n, entity in enumerate(entities) if entity[3] & 1]
        # 097E: insertion sort descending Y; lower entity index wins ties.
        active.sort(key=lambda n: (-entities[n][0x11], n))
        sprites = []
        for index in active:
            batch, collision, address = entity_sprites(rom, entities[index])
            assert entities[index][0x1b:0x1d] == collision, (number,index,'collision')
            sprites.extend(batch)
            addresses.add(address)
        ys = bytes(item[1] for item in sprites) + b'\xd0'
        xy = bytes(value for x, _, tile in sprites for value in (x,tile))
        assert ram[0x1d40:0x1d40+len(ys)] == ys, (number,'Y list')
        assert ram[0x1d80:0x1d80+len(xy)] == xy, (number,'X/tile list')
        checked += len(sprites)
    report = dict(source_sha256=capture['rom_sha256'], checked_frames=60,
                  checked_sprites=checked, descriptors=sorted(addresses),
                  sprite_lists_exact=True, collision_indices_exact=True,
                  behavior_inputs='Source entity states; native simulation remains unported')
    (ROOT / 'analysis/sprite_descriptor_reference.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
