"""Bind stationary puzzle source evidence, compiled fixtures and live checks."""
import hashlib,json
from extract_room_puzzles import ROOT,records

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    rom=(ROOT/'input/original.sms').read_bytes();md=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(md)
    assert len(md)==524288
    assert md==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    assert int.from_bytes(md[0x18e:0x190],'big')==sum(int.from_bytes(md[n:n+2],'big') for n in range(0x200,len(md),2))&65535
    old=json.loads((ROOT/'versions/v0054-1dbffe65/portals_patch_audit.json').read_bytes())
    baseline=ROOT/'analysis/baseline-v0054-main.c'
    assert sha(baseline.read_bytes())==old['source_files']['megadrive/src/main.c']
    s=(ROOT/'megadrive/src/main.c').read_text().replace('#include "room_puzzles.inc"\n','')
    a=s.index('/* Stationary UP scripts:');b=s.index('/* 6AA5..6AEA:',a);s=s[:a]+s[b:]
    s=s.replace('check_dungeon_key_door();check_room_puzzle(script_flags,0);','check_dungeon_key_door();').replace('check_dungeon_room_clear();check_room_puzzle(script_flags,1);','check_dungeon_room_clear();')
    assert s==baseline.read_text(),'Unrelated main changes'
    previous=json.loads((ROOT/'versions/v0051-3161f829/contacts_report.json').read_bytes())['source_copies']
    for name,h in previous.items():
        if name=='main.c':continue
        assert sha((ROOT/'megadrive/src'/name).read_bytes())==h,name
    assert sha((ROOT/'megadrive/src/room_portals.inc').read_bytes())==old['source_files']['megadrive/src/room_portals.inc']
    puzzles=records(rom)
    # 5E45 calls 1976 without a full redraw when all passages are open.
    # Its fourteen original rooms all have operation 9 (single marker cell).
    metadata={};p=0xbd1f
    while rom[p]:metadata[rom[p]]=list(rom[p+1:p+4]);p+=4
    assert all(metadata[x['room']&255][2]==9 for x in puzzles if x['native_kind']==5)
    source=json.loads((ROOT/'analysis/room_puzzles_reference.json').read_bytes())
    assert source['source_sha256']==sha(rom) and source['records']==puzzles
    generated=['/* Original stationary room transforms: room/kind/coordinate/argument/stage. */','static const u16 world_room_puzzles[31][5] = {']
    for x in puzzles:generated.append('    {'+','.join(str(v) for v in [x['room'],x['native_kind'],x['coordinate'],x['explicit_registers'].get('e',0),x['stage']])+'},')
    generated.append('};');assert (ROOT/'megadrive/src/room_puzzles.inc').read_text()=='\n'.join(generated)+'\n'
    names=['puzzles_report.json','puzzles_gameplay_report.json','puzzles_gameplay-pal_report.json','timing_report.json','timing-pal_report.json']
    names += [f'portals_gameplay-{room}{suffix}_report.json' for room in ['14b','16c'] for suffix in ['', '-pal']]
    evidence=[]
    for name in names:
        path=ROOT/'validation'/name;raw=path.read_bytes();report=json.loads(raw);assert report['md_sha256']==digest,name
        if name=='puzzles_report.json':assert report['cases_checked']==8192 and report['source_cells_maps_all_room_flags_and_key_count_exact']
        elif name.startswith('puzzles_gameplay'):assert len(report['cases'])==62 and all(x['trigger_timing_exact'] and x['settled_cells_maps_flags_loot_counter_keys_exact'] for x in report['cases'])
        elif name.startswith('timing'):
            assert all(x['differing_state_frames']==0 for x in report['natural_input_sequences'])
            assert report['enemy']['differing_motion_counter_frames']==0
        else:assert len(report['cases'])==1 and report['cases'][0]['loaded_state_cells_maps_flags_masks_loot_exact'] and report['cases'][0]['visible_wipe_frames_exact']==20
        evidence.append(dict(file=name,sha256=sha(raw)))
    paths=['megadrive/src/main.c','megadrive/src/room_puzzles.inc','tools/extract_room_puzzles.py','tools/extract_contact_scripts.py','tools/validate_room_cells.py','tools/puzzles_harness.c','tools/build_puzzles_harness.ps1','tools/validate_puzzles.py','tools/validate_puzzles_gameplay.py','tools/audit_puzzles_patch.py','analysis/baseline-v0054-main.c']
    report=dict(md_sha256=digest,source_sha256=sha(rom),md_size=len(md),checksum_aliases_verified=True,stationary_scripts=31,dispatch_order_preserved=True,baseline_main_v0054_sha256=sha(baseline.read_bytes()),all_other_production_files_unchanged=True,source_files={p:sha((ROOT/p).read_bytes()) for p in paths},current_reports=evidence,full_game_ported=False,limits=['496 selected puzzle fixture cases plus 7696 nonselected setup cases; two script calls per case.','124 live controller-trigger cases use controlled room/hero/frozen actor setup after a real dungeon entry.','Complete natural dungeon routes, ten item-message rewards, bosses, ending, full pixels, sound waveforms and redraw latency remain unverified.'])
    (ROOT/'validation/puzzles_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Stationary puzzle patch audit passed:',digest)

if __name__=='__main__':main()
