"""Test-only live SMS/native actor recorder; no captured state enters the game."""
import contextlib
import io
import re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES


class ActorPair:
    def __init__(self, label, pal=False):
        self.label = label
        self.suffix = '-pal' if pal else ''
        self.options = {'genesis_plus_gx_region_detect': 'pal' if pal else 'auto'}
        self.sy = {m[2].split('.lto_priv.')[0]: int(m[1], 16)&65535
                   for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
                   if (m := re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line))}
        self.comparisons = 0

    def execute(self, md, name, frames, writes):
        frames = set(frames)
        samples = {}
        base = self.sy['world_actor_state'] if md else 0x600
        def observe(f, ram):
            if f in frames:
                samples[f] = bytes(ram[(base+n)^1] for n in range(768)) if md else ram[base:base+768]
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'), max(frames),
                ROOT/f"validation/{'md' if md else 'sms'}-{self.label}-{name}{self.suffix}", set(),
                PRESSES if md else [(200, 220, 0)]+PRESSES, ram_writes=writes,
                ram_observer=observe, core_options=self.options)
        assert set(samples) == frames
        return samples

    def compare(self, source, native, frames, slots, label):
        for f in sorted(frames):
            for slot in slots:
                x, y = source[f][slot*48:(slot+1)*48], native[f][slot*48:(slot+1)*48]
                assert x[:27]+x[29:] == y[:27]+y[29:], (
                    label, f, slot, [(n, a, b) for n, (a, b) in enumerate(zip(x, y)) if a != b])
                self.comparisons += 1
