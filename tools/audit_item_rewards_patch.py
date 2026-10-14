"""Bind native item acquisition changes to original ROM and runtime evidence."""
import hashlib,json,re
from extract_item_rewards import ROOT,records

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    source=(ROOT/'input/original.sms').read_bytes();md=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(md)
    assert len(md)==524288
    assert md==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(md[p:p+2],'big') for p in range(0x200,len(md),2))&65535
    assert int.from_bytes(md[0x18e:0x190],'big')==checksum
    old=json.loads((ROOT/'versions/v0056-e9694529/puzzles_patch_audit.json').read_bytes())
    baseline=ROOT/'analysis/baseline-v0056-main.c';assert sha(baseline.read_bytes())==old['source_files']['megadrive/src/main.c']
    s=(ROOT/'megadrive/src/main.c').read_text().replace('#include "item_rewards.inc"\n','')
    a=s.index('extern const u8 reward_labels[]');b=s.index('/* 6AA5..6AEA:',a);s=s[:a]+s[b:]
    s=s.replace('check_dungeon_key_door();check_dungeon_item_reward(script_flags);','check_dungeon_key_door();')
    assert s==baseline.read_text(),'Unrelated production main change'
    copies=json.loads((ROOT/'versions/v0056-e9694529/puzzles_report.json').read_bytes())['source_copies']
    for name,h in copies.items():
        if name!='main.c':assert sha((ROOT/'megadrive/src'/name).read_bytes())==h,name
    reference=json.loads((ROOT/'analysis/item_rewards_reference.json').read_bytes());assert reference['source_sha256']==sha(source)
    items=records(source);labels=bytearray();indices=bytearray()
    generated=['/* Source 5D59: room/coordinate/inventory offset/value/item/weapon guard. */','static const u16 world_item_rewards[10][6] = {']
    for x in items:
        assert x['call_site']==x['entry']+3
        p=int.from_bytes(source[0x63b3+x['item']*2:0x63b5+x['item']*2],'little');offset=0xc000+(p&0x3fff);end=source.index(0,offset)+1
        x.update(label_pointer=p,label_hex=source[offset:end].hex());indices.extend(len(labels).to_bytes(2,'little'));labels.extend(source[offset:end])
        generated.append('    {'+','.join(str(v) for v in [x['room'],x['coordinate'],x['inventory_offset'],x['value'],x['item'],int(x['requires_weapon_absent'])])+'},')
    generated.append('};');assert (ROOT/'megadrive/src/item_rewards.inc').read_text()=='\n'.join(generated)+'\n'
    assert reference['records']==items
    assets={'reward_labels':labels,'reward_label_index':indices,'reward_hero_bitmap':source[0x12241:0x12241+145],'reward_hero_frame':bytes([8])+source[0x304b6:0x304b6+24]}
    c=(ROOT/'megadrive/src/item_rewards_data.c').read_text()
    for name,data in assets.items():
        match=re.search(name+r'\[\]\s*=\s*\{(.*?)\};',c,re.S);assert match,name
        assert bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',match[1]))==data,name
    assert source[0x636c:0x636e]==bytes.fromhex('06b4')
    reports=['item_rewards_report.json','item_rewards_gameplay_report.json','item_rewards_gameplay-pal_report.json','item_rewards_visuals_report.json','item_rewards_save_report.json','timing_report.json','timing-pal_report.json']
    evidence=[];floor=[]
    for name in reports:
        path=ROOT/'validation'/name;raw=path.read_bytes();d=json.loads(raw);assert d['md_sha256']==digest,name
        if name=='item_rewards_report.json':assert d['cases_checked']==8192 and d['inventory_writes_exact'] and d['source_cells_maps_all_room_flags_and_key_count_exact']
        elif name.startswith('item_rewards_gameplay'):
            assert len(d['cases'])==22 and all(x['inventory_flags_nonanimated_cells_maps_loot_music_exact'] for x in d['cases'])
            for x in d['cases']:
                if x['post_confirmation_floor_state_differences']:floor.append(dict(region=d['region'],room=x['room'],differences=x['post_confirmation_floor_state_differences']))
        elif name=='item_rewards_visuals_report.json':assert len(d['cases'])==20 and all(x['window_words']==150 and x['tiles_pixels_exact']==38 and x['held_pose_sprites_exact']==8 for x in d['cases'])
        elif name=='item_rewards_save_report.json':assert len(d['cases'])==10 and d['production_save_and_cold_load_by_normal_input'] and all(x['save_payload_bytes_exact']==592 for x in d['cases'])
        else:
            assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences'])
            assert d['enemy']['differing_motion_counter_frames']==0
        evidence.append(dict(file=name,sha256=sha(raw)))
    paths=['megadrive/src/main.c','megadrive/src/item_rewards.inc','megadrive/src/item_rewards_data.c','tools/extract_item_rewards.py','tools/profile_item_rewards.py','tools/validate_room_cells.py','tools/item_rewards_harness.c','tools/build_item_rewards_harness.ps1','tools/validate_item_rewards.py','tools/validate_item_rewards_gameplay.py','tools/validate_item_rewards_save.py','tools/audit_item_reward_visuals.py','tools/audit_item_rewards_patch.py','analysis/baseline-v0056-main.c']
    report=dict(md_sha256=digest,source_sha256=sha(source),md_size=len(md),checksum=hex(checksum),checksum_aliases_verified=True,item_scripts=10,source_table_and_assets_exact=True,all_prior_production_files_except_main_unchanged=True,baseline_main_v0056_sha256=sha(baseline.read_bytes()),source_files={p:sha((ROOT/p).read_bytes()) for p in paths},current_reports=evidence,known_post_confirmation_floor_differences=floor,full_game_ported=False,limits=['160 selected original/native grant fixtures; 8032 nonselected room setup cases. Modal frontend excluded from unit tests.','44 live cases compare inventory, flags, nonanimated cells/maps, loot and music commands; complete natural dungeon routes are not established.','Stable reward windows match VRAM words, tile pixels and sprite entries; full framebuffer sequences, sound waveforms and redraw latency are unverified.','Ten actual earned inventories and room flags are transferred to the save-point route, then saved/cold-loaded through normal menus. Uninterrupted travel to that save point is unverified.','Post-confirmation animated floor phase differences remain in the listed rooms. All item abilities, quests, bosses and ending are not complete.'])
    (ROOT/'validation/item_rewards_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Item acquisition patch audit passed:',digest)

if __name__=='__main__':main()
