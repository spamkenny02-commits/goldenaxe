"""Bind source load trace and runtime checks; preserve remaining timing offsets."""
import hashlib,json
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
    assert len(rom)==524288
    assert int.from_bytes(rom[0x18e:0x190],'big')==sum(int.from_bytes(rom[i:i+2],'big') for i in range(0x200,len(rom),2))&65535
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
    baseline=ROOT/'versions/v0045-e45374ab';old_audit=json.loads((baseline/'room_clear_patch_audit.json').read_bytes())
    old=(ROOT/'analysis/baseline-v0045-main.c').read_bytes()
    assert sha(old)==old_audit['source_files']['megadrive/src/main.c']
    expected=old.decode().replace('\r\n','\n').replace('        if(world_actor_load_tstates)\n','        if(world_actor_load_tstates || world_graphics_class==2)\n').replace('            /* 1780/032A/1D0D: preserve','            /* Even a cleared dungeon executes 24C5/1780/2C63/5B20/1CAF:\n             * empty graphics do not mean zero foreground work.\n             * 1780/032A/1D0D: preserve')
    current=(ROOT/'megadrive/src/main.c').read_text();assert current==expected
    old_unit=json.loads((baseline/'key_doors_report.json').read_bytes())
    for file,expected_sha in old_unit['source_copies'].items():
        if file!='main.c':assert sha((ROOT/'megadrive/src'/file).read_bytes())==expected_sha,file
    evidence=[];reports={};offsets=[];cross_deltas=[];profile_summary=[]
    names=[name+suffix for name in ['dungeon_scroll','room_clear_gameplay','room_clear_cross','key_door_gameplay','timing'] for suffix in ['', '-pal']]
    for stem in names:
        path=ROOT/'validation'/f'{stem}_report.json';raw=path.read_bytes();r=json.loads(raw);assert r['md_sha256']==digest,stem
        reports[stem]=r;evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
    for suffix in ['', '-pal']:
        assert len(reports['dungeon_scroll'+suffix]['cases'])==8
        for case in reports['dungeon_scroll'+suffix]['cases']:
            assert case['destination_state_source_exact'] and case['old_objects_hidden']
            offsets.append(dict(region=suffix or 'ntsc',origin=case['origin'],direction=case['direction'],offset=case['timing']['md']['resumed']-case['timing']['sms']['resumed']))
        cases=reports['room_clear_gameplay'+suffix]['cases'];assert len(cases)==6
        assert all(c['settled_cells_exact'] and c['settled_map_exact'] and c['settled_flags_count_keys_exact'] for c in cases)
        cases=reports['room_clear_cross'+suffix]['cases'];assert len(cases)==3
        assert all(c['cross_and_return_verified'] and c['settled_flags_count_keys_exact'] and c['settled_cells_exact'] and c['settled_map_exact'] for c in cases)
        previous=json.loads((baseline/f'room_clear_cross{suffix}_report.json').read_bytes())
        for old_case,case in zip(previous['cases'],cases):
            assert old_case['room']==case['room']
            delta=lambda c:c['timing']['md']['returned']-c['timing']['sms']['returned']
            cross_deltas.append(dict(region=suffix or 'ntsc',room=case['room'],before=delta(old_case),after=delta(case)))
        assert len(reports['key_door_gameplay'+suffix]['cases'])==9
        assert all(c['settled_crossing_return_fields_source_exact'] for c in reports['key_door_gameplay'+suffix]['cases'])
        assert all(c['differing_state_frames']==0 for c in reports['timing'+suffix]['natural_input_sequences'])
        assert reports['timing'+suffix]['enemy']['differing_motion_counter_frames']==0
        path=ROOT/f'analysis/room17d_long_profile{suffix}.json';raw=path.read_bytes();p=json.loads(raw);assert p['md_sha256']==digest and p['scenario_assertion'] is None
        evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
        rows={tag:{r['frame']:r for r in trace} for tag,trace in p['traces'].items()}
        for frame in range(3611,3701):
            for field in ['room','game','x','y','counter','dx','dy']:assert rows['sms'][frame][field]==rows['md'][frame][field],(suffix,frame,field)
        assert rows['sms'][3750]['room']==rows['md'][3750]['room']==0x17d
        assert rows['sms'][3750]['cells']==rows['md'][3750]['cells']
        es=p['source_timing_events'];start=next(e for e in es if e[0]==0x24c5 and e[3]==0x17d);end=next(e for e in es if e[0]==0x24f2 and e[3]==0x17d)
        foreground=(end[1]-start[1]-end[2]+start[2])//15;assert foreground==52075
        profile_summary.append(dict(region=suffix or 'ntsc',source_empty_room_load_tstates=foreground,source_irq_tstates=(end[2]-start[2])//15,movement_frames_same_frame_exact=90,long_hold_no_extra_scroll=True,final_floor_cells_exact=True))
    assert sum(abs(c['after']) for c in cross_deltas)<sum(abs(c['before']) for c in cross_deltas)
    report=dict(md_sha256=digest,rom_size=len(rom),checksum_and_aliases_verified=True,production_change='Include cleared dungeons in the existing foreground initialization delay.',unchanged_routines_validation=dict(archived_rom_sha256=old_audit['md_sha256'],archived_audit_sha256=sha((baseline/'room_clear_patch_audit.json').read_bytes()),isolated_cases_previously_executed=24576,production_source_change_exactly_checked=True,isolated_cases_rerun_for_this_rom=False),current_evidence=evidence,source_profiles=profile_summary,cross_return_offsets=cross_deltas,dungeon_scroll_offsets=offsets,source_files={name:sha((ROOT/name).read_bytes()) for name in ['megadrive/src/main.c','tools/profile_room17d_path.py','tools/audit_empty_dungeon_loading.py','tools/validate_room_clear_gameplay.py']},full_game_ported=False,limits=['The generic 20000-T overhead remains approximate; the 52075-T source trace is evidence, not a per-room delay constant.','Some horizontal loads now resume one frame late; upward loading can still resume up to five frames early in the controlled routes.','PAL room 151 return is one frame late instead of previously exact; this remains a timing-model limitation.','Controlled fixtures, not full natural dungeon progression. Sprite pixels, audio waveform, remaining puzzles, bosses and ending are unverified or incomplete.'])
    (ROOT/'validation/empty_dungeon_loading_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('10 runtime reports + 2 source profiles bound. 17D motion: 180 exact frames; source empty load: 52075 T. Remaining offsets recorded.')
if __name__=='__main__':main()
