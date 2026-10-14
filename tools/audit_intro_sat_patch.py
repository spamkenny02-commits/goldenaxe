"""Bind the source-derived intro SAT upload change and its remaining differences."""
import hashlib
import json
from actor_reference import ROOT
from finalize_md_rom import md_checksum


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    assert len(rom)==524288
    assert int.from_bytes(rom[0x18e:0x190],'big')==md_checksum(rom)
    for alias in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
        assert (ROOT/alias).read_bytes()==rom
    baseline=ROOT/'versions/v0030-c325609b/intro_actors_profile.json'
    before=json.loads(baseline.read_bytes())
    assert before['md_sha256']=='c325609b47f43b324624a254be204fd89f59856ace4b2460f4e588f06f05cea1'
    paths=['analysis/intro_actors_profile.json','analysis/intro_scenes_profile.json']
    paths += [f'validation/{name}_report.json' for name in
              ['intro','intro-pal','title_cadence','title_cadence-pal',
               'title_cadence-natural','title_cadence-pal-natural',
               'scroll_objects','scroll_objects-pal','timing','timing-pal']]
    evidence=[]
    for name in paths:
        raw=(ROOT/name).read_bytes();r=json.loads(raw)
        assert r['md_sha256']==digest,name
        if name.endswith('intro_actors_profile.json'):
            assert [r['regions'][k]['sprite_difference_count'] for k in ['ntsc','pal']]==[15,16]
            assert [before['regions'][k]['sprite_difference_count'] for k in ['ntsc','pal']]==[118,111]
            for region,d in r['regions'].items():
                assert not d['difference_count'] and not d['missing_count']
                assert d['matching_samples']==before['regions'][region]['matching_samples']
        if name.endswith('intro_scenes_profile.json'):
            for systems in r['regions'].values():
                assert systems['comparison']['completed_pass_patterns_exact']
                for tag in ['sms','md']:
                    assert len(systems[tag]['passes'])==24
                    assert systems['comparison']['per_scene_start_intervals'][tag]==[[5]*7]*3
        if name in ['validation/intro_report.json','validation/intro-pal_report.json']:
            assert len(r['story_lines'])==65 and r['title_returns_after_intro']
        if 'scroll_objects' in name:
            assert len(r['cases'])==4 and all(c['checks']['md']['nonhero_sprite_errors']==0 for c in r['cases'])
        evidence.append(dict(file=name,sha256=sha(raw)))
    audit=dict(md_sha256=digest,baseline_sha256=before['md_sha256'],
               baseline_profile_sha256=sha(baseline.read_bytes()),evidence=evidence,
               additive_checksum_valid=True,aliases_equal=True,
               sat_mismatch_count_before=229,sat_mismatch_count_after=31,
               logical_actor_state_comparisons=7516,
               hardware_sat_equivalence_verified=False,absolute_intro_timing_exact=False,
               intro_palette_pipeline_verified=False,full_game_ported=False,
               source_files={name:sha((ROOT/name).read_bytes()) for name in
                    ['megadrive/src/intro.inc','tools/profile_intro_actors.py']})
    (ROOT/'validation/intro_sat_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(f'{len(evidence)} current reports; SAT differences reduced 229 -> 31: {digest}')


if __name__=='__main__':main()
