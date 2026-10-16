"""Natural controller regression for New Game/Continue cursor and confirm sounds."""
import contextlib, hashlib, io, json, re
from pathlib import Path
from run_core import run

ROOT = Path(__file__).resolve().parents[1]

def main():
    symbols = {m[2].split('.lto_priv.')[0]: int(m[1], 16) & 65535
               for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
               if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
    source = (ROOT/'input/original.sms').read_bytes()
    assert source[0x1559:0x155e] == bytes.fromhex('2108de3695')
    assert source[0x1560:0x1565] == bytes.fromhex('3eab3208de')
    cases = []
    for region in ['auto', 'pal']:
        for choice in ['new', 'continue']:
            presses = [(200,220,0),(920,935,0),
                       (1100,1104,5),(1200,1204,5),
                       (1300,1304,4),(1400,1404,4)]
            if choice == 'continue': presses.append((1500,1504,5))
            presses.append((1600,1604,0))
            results = {}
            for tag, rom in [('sms',ROOT/'input/original.sms'), ('md',ROOT/'gaw-megadrive.bin')]:
                records = {}; psg = {}
                def observe(frame, ram):
                    if frame < 1000: return
                    records[frame] = (bytes(ram[0x1e00:0x1f90]) if tag == 'sms' else
                                      bytes(ram[(symbols['sound_ram']+i)^1] for i in range(400)))
                folder = ROOT/f'validation/start-menu-sfx/{choice}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,1700,folder,{1090,1550,1680},presses,skip_intro=False,
                        core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll',
                        ram_observer=observe,psg_observer=lambda f,p:psg.update({f:p}),
                        core_options={'genesis_plus_gx_region_detect':region})
                def active(record): return any(record[i]&128 for i in [0x100,0x130,0x160])
                events = [(f,r[15]) for f,r in records.items()
                          if r[15] in [0x95,0xab] and active(r)
                          and not active(records.get(f-1,bytes(400)))]
                expected = [(1100,0x95),(1300,0x95)]
                if choice == 'continue': expected.append((1500,0x95))
                expected.append((1600,0xab))
                print(region,choice,tag,'events',events,flush=True)
                assert len(events) == len(expected),(region,choice,tag,events)
                for (frame,command),(wanted,code) in zip(events,expected):
                    assert command == code and wanted <= frame <= wanted+8,(tag,events,expected)
                    # Diagnostic core exports linear amplitudes (zero is mute).
                    assert any(any(records[f][offset]&128 and psg[f][volume] > 0
                                   for offset,volume in [(0x100,3),(0x130,5),(0x160,7)])
                               for f in range(frame,frame+10)),(tag,'muted effect',command)
                (folder/'reader-records.bin').write_bytes(b''.join(records.values()))
                results[tag] = dict(events=events,frames=len(records),audible_effects=True)
            assert results['sms']['events'] == results['md']['events']
            cases.append(dict(region=region,choice=choice,results=results))
    report = dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,
                  natural_controller_input=True,ram_injections=False,
                  same_choice_presses_silent=True,full_game_ported=False,
                  limits=['Checks natural effect dispatch and audible PSG with music in PAL/NTSC.',
                          'Exact effect sequences are covered separately by validate_sfx; waveform equivalence is not claimed.'])
    (ROOT/'validation/natural_start_menu_sfx_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__ == '__main__': main()
