"""Freeze logical-clock and source-cost evidence, then reclaim generated captures."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
def main():
    r=json.loads((ROOT/'analysis/screen_spell_clock_release_v0251_report.json').read_bytes());assert r['passed']
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest==r['md_sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==251
    marker=ROOT/'analysis/screen-spell-timing-source';assert (ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c').read_bytes()==(marker/'z80-original.txt').read_bytes()
    research=ROOT/'validation/screen-spell-clock-v0251';research.mkdir(exist_ok=True)
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_screen_spell_libretro.dll';(research/core.name).write_bytes(core.read_bytes())
    roots=[]
    for pattern in ['screen-spell-timing-*-sms','screen-spell-timing-*-md','screen-spell-cost*','screen-spell-v0251-*','screen-spell-clock-v0251']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()};paths.update(marker.iterdir())
    for pattern in ['analysis/screen_spell*.json','analysis/screen_spell_clock_v0251.md','validation/screen-spell*.log','validation/build-v025[01].log','versions/v025[01]-*/*']:
        paths.update(ROOT.glob(pattern))
    for name in ['README.md','megadrive/src/main.c','megadrive/src/screen_spell.inc','megadrive/src/source_sprite_scene_timed.c','megadrive/src/source_sprite_scene_cost.c','megadrive/src/source_sprite_scene_cost.h','megadrive/out/release/symbol.txt','tools/build_screen_spell_timing_core.py','tools/screen_spell_cost.py','tools/validate_screen_spell_cost.py','tools/validate_screen_spell.py','tools/archive_screen_spell_clock_release.py','analysis/world_next.md','validation/v0251-world-prefix.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/v0251-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/screen-spell-clock-v0251';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=251,observer_core_sha256=sha(core.read_bytes()),full_game_verified=False),roots,cleanup=True)
    recovered=0
    for i in m['compressed'].values():
        encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];recovered+=len(raw)
    assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==r['source_sha256']
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=251,original_sms_preserved=True,observer_working_source_restored=True,recovered_bytes_verified=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/screen_spell_clock_recovery_v0251_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
