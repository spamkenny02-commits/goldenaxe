"""Freeze full native graphics load and independent source-data proofs."""
import hashlib
import json
from actor_reference import ROOT
from validate_native_graphics_load import MODULES

def main():
    folder=ROOT/'analysis/native-graphics-load-v0198';paths=set()
    for name in MODULES:
        for suffix in ['c','h']:
            path=ROOT/'megadrive/src'/f'{name}.{suffix}'
            if path.exists():paths.add(path.relative_to(ROOT).as_posix())
    paths.update(['tools/validate_native_graphics_load.py','tools/validate_native_graphics_load_68k.py',
                  'tools/build_graphics_data_core.py','tools/validate_graphics_source_data.py',
                  'tools/graphics_load_phase.py','tools/graphics_load_refresh.py',
                  'tools/ram_plane_loading_cost.py','tools/class0_graphics_loading_cost.py',
                  'analysis/native_graphics_load_report.json','analysis/native_graphics_load_68k_report.json',
                  'analysis/native_graphics_load_milestone.md','analysis/graphics_source_data_report.json',
                  'analysis/graphics-data-observer-v0198/z80-graphics-data.txt',
                  'validation/native-graphics-load/cases.json','validation/native-graphics-load/wrapper.c',
                  'validation/build-native-graphics-load.log','validation/graphics-data-core-build.log'])
    for relative in ['src/main.c','src/wrapper.c','src/expected.h','out/release/rom.bin','out/release/symbol.txt','build.log']:
        paths.add(f'validation/native-graphics-load/kernel/{relative}')
    for row in json.loads((ROOT/'analysis/native_graphics_load_report.json').read_text())['rows']:
        base=f"validation/graphics-load-refresh/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['foreground-phase-records.bin','foreground-m1-records.bin','cycle-events.json','audio-irq-events.json']:
            paths.add(f"{base}/{row['region']}-{suffix}")
        base=f"validation/graphics-source-data/{row['town']:02x}-{row['mask']:02x}/{row['region']}"
        for suffix in ['foreground.bin','m1.bin','data-hashes.bin','capture.json']:paths.add(f'{base}/{suffix}')
    manifest=[]
    for name in sorted(paths):
        raw=(ROOT/name).read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==raw,('Immutable archive differs',name)
        else:target.write_bytes(raw)
        manifest.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    target=folder/'manifest.json';raw=(json.dumps(manifest,indent=2)+'\n').encode()
    if target.exists():assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    print('Archived',len(manifest),'proof files; captures and compiled kernel retained locally.')

if __name__=='__main__':main()
