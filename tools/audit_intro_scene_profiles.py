"""Bind three-scene checks and unresolved hardware SAT diagnostics to v0030."""
import hashlib
import json
from actor_reference import ROOT
from finalize_md_rom import md_checksum


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes()
    digest=sha(rom)
    assert digest == 'c325609b47f43b324624a254be204fd89f59856ace4b2460f4e588f06f05cea1'
    assert int.from_bytes(rom[0x18e:0x190],'big') == md_checksum(rom)
    assert (ROOT/'versions/v0030-c325609b/gaw-megadrive-v0030.bin').read_bytes() == rom
    evidence=[]
    for name in ['intro_scenes_profile','intro_actors_profile']:
        path=ROOT/f'analysis/{name}.json'
        raw=path.read_bytes();r=json.loads(raw)
        assert r['md_sha256'] == digest
        assert r['source_sha256'] == sha((ROOT/'input/original.sms').read_bytes())
        assert r['no_ram_mutations']
        if name == 'intro_scenes_profile':
            for region, systems in r['regions'].items():
                for tag in ['sms','md']:
                    assert len(systems[tag]['passes']) == 24
                    assert systems['comparison']['per_scene_start_intervals'][tag] == [[5]*7]*3
                assert [p['planar_sha256'] for p in systems['sms']['passes']] == [p['planar_sha256'] for p in systems['md']['passes']]
        else:
            assert r['vtimer_width_bytes'] == 4
            assert [r['regions'][k]['matching_samples'] for k in ['ntsc','pal']] == [3744,3772]
            assert [r['regions'][k]['sprite_difference_count'] for k in ['ntsc','pal']] == [118,111]
            assert all(not d['difference_count'] and not d['missing_count'] for d in r['regions'].values())
        evidence.append(dict(file=path.name,sha256=sha(raw)))
    audit=dict(md_sha256=digest,evidence=evidence,three_scene_completed_patterns_and_cadence_verified=True,
               logical_actor_states_consistent_at_matching_phases=True,
               hardware_sat_equivalence_verified=False,hardware_sat_differences_reproduced=True,
               absolute_intro_timing_exact=False,rom_changed=False,full_game_ported=False,
               source_files={name:sha((ROOT/name).read_bytes()) for name in
                   ['tools/profile_intro_scenes.py','tools/profile_intro_actors.py']})
    (ROOT/'validation/intro_scene_profiles_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('Three scene profiles verified; 229 hardware SAT differences remain recorded')


if __name__=='__main__': main()
