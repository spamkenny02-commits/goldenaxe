"""Freeze native graphics/map chain, shared decoder and direct source data proofs."""
import hashlib
import json
from actor_reference import ROOT
from validate_native_world_map import MODULES

def main():
    folder=ROOT/'analysis/native-world-map-v0198';paths=set()
    for name in MODULES:
        for suffix in ['c','h']:
            path=ROOT/'megadrive/src'/f'{name}.{suffix}'
            if path.exists():paths.add(path.relative_to(ROOT).as_posix())
    paths.update(['tools/validate_native_world_map.py','tools/validate_native_world_map_68k.py',
                  'tools/build_world_data_core.py','tools/validate_world_source_data.py',
                  'tools/world_map_phase.py','tools/world_map_refresh.py','tools/world_map_loading_cost.py',
                  'tools/validate_native_graphics_load.py','tools/validate_native_graphics_load_68k.py',
                  'analysis/native_world_map_report.json','analysis/native_world_map_68k_report.json',
                  'analysis/native_world_map_milestone.md','analysis/world_source_data_report.json',
                  'analysis/native_graphics_load_report.json','analysis/native_graphics_load_68k_report.json',
                  'analysis/world-data-observer-v0198/z80-world-data.txt',
                  'validation/native-world-map/cases.json','validation/native-world-map/wrapper.c',
                  'validation/native-graphics-load/cases.json','validation/build-native-world-map.log',
                  'validation/world-data-core-build.log'])
    for base in ['validation/native-world-map/kernel','validation/native-graphics-load/kernel']:
        for relative in ['src/main.c','src/wrapper.c','src/expected.h','out/release/rom.bin','out/release/symbol.txt','build.log']:
            paths.add(f'{base}/{relative}')
    for row in json.loads((ROOT/'analysis/native_world_map_report.json').read_text())['rows']:
        base=f"validation/world-map-refresh/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['foreground-phase-records.bin','foreground-m1-records.bin','cycle-events.json','audio-irq-events.json']:
            paths.add(f"{base}/{row['region']}-{suffix}")
        base=f"validation/world-source-data/{row['town']:02x}-{row['mask']:02x}/{row['region']}"
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
    print('Archived',len(manifest),'proof files; source captures and kernels retained locally.')

if __name__=='__main__':main()
