"""Preserve v0219 evidence, clean generated captures, recover the pixel checks."""
import gzip,io,json
from pathlib import Path
from PIL import Image
from archive_lossless_evidence import freeze,sha
from validate_playable_sprite_viewport import sprite_plane

ROOT=Path(__file__).resolve().parents[1]

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes())
    assert digest=='7518d3c174b117b299c1317b5921e351de7e96eee44fcd4a7d3d43566854cce7'
    reports=[ROOT/('analysis/'+name) for name in ['playable_sprite_viewport_v0219_report.json','world_frame_coherence_v0219_report.json','inventory_restore_v0219_report.json']]
    for p in reports:assert json.loads(p.read_bytes())['md_sha256']==digest
    assert all(json.loads(p.read_bytes())['passed'] for p in reports[:2])
    inventory=json.loads(reports[2].read_bytes());assert len(inventory['cases'])==6 and not inventory['diagnostic_only']
    for case in inventory['cases']:
        assert case['inventory_open_and_closed'] and not case['early_native_static_pattern_changes_from_before_menu']
        assert not any(case['static_background_pattern_difference_indices'].values())
    roots=[ROOT/'validation/playable-sprite-viewport-v0219',ROOT/'validation/world-frame-coherence-v0219']
    roots.extend(ROOT/f'validation/inventory-restore-{place}-{region}-{tag}' for place in ['exterior','first_house','second_house'] for region in ['auto','pal'] for tag in ['md','sms'])
    paths=set(p for folder in roots for p in folder.rglob('*') if p.is_file())
    paths.update(reports)
    paths.update(ROOT/name for name in ['README.md','analysis/world_next.md','analysis/playable_sprite_viewport_v0219.md','validation/sprite-viewport-v0219-world-prefix.json','megadrive/src/main.c','megadrive/src/sound.inc','megadrive/out/release/symbol.txt','megadrive/out/release/rom.bin','gaw-megadrive.bin','gaw-title-megadrive.bin','tools/archive_sprite_viewport_release.py','tools/validate_playable_sprite_viewport.py','tools/validate_world_frame_coherence.py','tools/validate_inventory_restore.py','validation/sms-vertical-check/vdp_regs_03120.bin','validation/sms-vertical-check/ram_03120.bin','versions/index.json'])
    paths.update(ROOT.glob('validation/v0219-*.log'))
    paths.update((ROOT/'versions/v0219-7518d3c1').iterdir())
    prefix=json.loads((ROOT/'validation/sprite-viewport-v0219-world-prefix.json').read_bytes())
    assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==219
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    out=ROOT/'analysis/sprite-viewport-v0219'
    manifest=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=219,full_game_validated=False),roots,cleanup=True)
    def recover(name):
        if name in manifest['files']:
            b=(out/name).read_bytes();assert sha(b)==manifest['files'][name];return b
        item=manifest['compressed'][name];encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        b=gzip.decompress(encoded);assert sha(b)==item['raw_sha256'] and len(b)==item['raw_bytes'];return b
    count=0
    for region in ['auto','pal']:
        for label in ['above_all','above_partial','top_partial','bottom_partial','below_all']:
            for frame in range(3131,3141):
                base=f'validation/playable-sprite-viewport-v0219/{region}-{label}'
                before=sprite_plane(recover(f'{base}-old/vram_{frame:05d}.bin'),8)
                after=sprite_plane(recover(f'{base}-new/vram_{frame:05d}.bin'),16)
                assert after==bytes(4096)+before[4096:256*208]+bytes(4096)
                image=Image.open(io.BytesIO(recover(f'{base}-new/frame_{frame:05d}.png'))).convert('RGB')
                assert all(image.getpixel((x,y))==(0,0,0) for y in list(range(16))+list(range(208,224)) for x in range(256))
                count+=1
    assert all(sha(p.read_bytes())==digest for p,digest in roms.items())
    assert sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in manifest['removed_verified_generated'])
    result=dict(md_sha256=manifest['playable_sha256'],passed=True,frames_recovered=count,numbered_roms_preserved=len(roms),removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),original_sms_preserved=True)
    (ROOT/'analysis/sprite_viewport_recovery_v0219_report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)

if __name__=='__main__':main()
