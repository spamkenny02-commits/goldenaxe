"""Freeze clocked prefix proofs and corrected pattern work; keep old archive intact."""
import hashlib
import json
from actor_reference import ROOT
from validate_native_graphics_prefix import MODULES

def main():
    folder=ROOT/'analysis/native-graphics-prefix-v0198';paths=set()
    for name in [*MODULES,'source_pattern']:
        for suffix in ['c','h']:
            path=ROOT/'megadrive/src'/f'{name}.{suffix}'
            if path.exists():paths.add(path.relative_to(ROOT).as_posix())
    paths.update(['tools/validate_native_graphics_prefix.py','tools/validate_native_graphics_prefix_68k.py',
                  'tools/validate_native_patterns.py','tools/validate_native_patterns_68k.py',
                  'tools/graphics_prefix_phase.py','tools/graphics_prefix_refresh.py','tools/actor_loading_cost.py',
                  'tools/validate_native_source_wait.py','tools/run_core.py',
                  'analysis/native_graphics_prefix_report.json','analysis/native_graphics_prefix_68k_report.json',
                  'analysis/native_graphics_prefix_milestone.md','analysis/native_patterns_report.json',
                  'analysis/native_patterns_68k_report.json','validation/native-graphics-prefix/cases.json',
                  'validation/native-graphics-prefix/wrapper.c','validation/native-patterns/vectors.json',
                  'validation/build-pattern-clock.log'])
    for base in ['validation/native-graphics-prefix/kernel','validation/native-patterns/kernel']:
        for relative in ['src/main.c','src/wrapper.c','src/expected.h','out/release/rom.bin','out/release/symbol.txt','build.log']:
            if (ROOT/base/relative).exists():paths.add(f'{base}/{relative}')
    for row in json.loads((ROOT/'analysis/native_graphics_prefix_report.json').read_text())['rows']:
        base=f"validation/graphics-prefix-refresh/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['foreground-phase-records.bin','foreground-m1-records.bin','cycle-events.json','audio-irq-events.json']:
            paths.add(f"{base}/{row['region']}-{suffix}")
    manifest=[]
    for name in sorted(paths):
        raw=(ROOT/name).read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==raw,('Immutable archive differs',name)
        else:target.write_bytes(raw)
        manifest.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    target=folder/'manifest.json';raw=(json.dumps(manifest,indent=2)+'\n').encode()
    if target.exists():assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    print('Archived',len(manifest),'proof files; originals and compiled kernels retained locally.')

if __name__=='__main__':main()
