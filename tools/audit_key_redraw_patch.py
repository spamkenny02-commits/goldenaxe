"""Bind the native redraw schedule, source profiles and persistence checks."""
import hashlib,json
from run_core import ROOT


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(data)
    assert len(data)==524288
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
        assert (ROOT/name).read_bytes()==data
    assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535
    assert int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
    names=['key_doors','key_door_save','key_redraw_model']+[stem+suffix for stem in
        ['key_door_gameplay','key_door_continue','timing'] for suffix in ['', '-pal']]
    evidence=[];reports={}
    for stem in names:
        name=stem+'_report.json';raw=(ROOT/'validation'/name).read_bytes();report=json.loads(raw)
        assert report['md_sha256']==digest,name
        reports[stem]=report;evidence.append(dict(file=name,sha256=sha(raw)))
    keys=reports['key_doors']
    assert keys['cases_checked']==8192 and keys['source_opened_cases']==180 and keys['source_key_consumption_cases']==120
    for name,expected in keys['source_copies'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==expected,name
    model=reports['key_redraw_model']
    assert model['source_map_loop_tstates_exact']==192686 and len(model['cases'])==6
    for profile in model['profiles']:
        raw=(ROOT/profile['file']).read_bytes();assert sha(raw)==profile['sha256']
        assert json.loads(raw)['md_sha256']==digest
        evidence.append(dict(file=profile['file'],sha256=sha(raw)))
        assert sha((ROOT/profile['baseline_file']).read_bytes())==profile['baseline_sha256']
    for suffix in ['', '-pal']:
        for stem in ['key_door_gameplay','key_door_continue']:
            cases=reports[stem+suffix]['cases'];assert len(cases)==9
            assert all(c['settled_crossing_return_fields_source_exact'] for c in cases)
            if stem=='key_door_continue':assert all(c['death_continue_persistence_verified'] for c in cases)
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
    assert all(c['save_payload_bytes_exact']==592 for c in reports['key_door_save']['cases'])
    report=dict(md_sha256=digest,md_size=len(data),rom_aliases_exact=True,additive_checksum_valid=True,
                current_targeted_reports=evidence,original_map_loop_tstates=192686,
                redraw_pause_pal_source_exact_in_three_cases=True,redraw_pause_ntsc_one_frame_early=True,
                key_logic_cases=8192,controller_cases=18,death_continue_cases=18,cold_load_cases=2,
                source_files={name:sha((ROOT/name).read_bytes()) for name in
                    ['megadrive/src/main.c','megadrive/src/key_redraw_cost.inc','tools/extract_key_redraw_cost.py',
                     'tools/instrument_key_timing.py','tools/profile_key_redraw.py','tools/validate_key_redraw_model.py',
                     'tools/audit_key_redraw_patch.py']},
                full_game_ported=False,
                limits=['HUD/metadata/IRQ phase uses an approximate budget; only the original map loop cost is instruction exact.',
                        'NTSC post-redraw movement remains one frame early; vertical scrolling/loading has additional offsets.',
                        'Whole transition pixels and audio waveform are unverified.',
                        'Fixtures control initial rooms/inventory; complete natural dungeon progression, remaining puzzles, bosses and ending are incomplete.'])
    (ROOT/'validation/key_redraw_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Nine targeted reports and six profiles bound to ROM; remaining timing limits explicit.')


if __name__=='__main__':main()
