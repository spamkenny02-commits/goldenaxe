"""Freeze room/HUD chain, source data captures and exhaustive HUD value proofs."""
import hashlib
import json
from actor_reference import ROOT
from validate_native_room_hud import MODULES

def main():
    folder=ROOT/'analysis/native-room-hud-v0198';paths=set()
    for name in MODULES:
        for suffix in ['c','h']:
            path=ROOT/'megadrive/src'/f'{name}.{suffix}'
            if path.exists():paths.add(path.relative_to(ROOT).as_posix())
    paths.update(['tools/validate_native_room_hud.py','tools/validate_native_room_hud_68k.py',
                  'tools/build_roomhud_data_core.py','tools/validate_roomhud_source_data.py',
                  'tools/validate_native_hud_values.py','tools/validate_native_hud_values_68k.py',
                  'tools/validate_hud_loading_cost.py','tools/map_hud_phase.py','tools/hud_loading_cost.py',
                  'tools/room_map_loading_cost.py','analysis/native_room_hud_report.json',
                  'analysis/native_room_hud_68k_report.json','analysis/native_room_hud_milestone.md',
                  'analysis/roomhud_source_data_report.json','analysis/native_hud_values_report.json',
                  'analysis/native_hud_values_68k_report.json',
                  'analysis/roomhud-data-observer-v0198/z80-roomhud-data.txt',
                  'validation/native-room-hud/cases.json','validation/native-room-hud/wrapper.c',
                  'validation/native-hud-values/vectors.bin','validation/native-hud-values/wrapper.c',
                  'validation/hud-loading-cost/source.sms','validation/build-native-room-hud.log',
                  'validation/roomhud-data-core-build.log'])
    bases=['validation/native-room-hud/kernel']
    bases.extend(p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'validation/native-hud-values').glob('part-*')))
    for base in bases:
        for relative in ['src/main.c','src/wrapper.c','src/expected.h','out/release/rom.bin','out/release/symbol.txt','build.log']:
            paths.add(f'{base}/{relative}')
    for row in json.loads((ROOT/'analysis/native_room_hud_report.json').read_text())['rows']:
        base=f"validation/wait-refresh/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['foreground-phase-records.bin','foreground-m1-records.bin','hud-context-records.bin','cycle-events.json','audio-irq-events.json']:
            paths.add(f"{base}/{row['region']}-{suffix}")
        base=f"validation/roomhud-source-data/{row['town']:02x}-{row['mask']:02x}/{row['region']}"
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
