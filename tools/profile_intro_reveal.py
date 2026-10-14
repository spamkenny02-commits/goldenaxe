"""Measure first-scene reveal progress in hardware VRAM, without game mutations."""
import contextlib
import hashlib
import io
import json
from collections import Counter
from actor_reference import ROOT
from run_core import run


def main():
    regions = {}
    for pal in (False, True):
        suffix = '-pal' if pal else ''
        systems = {}
        for md in (False, True):
            tag = 'md' if md else 'sms'
            events = []
            previous = None
            passes = []
            starts = []
            masks = [127, 63, 31, 15, 7, 3, 1, 0]

            def observe(frame, vram):
                nonlocal previous
                if md:
                    # Genesis VRAM in the core's serialized VDP state is
                    # byte-addressed, with each 16-bit word host-swapped.
                    raw = bytearray(vram[512:512+0x2400])
                    raw[::2], raw[1::2] = raw[1::2], raw[::2]
                    rows = []
                    for offset in range(0, len(raw), 4):
                        value = 0
                        for byte in raw[offset:offset+4]:
                            value = (value << 2) | ((byte >> 6) & 2) | ((byte >> 3) & 1)
                        rows.append(value)
                else:
                    rows = vram[3:0x2400:4]
                histogram = sorted(Counter(rows).items())
                if len(passes) < 8:
                    mask = masks[len(passes)]
                    rotated = mask
                    pattern = []
                    for n in range(4):
                        pattern.append(rotated)
                        rotated = ((rotated >> 2) | (rotated << 6)) & 255
                    if list(rows[:4]) == pattern:
                        if len(starts) == len(passes):
                            starts.append(frame)
                        if list(rows) == pattern*576:
                            if md:
                                planar = bytearray(0x2400)
                                for row in range(0x900):
                                    for pixel in range(8):
                                        byte = raw[row*4+pixel//2]
                                        color = (byte >> (0 if pixel & 1 else 4)) & 15
                                        for plane in range(4):
                                            planar[row*4+plane] |= ((color >> plane) & 1) << (7-pixel)
                            else:
                                planar = vram[:0x2400]
                            passes.append(dict(mask=mask, start_frame=starts[-1], end_frame=frame,
                                               planar_sha256=hashlib.sha256(planar).hexdigest()))
                key = (tuple(rows[:8]), tuple(rows[-8:]), tuple(histogram))
                if key != previous:
                    events.append(dict(frame=frame, first_rows=list(rows[:8]),
                                       last_rows=list(rows[-8:]), histogram=histogram))
                    previous = key

            rom = ROOT/('gaw-megadrive.bin' if md else 'input/original.sms')
            with contextlib.redirect_stdout(io.StringIO()):
                run(rom, 150, ROOT/f'validation/{tag}-intro-reveal-profile{suffix}',
                    set(), [], skip_intro=False, vram_observer=observe,
                    core_options={'genesis_plus_gx_region_detect': 'pal' if pal else 'auto'})
            assert len(passes) == 8, (tag, suffix, passes)
            assert [p['start_frame']-passes[0]['start_frame'] for p in passes] == list(range(0,40,5))
            assert all(p['end_frame']-p['start_frame'] == 4 for p in passes)
            systems[tag] = dict(events=events, passes=passes)
        assert [p['planar_sha256'] for p in systems['sms']['passes']] == [p['planar_sha256'] for p in systems['md']['passes']]
        differences = []
        for source, native in zip(systems['sms']['passes'], systems['md']['passes']):
            mask = source['mask']
            values = set()
            for n in range(4):
                values.add(mask)
                mask = ((mask >> 2) | (mask << 6)) & 255
            counts = []
            for tag, p in [('sms', source), ('md', native)]:
                rows_per_frame = []
                for frame in range(p['start_frame'], p['end_frame']+1):
                    event = next(e for e in reversed(systems[tag]['events']) if e['frame'] <= frame)
                    rows_per_frame.append(sum(n for v, n in event['histogram'] if v in values))
                counts.append(rows_per_frame)
            differences.extend(y-x for x, y in zip(*counts))
        systems['comparison'] = dict(
            start_offset_frames=systems['md']['passes'][0]['start_frame']-systems['sms']['passes'][0]['start_frame'],
            completed_pass_patterns_exact=True, pass_cadence_frames=5,
            relative_updated_rows_difference_range=[min(differences), max(differences)],
            partial_frame_patterns_exact=False, absolute_start_timing_exact=False)
        regions['pal' if pal else 'ntsc'] = systems
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  no_ram_mutations=True, no_buttons=True, hardware_vram=True, regions=regions)
    path = ROOT/'analysis/intro_reveal_profile.json'
    path.write_text(json.dumps(report, indent=2)+'\n')
    for region, systems in regions.items():
        for tag, system in systems.items():
            if tag == 'comparison':
                continue
            print(region, tag, [(p['mask'],p['start_frame'],p['end_frame']) for p in system['passes']])


if __name__ == '__main__':
    main()
