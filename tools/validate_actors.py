"""Verify the native room loader's entity records and prepared SMS tiles."""
import hashlib
import json
import re
from actor_reference import ROOT, load_room_actors


def main():
    rom = (ROOT / 'input/original.sms').read_bytes()
    target = ROOT / 'validation/md-vertical'
    capture = json.loads((target / 'capture.json').read_text())
    assert not capture.get('test_ram_writes'), 'Native loader validation requires an uninjected run'
    assert capture['rom_sha256'] == hashlib.sha256((ROOT / 'gaw-megadrive.bin').read_bytes()).hexdigest()
    symbols = {}
    for line in (ROOT / 'megadrive/out/release/symbol.txt').read_text().splitlines():
        match = re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line)
        if match:
            symbols[match[2].split('.lto_priv.')[0]] = int(match[1], 16) & 65535
    checked = []
    for frame in (3000,3071,3097,3160):
        raw = (target / f'ram_{frame:05}.bin').read_bytes()
        ram = bytes(value for n in range(0, len(raw), 2) for value in (raw[n+1], raw[n]))
        def word(name):
            address = symbols[name]
            return int.from_bytes(ram[address:address+2], 'big')
        room = word('room_id')
        expected, patterns, allocation, count, _ = load_room_actors(rom, room)
        start = symbols['world_actor_state']
        if frame<=3071:
            assert ram[start:start+len(expected)] == expected, ('initial entity records',frame)
            checked_entity_bytes=len(expected)
        else:
            checked_entity_bytes=0
            for slot in range(8):
                for field in (0,2,0x18,0x19,0x1a):
                    offset=slot*0x30+field
                    assert ram[start+offset]==expected[offset], ('immutable loader field',frame,slot,field)
                    checked_entity_bytes+=1
        assert word('world_actor_tiles') == allocation, ('tile allocation', frame)
        assert word('world_actor_count') == count, ('actor count', frame)
        start = symbols['sms_vram'] + 0x2000
        size = allocation * 32
        assert ram[start:start+size] == patterns[0x2000:0x2000+size], ('prepared graphics', frame)
        raw_vram = (target / f'vram_{frame:05}.bin').read_bytes()
        vram = bytes(value for n in range(0,len(raw_vram),2)
                     for value in (raw_vram[n+1],raw_vram[n]))
        expected_vram = bytearray()
        for offset in range(0x2000, 0x2000+size, 4):
            word = 0
            for bit in range(8):
                color = sum(((patterns[offset+plane] >> bit) & 1) << plane
                            for plane in range(4))
                word |= color << (bit*4)
            expected_vram.extend(word.to_bytes(4,'big'))
        start = (16+256)*32
        assert vram[start:start+size] == expected_vram, ('Mega Drive VDP graphics',frame)
        checked.append(dict(frame=frame, room=room, entity_bytes=checked_entity_bytes,
                            prepared_pattern_bytes=size, active_count=count))
    report = dict(md_sha256=capture['rom_sha256'],
                  source_sha256=hashlib.sha256(rom).hexdigest(), native_loader_exact=True,
                  checks=checked, graphics_uploaded_to_md_vdp=True,
                  active_types_ported=[0x20,0x21,0x22,0x26,0x27,0x28],actor_simulation_complete=False,
                  progression_conditionals_ported=False,
                  source_loading_frame_timing_reproduced=False)
    (ROOT / 'validation/actor_report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
