"""Freeze v0220 dialogue evidence before cleaning generated capture binaries."""
import gzip,io,json
from PIL import Image
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
from validate_dialogue_vblank import text_pixels

def main():
    digest='b49be582d3019f00e396840b1d0716b75f3ada775e298c75049c1e0216266202'
    for name in ['gaw-megadrive.bin','gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==digest
    reports=[ROOT/f'analysis/{n}_report.json' for n in ['dialogue_vblank_v0220','dialogue_opening_regression_v0220','house_dialogue_v0220','merchant_v0220']]
    for p in reports:assert json.loads(p.read_bytes())['md_sha256']==digest
    for p in reports[:2]:assert json.loads(p.read_bytes())['passed']
    baseline=ROOT/'analysis/dialogue_vblank_v0219_report.json';old=json.loads(baseline.read_bytes());assert [c['differing_frames'] for c in old['cases']]==[10,5]
    roots=[ROOT/f'validation/dialogue-vblank-v{v}' for v in ['0219','0220']]
    roots.extend(ROOT/f'validation/{tag}-house-dialogue-{n}' for tag in ['sms','md'] for n in ['0','1','2','3','4','5','walking'])
    roots.extend(ROOT/f'validation/{tag}-merchant-{n}' for tag in ['sms','md'] for n in ['key','feather','oil','poor','keys_full','feather_owned','oil_owned','natural'])
    roots.extend(ROOT/f'validation/dialogue-scroll-{region}-{tag}{suffix}' for tag in ['sms','md'] for region in ['auto','pal'] for suffix in ['','-v0219-reference'])
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    paths.update(reports);paths.add(baseline)
    paths.update(ROOT/n for n in ['README.md','analysis/world_next.md','analysis/dialogue_vblank_v0220.md','validation/dialogue-v0220-world-prefix.json','validation/v0219-symbols.txt','megadrive/src/main.c','megadrive/src/sound.inc','megadrive/out/release/symbol.txt','megadrive/out/release/rom.bin','gaw-megadrive.bin','gaw-title-megadrive.bin','tools/validate_dialogue_vblank.py','tools/validate_dialogue_scroll.py','tools/validate_house_dialogue.py','tools/validate_merchant.py','tools/archive_dialogue_vblank_release.py','versions/index.json','validation/dialogue_scroll_v0219_reference_baseline_report.json','validation/dialogue_scroll_baseline_report.json'])
    paths.update(ROOT.glob('validation/v0220-*.log'))
    paths.update((ROOT/'versions/v0220-b49be582').iterdir())
    prefix=json.loads((ROOT/'validation/dialogue-v0220-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==220
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    out=ROOT/'analysis/dialogue-vblank-v0220'
    manifest=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=220,full_game_validated=False,source_dialogue_cadence_exact=False),roots,cleanup=True)
    def recover(name):
        if name in manifest['files']:
            b=(out/name).read_bytes();assert sha(b)==manifest['files'][name];return b
        i=manifest['compressed'][name];encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==i['raw_sha256'] and len(b)==i['raw_bytes'];return b
    count=0
    for case in json.loads(reports[0].read_bytes())['cases']:
        base=f'validation/dialogue-vblank-v0220/{case["region"]}'
        for row in case['frames']:
            f=row['frame'];expected=text_pixels(recover(f'{base}/vram_{f:05d}.bin'),recover(f'{base}/cram_{f:05d}.bin'))
            actual=list(Image.open(io.BytesIO(recover(f'{base}/frame_{f:05d}.png'))).convert('RGB').crop((24,128,232,168)).getdata());assert actual==expected;count+=1
    assert count==302 and all(sha(p.read_bytes())==h for p,h in roms.items())
    assert sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in manifest['removed_verified_generated'])
    result=dict(md_sha256=digest,passed=True,frames_recovered=count,text_pixels_recovered=count*208*40,numbered_roms_preserved=len(roms),removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),original_sms_preserved=True)
    (ROOT/'analysis/dialogue_vblank_recovery_v0220_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
