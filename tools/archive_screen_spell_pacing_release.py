"""Archive all pacing prototypes and current evidence before capture cleanup."""
import gzip,json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
def main():
    release=ROOT/'analysis/screen_spell_pacing_release_v0264_report.json';before=release.read_bytes();r=json.loads(before);assert r['passed']
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest==r['md_sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==264
    roots=[]
    for pattern in ['screen-spell-v025[23456789]*','screen-spell-v026*','screen-spell-cost-host']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    for pattern in ['analysis/screen_spell*.json','analysis/screen_spell_pacing_v0264.md','validation/screen-spell*.log','validation/spell-v02*-disassembly.txt','validation/spell-profile-v0255.json','validation/build-v025[23456789]*.log','validation/build-v026*.log']:
        paths.update(ROOT.glob(pattern))
    entries=json.loads((ROOT/'versions/index.json').read_bytes())
    for entry in entries:
        if 252<=entry['version']<=264:paths.update((ROOT/'versions'/entry['rom']).parent.iterdir())
    for name in ['README.md','build.ps1','megadrive/src/main.c','megadrive/src/sound.inc','megadrive/src/screen_spell.inc','megadrive/src/screen_spell_pacing.inc','megadrive/src/screen_spell_assets.inc','megadrive/src/source_sprite_scene_cost.c','megadrive/src/source_sprite_scene_cost.h','megadrive/src/source_sprite_scene_tstates.c','megadrive/src/source_sprite_scene_timed.c','megadrive/out/release/symbol.txt','tools/generate_screen_spell.py','tools/screen_spell_cost.py','tools/validate_screen_spell_cost.py','tools/validate_screen_spell.py','tools/summarize_screen_spell_pacing_release.py','tools/archive_screen_spell_pacing_release.py','analysis/world_next.md','validation/v0264-world-prefix.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/v0264-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/screen-spell-pacing-v0264';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=264,full_game_verified=False),roots,cleanup=True)
    recovered=0
    for i in m['compressed'].values():
        encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];recovered+=len(raw)
    subprocess.run([sys.executable,'tools/summarize_screen_spell_pacing_release.py'],cwd=ROOT,check=True);assert release.read_bytes()==before
    assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==r['source_sha256']
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=264,original_sms_preserved=True,release_identical_after_recovery=True,recovered_bytes_verified=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/screen_spell_pacing_recovery_v0264_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
