"""Freeze and recover v0221 scroll and dialogue evidence before cleanup."""
import gzip,io,json
from PIL import Image
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
from validate_dialogue_vblank import text_pixels
from validate_dialogue_scroll import shifted

def main():
    digest='0cc51636efdff6e1bed7c0e74808d0ce5589f9333718abdccb392cef7daa1013'
    reports=[ROOT/f'analysis/{n}_v0221_report.json' for n in ['dialogue_scroll','house_dialogue','final_dialogue','dialogue_vblank']]
    for p in reports:assert json.loads(p.read_bytes())['md_sha256']==digest
    scroll=json.loads(reports[0].read_bytes());assert scroll['passed'] and not scroll['diagnostic_only']
    assert json.loads(reports[3].read_bytes())['passed']
    assert len(json.loads(reports[1].read_bytes())['cases'])==6 and len(json.loads(reports[2].read_bytes())['cases'])==12
    roots=[ROOT/'validation/dialogue-vblank-v0221']
    roots.extend(ROOT/f'validation/dialogue-scroll-{region}-{tag}' for region in ['auto','pal'] for tag in ['sms','md'])
    roots.extend(ROOT/f'validation/{tag}-house-dialogue-{n}' for tag in ['sms','md'] for n in ['0','1','2','3','4','5','walking'])
    roots.extend(ROOT/f'validation/final-dialogue-{region}-{button}-{tag}' for region in ['auto','pal'] for button in [0,8,4,5,6,7] for tag in ['sms','md'])
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()};paths.update(reports)
    paths.update(ROOT/n for n in ['README.md','analysis/world_next.md','analysis/dialogue_scroll_v0221.md','validation/dialogue-scroll-v0221-world-prefix.json','megadrive/src/main.c','megadrive/src/sound.inc','megadrive/out/release/symbol.txt','megadrive/out/release/rom.bin','gaw-megadrive.bin','gaw-title-megadrive.bin','tools/archive_dialogue_scroll_release.py','tools/archive_lossless_evidence.py','tools/validate_dialogue_vblank.py','tools/validate_dialogue_scroll.py','tools/validate_house_dialogue.py','tools/validate_final_dialogue.py','versions/index.json'])
    paths.update(ROOT.glob('validation/v0221-*.log'));paths.update((ROOT/'versions/v0221-0cc51636').iterdir())
    prefix=json.loads((ROOT/'validation/dialogue-scroll-v0221-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for name in ['gaw-megadrive.bin','gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==digest
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==221
    out=ROOT/'analysis/dialogue-scroll-v0221'
    manifest=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=221,full_game_validated=False,complete_dialogue_cadence_exact=False),roots,cleanup=True)
    def recover(name):
        if name in manifest['files']:
            b=(out/name).read_bytes();assert sha(b)==manifest['files'][name];return b
        item=manifest['compressed'][name];encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==item['raw_sha256'] and len(b)==item['raw_bytes'];return b
    pose_count=0
    for case in scroll['cases']:
        region=case['region'];records={}
        for tag in ['sms','md']:
            raw=recover(f'validation/dialogue-scroll-{region}-{tag}/bitmap-records.bin');assert len(raw)==52*2080
            records[tag]={f:(raw[(f-2199)*2080:(f-2199)*2080+1040],raw[(f-2199)*2080+1040:(f-2198)*2080]) for f in range(2199,2251)}
        base=records['sms'][2199][0];assert base==records['md'][2199][0]
        for pose in case['poses']:
            expected=shifted(base,pose['cumulative_shift']);assert sha(expected)==pose['bitmap_sha256']
            lists={tag:[f for f,r in frames.items() if r[1]==expected] for tag,frames in records.items()}
            assert lists['sms']==lists['md']==pose['matching_frames']['sms']['patterns'];pose_count+=1
        following=case['following_complete_bitmap_frames']
        assert following['sms'][0]==following['md'][0]
        for tag in ['sms','md']:
            assert [f for f,r in records[tag].items() if sha(r[1])==case['first_following_complete_bitmap_sha256']]==following[tag]
    count=0
    for case in json.loads(reports[3].read_bytes())['cases']:
        base=f'validation/dialogue-vblank-v0221/{case["region"]}'
        for row in case['frames']:
            f=row['frame'];expected=text_pixels(recover(f'{base}/vram_{f:05d}.bin'),recover(f'{base}/cram_{f:05d}.bin'))
            actual=list(Image.open(io.BytesIO(recover(f'{base}/frame_{f:05d}.png'))).convert('RGB').crop((24,128,232,168)).getdata());assert actual==expected;count+=1
    assert pose_count==8 and count==302 and all(sha(p.read_bytes())==h for p,h in roms.items())
    assert sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in manifest['removed_verified_generated'])
    result=dict(md_sha256=digest,passed=True,complete_scroll_pose_lists_recovered=pose_count,text_frames_recovered=count,numbered_roms_preserved=len(roms),removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),original_sms_preserved=True)
    (ROOT/'analysis/dialogue_scroll_recovery_v0221_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
