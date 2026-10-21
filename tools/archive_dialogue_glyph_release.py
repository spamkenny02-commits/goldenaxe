"""Freeze v0222 glyph/production evidence and recover it after cleanup."""
import gzip,io,json
from PIL import Image
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
from validate_dialogue_vblank import text_pixels

def main():
    digest='13edb546df3bb0f6a5466843170323fbaa9b258355e171672391fcbef61b7ce8'
    release=ROOT/'analysis/dialogue_glyph_v0222_report.json';r=json.loads(release.read_bytes());assert r['passed'] and r['md_sha256']==digest
    roots=[ROOT/'validation/dialogue-glyph-v0222',ROOT/'validation/dialogue-vblank-v0222']
    roots.extend(ROOT/f'validation/{tag}-house-dialogue-{n}' for tag in ['sms','md'] for n in ['0','1','2','3','4','5','walking'])
    roots.extend(ROOT/f'validation/dialogue-scroll-{region}-{tag}' for region in ['auto','pal'] for tag in ['sms','md'])
    roots.extend(ROOT/f'validation/dialogue-preparation-{tag}{suffix}' for tag in ['sms','md'] for suffix in ['', '-pal'])
    fixtures=['plain','toggle','toggle_inside_word','double_toggle','toggle_wrap','overwide_word','forced_name','number_zero','number_65','number_12345','pause','pause_toggle','newline_toggle']
    roots.extend(ROOT/f'validation/dialogue-controls-{region}-{name}' for region in ['auto','pal'] for name in fixtures)
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()};paths.add(release)
    for name,h in r['evidence'].items():
        p=ROOT/name;assert sha(p.read_bytes())==h;paths.add(p)
    paths.update(ROOT/n for n in ['README.md','analysis/world_next.md','analysis/dialogue_glyph_v0222.md','validation/dialogue-glyph-v0222-world-prefix.json','megadrive/src/main.c','megadrive/src/sound.inc','megadrive/out/release/symbol.txt','megadrive/out/release/rom.bin','gaw-megadrive.bin','gaw-title-megadrive.bin','tools/archive_dialogue_glyph_release.py','tools/archive_lossless_evidence.py','tools/validate_dialogue_glyph_bytes.py','tools/summarize_dialogue_glyph_release.py','tools/validate_dialogue_vblank.py','tools/profile_dialogue_preparation.py','tools/validate_dialogue_controls.py','tools/validate_house_dialogue.py','tools/validate_dialogue_scroll.py','versions/index.json'])
    paths.update(ROOT.glob('analysis/*_v0222_report.json'));paths.update(ROOT.glob('validation/v0222-*.log'));paths.update((ROOT/'versions/v0222-13edb546').iterdir())
    prefix=json.loads((ROOT/'validation/dialogue-glyph-v0222-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for name in ['gaw-megadrive.bin','gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==digest
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==222
    out=ROOT/'analysis/dialogue-glyph-v0222'
    m=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=222,complete_dialogue_timing_exact=False,full_game_validated=False),roots,cleanup=True)
    def recover(name):
        if name in m['files']:
            b=(out/name).read_bytes();assert sha(b)==m['files'][name];return b
        i=m['compressed'][name];encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==i['raw_sha256'] and len(b)==i['raw_bytes'];return b
    for suffix in ['', '-pal']:
        p=json.loads(recover(f'analysis/dialogue_preparation_v0222{suffix}_profile.json'));a=p['results']['sms'];b=p['results']['md'];end=next(e['frame'] for e in a['events'] if e['pc']==0x7f4);previous=0;shapes=set()
        events=[e for e in a['events'] if e['pc']==0x7b3 and e['frame']<=end]
        for e in events:
            h=a['hardware_bitmap_sha256'][str(e['frame'])];shapes.add(h);matches=[int(f) for f,v in b['hardware_bitmap_sha256'].items() if v==h and b['hardware_bitmap_colors_valid'][f] and int(f)>=previous];assert matches;previous=min(matches)
        assert len(events)==37 and len(shapes)==29
    count=0
    for case in json.loads(recover('analysis/dialogue_vblank_v0222_report.json'))['cases']:
        base=f'validation/dialogue-vblank-v0222/{case["region"]}'
        for row in case['frames']:
            f=row['frame'];expected=text_pixels(recover(f'{base}/vram_{f:05d}.bin'),recover(f'{base}/cram_{f:05d}.bin'))
            actual=list(Image.open(io.BytesIO(recover(f'{base}/frame_{f:05d}.png'))).convert('RGB').crop((24,128,232,168)).getdata());assert actual==expected;count+=1
    assert count==302 and all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in m['removed_verified_generated'])
    result=dict(md_sha256=digest,passed=True,text_frames_recovered=count,ordered_source_distinct_bitmap_hashes_recovered=58,numbered_roms_preserved=len(roms),removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),original_sms_preserved=True)
    (ROOT/'analysis/dialogue_glyph_recovery_v0222_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
