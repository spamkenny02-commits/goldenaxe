"""Freeze the native pattern decoder proof and its production regressions."""
import hashlib
import json
from pathlib import Path
from actor_reference import ROOT

def main():
    folder=ROOT/'analysis/native-patterns-v0198'
    paths=['megadrive/src/source_pattern.c','megadrive/src/source_pattern.h',
           'tools/validate_native_patterns.py','tools/validate_pattern_production.py','tools/validate_native_patterns_68k.py',
           'tools/graphics_prefix_phase.py','tools/actor_loading_cost.py',
           'analysis/native_patterns_report.json','analysis/native_patterns_68k_report.json',
           'analysis/native_patterns_milestone.md','validation/native-patterns/vectors.json',
           'validation/native-patterns/baseline_close_report.json',
           'validation/natural_start_menu_sfx_report.json','validation/pattern_production_report.json',
           'validation/native-patterns/kernel/src/main.c',
           'validation/native-patterns/kernel/src/expected.h',
           'validation/native-patterns/kernel/out/release/rom.bin']
    manifest=[]
    for name in paths:
        raw=(ROOT/name).read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==raw,('Immutable archive differs',name)
        else:target.write_bytes(raw)
        manifest.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Archived',len(manifest),'proof files; source and kernel retained locally.')

if __name__=='__main__':main()
