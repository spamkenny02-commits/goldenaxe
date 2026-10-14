"""Bind SRAM-derived dungeon animation and item-recovery timing evidence."""
import hashlib,json,re
from extract_dungeon_bitmaps import ROOT,extract

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    rom=(ROOT/'input/original.sms').read_bytes();md=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(md)
    assert len(md)==524288 and md==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(md[n:n+2],'big') for n in range(0x200,len(md),2))&65535;assert int.from_bytes(md[0x18e:0x190],'big')==checksum
    old=json.loads((ROOT/'versions/v0060-b2742e83/item_rewards_patch_audit.json').read_bytes())
    base=ROOT/'analysis/baseline-v0060-main.c';assert sha(base.read_bytes())==old['source_files']['megadrive/src/main.c']
    s=(ROOT/'megadrive/src/main.c').read_text().replace('static u16 dungeon_bitmap_pending;\n\n','')
    a=s.index('    if(dungeon_bitmap_pending)');b=s.index('    if(house_animation_patterns_pending)',a);s=s[:a]+s[b:]
    a=s.index('extern const u8 dungeon_animation_bitmaps[];');b=s.index('/* 6AA5..6AEA:',a);s=s[:a]+s[b:]
    s=s.replace('dungeon_animation_scan=dungeon_animation_phase=0;dungeon_bitmap_pending=0;','dungeon_animation_scan=dungeon_animation_phase=0;').replace('animate_dungeon_bitmaps();animate_dungeon_cells();','animate_dungeon_cells();').replace('started=vtimer;update_world_music();hero_state=0;','update_world_music();hero_state=0;')
    a=s.index('    inventory_hud_icon();hero_loaded_pose=65535;prepare_hero_patterns();update_hero_sprites();\n    /* 637D');b=s.index('    item_reward_active=0;',a)
    s=s[:a]+'    inventory_hud_icon();hero_loaded_pose=65535;prepare_hero_patterns();update_hero_sprites();redraw_current_room(vtimer);\n'+s[b:];assert s==base.read_text()
    previous=json.loads((ROOT/'versions/v0060-b2742e83/item_rewards_report.json').read_bytes())['source_copies']
    for name,h in previous.items():
        if name!='main.c':assert sha((ROOT/'megadrive/src'/name).read_bytes())==h,name
    start,end,decoded=extract(rom);data=(ROOT/'megadrive/src/dungeon_animation_data.c').read_text();match=re.search(r'dungeon_animation_bitmaps\[\]\s*=\s*\{(.*?)\}',data,re.S)
    assert bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',match[1]))==decoded[:576]
    reference=json.loads((ROOT/'analysis/dungeon_bitmap_reference.json').read_bytes());assert reference['source_sha256']==sha(rom) and reference['compressed_start']==start and reference['compressed_end']==end
    cost=json.loads((ROOT/'analysis/reward_restore_cost.json').read_bytes());assert cost['source_sha256']==sha(rom)
    assert len(cost['measurements'])==6
    source_evidence=[]
    for suffix in ['', '-pal']:
        p=ROOT/f'analysis/dungeon-bitmaps-source-v0063/reward_restore_timing{suffix}_profile.json';raw=p.read_bytes();d=json.loads(raw);assert d['source_sha256']==sha(rom)
        for case in d['cases']:
            events=case['events'];first=next(x for x in events if x['pc']==0x637d);last=next(x for x in events if x['pc']==0x1de2 and x['master_cycles']>first['master_cycles'])
            measured=(last['master_cycles']-first['master_cycles']-(last['irq_master_cycles']-first['irq_master_cycles']))//15
            row=next(x for x in cost['measurements'] if x['region']==d['region'] and x['room']==case['room']);assert measured==row['foreground_tstates'] and sha(raw)==row['profile_sha256']
        source_evidence.append(dict(file=str(p.relative_to(ROOT)),sha256=sha(raw)))
    names=['dungeon_bitmaps_report.json','dungeon_bitmaps_gameplay_report.json','dungeon_bitmaps_gameplay-pal_report.json','reward_floor_phase_report.json','item_rewards_report.json','item_rewards_gameplay_report.json','item_rewards_gameplay-pal_report.json','item_rewards_visuals_report.json','timing_report.json','timing-pal_report.json']
    evidence=[]
    for name in names:
        p=ROOT/'validation'/name;raw=p.read_bytes();d=json.loads(raw);assert d['md_sha256']==digest,name
        if name=='dungeon_bitmaps_report.json':assert d['cases_checked']==8192 and d['source_upload_commands']==1024 and d['source_pattern_bytes_and_native_pending_upload_exact']
        elif name.startswith('dungeon_bitmaps_gameplay'):assert d['cases'][0]['frames_compared']==93 and d['cases'][0]['source_native_vram_patterns_and_clock_exact']
        elif name=='reward_floor_phase_report.json':assert len(d['cases'])==6 and all(-1<=x['resume_delta']<=1 and x['aligned_scan_phase_frames_exact']==180 for x in d['cases'])
        elif name=='item_rewards_report.json':assert d['inventory_writes_exact'] and d['cases_checked']==8192
        elif name.startswith('item_rewards_gameplay'):assert len(d['cases'])==22 and all(x['inventory_flags_nonanimated_cells_maps_loot_music_exact'] for x in d['cases'])
        elif name=='item_rewards_visuals_report.json':assert len(d['cases'])==20
        else:assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        evidence.append(dict(file=name,sha256=sha(raw)))
    paths=['megadrive/src/main.c','megadrive/src/dungeon_animation_data.c','tools/extract_dungeon_bitmaps.py','tools/validate_dungeon_bitmaps.py','tools/dungeon_bitmaps_harness.c','tools/build_dungeon_bitmaps_harness.ps1','tools/validate_dungeon_bitmaps_gameplay.py','tools/profile_reward_floor_phase.py','tools/profile_reward_restore_timing.py','tools/validate_reward_floor_phase.py','tools/audit_dungeon_bitmaps_patch.py','analysis/baseline-v0060-main.c','analysis/reward_restore_cost.json']
    phase=json.loads((ROOT/'validation/reward_floor_phase_report.json').read_bytes())
    report=dict(md_sha256=digest,source_sha256=sha(rom),md_size=len(md),checksum=hex(checksum),aliases_verified=True,sram_animation_resource_exact=True,previous_production_files_except_main_unchanged=True,source_files={p:sha((ROOT/p).read_bytes()) for p in paths},source_timing_evidence=source_evidence,current_reports=evidence,recovery_cases=phase['cases'],full_game_ported=False,limits=['Live bitmap test synchronizes the source/native IRQ clock once; natural absolute clock phase remains unproven.','Source closing/HUD timing is measured in three controlled rooms per region; recovery and steady floor phase retain a one-frame NTSC offset.','Full natural dungeon progression, all item abilities, enemies/bosses, ending, full framebuffers and audio waveforms remain incomplete or unverified.'])
    (ROOT/'validation/dungeon_bitmaps_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Dungeon bitmap and recovery audit passed:',digest)

if __name__=='__main__':main()
