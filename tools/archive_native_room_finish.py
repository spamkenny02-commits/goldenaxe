"""Freeze16-checkpoint native loading chain, source VRAM/palette and clock proofs."""
import hashlib
import json
from actor_reference import ROOT
from validate_native_room_finish import MODULES

def main():
    folder=ROOT/'analysis/native-room-finish-v0198';paths=set()
    old=ROOT/'analysis/native-room-hud-v0198/megadrive/src/source_clock.c'
    assert (ROOT/'megadrive/src/source_clock.c').read_bytes().startswith(old.read_bytes())
    for name in MODULES:
        for suffix in ['c','h']:
            path=ROOT/'megadrive/src'/f'{name}.{suffix}'
            if path.exists():paths.add(path.relative_to(ROOT).as_posix())
    paths.update(['tools/validate_native_room_finish.py','tools/validate_native_room_finish_68k.py',
                  'tools/build_roomfinish_data_core.py','tools/validate_roomfinish_source_data.py',
                  'tools/validate_clock_disabled_repeat.py','tools/validate_native_palette.py',
                  'tools/validate_finish_units_68k.py','tools/map_hud_phase.py','tools/map_hud_loading_cost.py',
                  'analysis/native_room_finish_report.json','analysis/native_room_finish_68k_report.json',
                  'analysis/native_room_finish_milestone.md','analysis/roomfinish_source_data_report.json',
                  'analysis/native_palette_report.json','analysis/clock_disabled_repeat_report.json',
                  'analysis/finish_units_68k_report.json',
                  'analysis/roomfinish-data-observer-v0198/z80-roomfinish-data.txt',
                  'validation/native-room-finish/cases.json','validation/native-room-finish/wrapper.c',
                  'validation/native-palette/cases.json','validation/native-palette/wrapper.c','validation/native-palette/source.sms',
                  'validation/clock-disabled-repeat/cases.json','validation/clock-disabled-repeat/wrapper.c',
                  'validation/build-native-room-finish.log','validation/roomfinish-data-core-build.log'])
    for base in ['validation/native-room-finish/kernel','validation/finish-units-68k']:
        for relative in ['src/main.c','src/wrapper.c','src/expected.h','out/release/rom.bin','out/release/symbol.txt','build.log']:
            paths.add(f'{base}/{relative}')
    for row in json.loads((ROOT/'analysis/native_room_finish_report.json').read_text())['rows']:
        base=f"validation/wait-refresh/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['foreground-phase-records.bin','foreground-m1-records.bin','hud-context-records.bin','save-wait-records.bin','cycle-events.json','audio-irq-events.json']:
            paths.add(f"{base}/{row['region']}-{suffix}")
        base=f"validation/roomfinish-source-data/{row['town']:02x}-{row['mask']:02x}/{row['region']}"
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
