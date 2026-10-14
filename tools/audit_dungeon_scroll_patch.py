"""Bind compiled dungeon scrolling and focused regression evidence to one ROM."""
import hashlib
import json
import re
from extract_world import ROOT, initial_room


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    data=(ROOT/'gaw-megadrive.bin').read_bytes()
    digest=sha(data)
    original=(ROOT/'input/original.sms').read_bytes()
    assert sha(original)=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    assert len(data)==524288
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
        assert (ROOT/name).read_bytes()==data
    assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535
    assert int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in
             (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    *_,arrays,_=initial_room(original)
    for name in ['world_room_index','world_room_streams','world_dungeon_palettes','world_dungeon_dark_rooms']:
        address=symbols[name]
        assert data[address:address+len(arrays[name])]==arrays[name],name
    evidence=[];timing=[]
    for suffix in ['', '-pal']:
        reports={}
        for stem in ['dungeon_scroll','dungeon_doors','scroll_objects','timing']:
            name=stem+suffix+'_report.json'
            raw=(ROOT/'validation'/name).read_bytes()
            report=json.loads(raw)
            assert report['md_sha256']==digest,name
            reports[stem]=report
            evidence.append(dict(file=name,sha256=sha(raw)))
        cases=reports['dungeon_scroll']['cases']
        assert len(cases)==8 and {c['direction'] for c in cases}=={'left','right','up','down'}
        assert sum(c['dark_destination'] for c in cases)==2
        for case in cases:
            assert case['destination_state_source_exact'] and case['old_objects_hidden']
            assert case['target']>=256 and case['fixed_palette_bytes_exact']==13
            assert case['map_bytes_exact']==1280 and case['persistence_bytes_exact']==256
            assert case['timing']['md']['nonhero_sprite_errors']==0
            timing.append(case['timing']['md']['resumed']-case['timing']['sms']['resumed'])
        assert len(reports['dungeon_doors']['cases'])==10
        assert all(c['settled_entry_exit_fields_source_exact'] for c in reports['dungeon_doors']['cases'])
        assert all(c['checks']['md']['nonhero_sprite_errors']==0 for c in reports['scroll_objects']['cases'])
        assert all(c['differing_state_frames']==0 for c in reports['timing']['natural_input_sequences'])
        assert reports['timing']['enemy']['differing_motion_counter_frames']==0
    report=dict(md_sha256=digest,md_size=len(data),rom_aliases_exact=True,additive_checksum_valid=True,
                controlled_dungeon_scroll_cases=16,dungeon_entry_exit_regressions=20,
                destination_maps_palettes_persistence_source_exact=True,old_objects_hidden=True,
                gameplay_resume_offset_frames_min=min(timing),gameplay_resume_offset_frames_max=max(timing),
                current_targeted_reports=evidence,
                source_files={name:sha((ROOT/name).read_bytes()) for name in
                              ['megadrive/src/main.c','tools/validate_dungeon_scroll.py','tools/audit_dungeon_scroll_patch.py']},
                full_game_ported=False,full_natural_dungeon_progression_verified=False,
                limits=['Controlled room/edge fixtures do not establish natural dungeon progression.',
                        'Some scroll setup/loading durations still differ from SMS; full transition pixels are not compared.',
                        'Conditional cells, room puzzles, keys, quests, remaining enemy behaviors, bosses and ending remain incomplete.',
                        'Lantern activation, tile animation and animated palette phase remain incomplete.'])
    (ROOT/'validation/dungeon_scroll_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Sixteen dungeon scrolls and eight current reports bound to cartridge.')


if __name__=='__main__':
    main()
