"""Header-only checksum migration: cartridge bytes and real core execution."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from finalize_md_rom import md_checksum
from run_core import ROOT
from validate_actor_tick import PRESSES


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    validation = ROOT / 'validation'
    parent = validation / 'checksum-parent.bin'
    current = ROOT / 'gaw-megadrive.bin'
    before, after = parent.read_bytes(), current.read_bytes()
    prior = json.loads((validation / 'checksum-parent-audit.json').read_text())
    assert sha(before) == prior['md_sha256']
    assert len(before) == len(after) == 524288
    offsets = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert offsets and set(offsets) <= {0x18e, 0x18f}, offsets
    # Independent byte-slice calculation matches GX getchecksum, loadrom.c:202.
    expected = (sum(after[0x200::2]) * 256 + sum(after[0x201::2])) & 65535
    assert expected == md_checksum(after) == int.from_bytes(after[0x18e:0x190], 'big')
    assert int.from_bytes(after[0x1a4:0x1a8], 'big') == len(after) - 1
    for alias in ['gaw-title-megadrive.bin', 'megadrive/out/release/rom.bin']:
        assert (ROOT / alias).read_bytes() == after
    assert sha((ROOT / 'input/original.sms').read_bytes()) == sha(
        Path(r'D:\Cartmod\GoldenAxeWarrior\chat\Golden Axe Warrior (USA, Europe).sms').read_bytes())
    scenarios = []
    for label, frames, captures, presses, skip in [
        ('intro', 1600, {120, 600, 1000, 1600}, [], False),
        ('title', 900, {450, 700, 800, 900}, [], True),
        ('gameplay', 4000, {2000, 2800, 3100, 3500, 4000}, PRESSES, True),
    ]:
        folders = []
        for version, rom in [('parent', parent), ('current', current)]:
            folder = validation / f'checksum-{label}-{version}'
            # A fresh process avoids the core retaining stack RAM between loads.
            code = (f'from run_core import run; run({str(rom)!r}, {frames!r}, '
                    f'{str(folder)!r}, {captures!r}, {presses!r}, skip_intro={skip!r}, '
                    f'audio_out={str(folder / "audio.wav")!r})')
            subprocess.run([sys.executable, '-c', code], check=True,
                           cwd=Path(__file__).parent, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            folders.append(folder)
        compared = []
        for f in sorted(folders[0].iterdir()):
            if f.name == 'audio.wav' or f.name.startswith(('ram_', 'vram_', 'cram_', 'vdp_regs_', 'frame_')):
                assert f.read_bytes() == (folders[1] / f.name).read_bytes(), (label, f.name)
                compared.append(f.name)
        assert len(compared) == len(captures) * 5 + 1
        scenarios.append(dict(name=label, frames=frames, captures=sorted(captures),
                              identical_files=compared, test_ram_writes=[]))
        print(f'{label}: RAM, VDP, images and audio identical', flush=True)
    inherited = []
    for name in prior['current_targeted_reports']:
        raw = (validation / name).read_bytes()
        report = json.loads(raw)
        assert report['md_sha256'] == sha(before), name
        inherited.append(dict(report=name, report_sha256=sha(raw), md_sha256=sha(before)))
    report = dict(md_sha256=sha(after), md_size=len(after), parent_md_sha256=sha(before),
                  changed_offsets=offsets, md_additive_checksum=expected,
                  executable_and_asset_bytes_identical=True, original_unchanged=True,
                  rom_aliases_exact=True, core_scenarios=scenarios,
                  inherited_parent_reports=inherited, inherited_reports_rerun=False,
                  full_regression_rerun=False, full_game_ported=False)
    (validation / 'md_checksum_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Checksum {expected:04X}; {len(inherited)} parent reports retained as historical evidence')


if __name__ == '__main__':
    main()
