"""Bind SMS overflow status modeling and projectile allocation evidence."""
import hashlib,json
from actor_reference import ROOT
from finalize_md_rom import md_checksum


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    assert len(rom)==524288
    assert int.from_bytes(rom[0x18e:0x190],'big')==md_checksum(rom)
    for alias in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
        assert (ROOT/alias).read_bytes()==rom
    source=(ROOT/'input/original.sms').read_bytes()
    assert sha(source)=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    for pc in [0x85c1,0x8872,0x903f,0x9078,0x90b2,0x949b,0x96b9]:
        assert source[pc:pc+3]==bytes.fromhex('cd5e49')
    names=['sprite_overflow','overflow_allocation','overflow_allocation-pal',
           'walker40','walker40-pal','pursuit_shooters','pursuit_shooters-pal','burst_walkers',
           'scroll_objects','scroll_objects-pal','timing','timing-pal',
           'title_cadence','title_cadence-pal','intro','intro-pal']
    evidence=[]
    for name in names:
        path=ROOT/f'validation/{name}_report.json';raw=path.read_bytes();r=json.loads(raw)
        assert r['md_sha256']==digest,name
        if name=='sprite_overflow':
            assert not r['status_or_vram_mutations'] and len(r['fixtures'])==11
            assert all(d['comparison_frames']==129 and not d['differences'] for d in r['regions'].values())
        if name.startswith('overflow_allocation'):
            assert len(r['cases'])==10 and r['record_comparisons']==160
            assert r['guarded_and_direct_paths_verified'] and not r['explicit_test_status_ram_writes']
        if name.startswith('scroll_objects'):
            assert all(c['checks']['md']['nonhero_sprite_errors']==0 for c in r['cases'])
        if name in ['intro','intro-pal']:
            assert len(r['story_lines'])==65 and r['title_returns_after_intro']
        evidence.append(dict(file=path.name,sha256=sha(raw)))
    audit=dict(md_sha256=digest,source_sha256=sha(source),evidence=evidence,
               additive_checksum_valid=True,aliases_equal=True,
               modeled_sms_status_frame_comparisons=258,allocation_record_comparisons=320,
               sms_eight_by_eight_sprite_mode=True,md_hardware_overflow_used=False,
               source_fixture_status_mutations=False,source_fixture_vram_mutations=False,
               all_sprite_layouts_verified=False,sms_flicker_or_priority_emulated=False,
               full_game_ported=False,
               source_files={name:sha((ROOT/name).read_bytes()) for name in
                   ['megadrive/src/actors.c','megadrive/src/actors.h','megadrive/src/main.c',
                    'megadrive/src/sound.inc','tools/validate_sprite_overflow.py',
                    'tools/validate_overflow_allocation.py']})
    (ROOT/'validation/sprite_overflow_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(f'{len(evidence)} reports bound to {digest}')


if __name__=='__main__':main()
