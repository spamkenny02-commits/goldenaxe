"""Audit the room-class inventory restore fix and bind targeted evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    assert sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535==int.from_bytes(rom[0x18e:0x190],'big')
    old=json.loads((ROOT/'versions/v0095-f2f9fdc1/fast_ground_patch_audit.json').read_bytes())
    base=ROOT/'analysis/inventory-restore-baseline-v0095/main.c';assert sha(base)==old['source_files']['megadrive/src/main.c']
    s=(ROOT/'megadrive/src/main.c').read_text().replace('Restore the current graphics class when the menu releases its patterns.','The currently ported exterior class uses the original global map resource.')
    new='    decode_planes(world_graphics_class==2?world_dungeon_background_rle:\n        world_graphics_class==1?world_house_background_rle:world_background_rle,sms_vram,4);'
    assert s.count(new)==1;s=s.replace(new,'    decode_planes(world_background_rle,sms_vram,4);');assert s==base.read_text(),'Undeclared main.c changes'
    for n,h in old['source_files'].items():
        if n.startswith('megadrive/') and n!='megadrive/src/main.c':assert sha(ROOT/n)==h,n
    opening=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    for n,h in opening['unchanged_production_assets'].items():
        if n not in ['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/rom_header.c','megadrive/src/save.inc']:assert sha(ROOT/n)==h,n
    d=json.loads((ROOT/'validation/inventory_restore_report.json').read_bytes());b=json.loads((ROOT/'validation/inventory_restore_baseline_report.json').read_bytes())
    assert b['md_sha256']==sha(ROOT/'versions/v0095-f2f9fdc1/gaw-megadrive-v0095.bin') and len(b['cases'])==len(d['cases'])==6
    for c in d['cases']:
        before=next(x for x in b['cases'] if (x['name'],x['region'])==(c['name'],c['region']))
        assert all(not v for v in c['static_background_pattern_difference_indices'].values()) and not c['early_native_pattern_changes_from_before_menu']
        if c['graphics_class']==1:assert len(before['static_background_pattern_difference_indices']['3470'])>100
    reports=[]
    for n in ['inventory_restore_report.json','inventory_report.json','merchant_report.json']:
        p=ROOT/'validation'/n;r=json.loads(p.read_bytes());assert r['md_sha256']==digest,n
        if n=='inventory_report.json':assert r['return_secondary_attack_states_exact']==31
        if n=='merchant_report.json':assert len(r['cases'])==7 and r['natural_walk_refusal_exit_without_ram_injection']
        reports.append(dict(file=n,sha256=sha(p)))
    paths=['megadrive/src/main.c','tools/validate_inventory_restore.py','tools/audit_inventory_restore_patch.py','analysis/inventory_restore_milestone.md','analysis/inventory-restore-baseline-v0095/main.c','analysis/inventory-restore-baseline-v0095/symbol.txt']
    result=dict(md_sha256=digest,source_sha256=sha(ROOT/'input/original.sms'),only_declared_inventory_background_resource_selection_changed=True,source_files={n:sha(ROOT/n) for n in paths},reports=reports,baseline_report_sha256=sha(ROOT/'validation/inventory_restore_baseline_report.json'),full_game_ported=False,limits=d['limits'])
    (ROOT/'validation/inventory_restore_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Inventory restore patch audit passed',digest)
if __name__=='__main__':main()
