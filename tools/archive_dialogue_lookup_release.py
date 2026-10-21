"""Freeze v0224 evidence and recover every checked indoor text frame."""
import gzip, io, json
from PIL import Image
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
from validate_dialogue_vblank import text_pixels

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes())
    report=json.loads((ROOT/'analysis/dialogue_lookup_v0224_report.json').read_bytes());assert report['passed'] and report['md_sha256']==digest
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==224
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roots=[ROOT/'validation/dialogue-lookup-v0224',ROOT/'validation/dialogue-vblank-v0224',ROOT/'validation/dialogue-page-buttons-v0224',ROOT/'validation/natural-dungeon-combat']
    for pattern in ['dialogue-controls-*','dialogue-scroll-*','dialogue-preparation-*']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths=set()
    for folder in roots:paths.update(p for p in folder.rglob('*') if p.is_file())
    for name in ['README.md','build.ps1','megadrive/src/main.c','megadrive/src/dialogue_glyph_lookup.inc','megadrive/src/menu_data.c','megadrive/out/release/symbol.txt','analysis/dialogue_lookup_v0224.md','analysis/dialogue_lookup_v0224_report.json','analysis/dialogue_vblank_v0224_report.json','analysis/dialogue_page_buttons_v0224_report.json','validation/dialogue_controls_report.json','validation/dialogue_scroll_report.json','tools/generate_dialogue_glyph_lookup.py','tools/validate_dialogue_lookup_release.py','tools/natural_dungeon_combat.py','analysis/world_next.md']:
        paths.add(ROOT/name)
    paths.update(ROOT.glob('analysis/dialogue_preparation_v022[34]*_profile.json'))
    paths.update(ROOT.glob('validation/v0224-*.log'));paths.add(ROOT/'validation/build-v0224.log')
    paths.update((ROOT/'versions/v0224-6be955fd').iterdir())
    out=ROOT/'analysis/dialogue-lookup-v0224'
    m=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=224,full_game_validated=False),roots,cleanup=True)
    def read(name):
        if name in m['files']:
            raw=(out/name).read_bytes();assert sha(raw)==m['files'][name];return raw
        i=m['compressed'][name];encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];return raw
    count=0
    for case in json.loads(read('analysis/dialogue_vblank_v0224_report.json'))['cases']:
        base=f'validation/dialogue-vblank-v0224/{case["region"]}'
        for row in case['frames']:
            f=row['frame'];expected=text_pixels(read(f'{base}/vram_{f:05d}.bin'),read(f'{base}/cram_{f:05d}.bin'))
            actual=list(Image.open(io.BytesIO(read(f'{base}/frame_{f:05d}.png'))).convert('RGB').crop((24,128,232,168)).getdata())
            assert actual==expected;count+=1
    assert count==302
    assert all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in m['removed_verified_generated'])
    result=dict(md_sha256=digest,passed=True,indoor_text_frames_recovered=count,numbered_roms_preserved=len(roms),original_sms_preserved=True,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/dialogue_lookup_recovery_v0224_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
