"""Freeze v0223 wait/control/save evidence and recover it after cleanup."""
import gzip,json,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
from validate_playable_sprite_limit import symbols

def main():
    digest='39e6995514a87d170d4d1fc713938a3645905842fe93a340415c80e996057a31'
    names=['dialogue_waits','service_wait_markers','dialogue_page_buttons','save','final_dialogue','dialogue_scroll','house_dialogue','merchant_magic_full']
    reports=[ROOT/f'analysis/{n}_v0223_report.json' for n in names]
    for p in reports:
        r=json.loads(p.read_bytes());assert r['md_sha256']==digest
        if 'passed' in r:assert r['passed'] and not r.get('diagnostic_only',False)
    save=json.loads(reports[3].read_bytes());assert len(save['cases'])==3 and all(c['payload_bytes_exact']==592 for c in save['cases'])
    roots=[ROOT/f'validation/{name}-v{version}' for name in ['dialogue-waits','service-waits','dialogue-page-buttons'] for version in ['0222','0223']]
    roots.extend(ROOT/f'validation/{tag}-save-{n}' for tag in ['sms','md'] for n in ['slot-0','slot-1','slot-2','reload-0','reload-1','reload-2','death-reload','no','cancel','overwrite','overwrite-occupied'])
    roots.extend(ROOT/f'validation/{tag}-continue-empty' for tag in ['sms','md'])
    roots.extend(ROOT/f'validation/{tag}-house-dialogue-{n}' for tag in ['sms','md'] for n in ['0','1','2','3','4','5','walking'])
    roots.extend(ROOT/f'validation/final-dialogue-{region}-{button}-{tag}' for region in ['auto','pal'] for button in [0,8,4,5,6,7] for tag in ['sms','md'])
    roots.extend(ROOT/f'validation/dialogue-scroll-{region}-{tag}' for region in ['auto','pal'] for tag in ['sms','md'])
    roots.extend(ROOT/f'validation/{tag}-all-merchants-magic-full' for tag in ['sms','md'])
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()};paths.update(reports)
    paths.update(ROOT.glob('validation/*save*.srm'));paths.update(ROOT.glob('validation/*all-merchants-fixture.srm'))
    for n in ['dialogue_waits','service_wait_markers','dialogue_page_buttons']:
        p=ROOT/f'analysis/{n}_v0222_report.json';r=json.loads(p.read_bytes());assert r['diagnostic_only'] and not r['passed'];paths.add(p)
    paths.update(ROOT/n for n in ['README.md','analysis/world_next.md','analysis/dialogue_waits_v0223.md','validation/dialogue-waits-v0223-world-prefix.json','megadrive/src/main.c','megadrive/src/save.inc','megadrive/src/healer.inc','megadrive/src/merchant.inc','megadrive/out/release/symbol.txt','megadrive/out/release/rom.bin','gaw-megadrive.bin','gaw-title-megadrive.bin','tools/archive_dialogue_waits_release.py','tools/archive_lossless_evidence.py','tools/validate_dialogue_waits.py','tools/validate_service_wait_markers.py','tools/validate_dialogue_page_buttons.py','tools/validate_save.py','tools/validate_all_merchants.py','tools/validate_final_dialogue.py','tools/validate_dialogue_scroll.py','tools/validate_house_dialogue.py','versions/index.json'])
    paths.update(ROOT.glob('validation/v0223-*.log'));paths.update((ROOT/'versions/v0223-39e69955').iterdir())
    prefix=json.loads((ROOT/'validation/dialogue-waits-v0223-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    for n in ['gaw-megadrive.bin','gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/n).read_bytes())==digest
    original=sha((ROOT/'input/original.sms').read_bytes());assert original=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==223
    out=ROOT/'analysis/dialogue-waits-v0223'
    if '--verify-only' in sys.argv:
        m=json.loads((out/'manifest.json').read_bytes());assert m['playable_sha256']==digest
    else:
        m=freeze(ROOT,out,paths,dict(playable_sha256=digest,numbered_roms_preserved=223,full_game_validated=False,global_source_clock_exact=False),roots,cleanup=True)
    def recover(name):
        if name in m['files']:
            b=(out/name).read_bytes();assert sha(b)==m['files'][name];return b
        i=m['compressed'][name];encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==i['raw_sha256'] and len(b)==i['raw_bytes'];return b
    for name in list(m['files'])+list(m['compressed']):recover(name)
    count=0
    for case in json.loads(recover('analysis/dialogue_waits_v0223_report.json'))['cases']:
        data={tag:json.loads(recover(e['path'])) for tag,e in case['evidence'].items()}
        for n in range(64):
            assert data['sms']['rows'][str(data['sms']['start']+n)]==data['md']['rows'][str(data['md']['start']+n)];count+=1
        for tag in ['sms','md']:
            assert data[tag]['rows']['2200']==dict(clock=255,marker=252) and data[tag]['rows']['2201']['clock']==0
    service_frames=0
    for case in json.loads(recover('analysis/service_wait_markers_v0223_report.json'))['cases']:
        data={tag:json.loads(recover(e['path'])) for tag,e in case['evidence'].items()}
        for f in range(3960,4080):assert data['sms'][str(f)]['marker']==data['md'][str(f)]['marker']==252;service_frames+=1
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');bitmaps=0
    for region in ['auto','pal']:
        for f in [1650,1750,1900]:
            a=recover(f'validation/dialogue-page-buttons-v0223/{region}-sms/ram_{f:05d}.bin')[0x1100:0x1510];r=recover(f'validation/dialogue-page-buttons-v0223/{region}-md/ram_{f:05d}.bin');b=bytes(r[(sy['scratch']+i)^1] for i in range(1040));assert a==b;bitmaps+=1
    for slot in range(3):
        # Match the regression frontend's SRAM import: odd-byte MD lane,
        # then erased FF for any tail omitted from the exported image.
        a=recover(f'validation/sms-save-slot-{slot}.srm').ljust(8192,b'\xff');b=recover(f'validation/md-save-slot-{slot}.srm')[1::2].ljust(8192,b'\xff');start=0x400+slot*0x400
        assert len(a[start:start+592])==len(b[start:start+592])==592
        assert a[start]!=255 and a[start:start+592]==b[start:start+592]
    assert count==128 and service_frames==480 and bitmaps==6 and all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(i['bytes'] for i in m['removed_verified_generated'])
    result=dict(md_sha256=digest,passed=True,page_clock_marker_frames_recovered=count,final_service_marker_frames_recovered=service_frames,button_fixture_bitmaps_recovered=bitmaps,save_payload_bytes_recovered=3*592,numbered_roms_preserved=len(roms),removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),original_sms_preserved=True)
    (ROOT/'analysis/dialogue_waits_recovery_v0223_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
