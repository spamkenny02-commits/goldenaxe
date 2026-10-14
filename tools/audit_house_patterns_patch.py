"""Bind the house metatile-offset correction to native/source evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    assert sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535==int.from_bytes(rom[0x18e:0x190],'big')
    old=json.loads((ROOT/'versions/v0096-0faff7e5/inventory_restore_patch_audit.json').read_bytes())
    base=ROOT/'analysis/house-animation-baseline-v0096/main.c';assert sha(base)==old['source_files']['megadrive/src/main.c']
    s=(ROOT/'megadrive/src/main.c').read_text();new='        u16 tile=scratch[0xe0]; /* 6A41: C9E0 relative to C900 metatiles. */'
    assert s.count(new)==1 and s.replace(new,'        u16 tile=scratch[0x1e0];')==base.read_text(),'Undeclared production changes'
    source=(ROOT/'input/original.sms').read_bytes();assert source[0x6a41:0x6a45]==bytes.fromhex('2ae0c926')
    prior=json.loads((ROOT/'versions/v0095-f2f9fdc1/fast_ground_patch_audit.json').read_bytes())
    for n,h in prior['source_files'].items():
        if n.startswith('megadrive/') and n!='megadrive/src/main.c':assert sha(ROOT/n)==h,n
    opening=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    for n,h in opening['unchanged_production_assets'].items():
        if n not in ['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/rom_header.c','megadrive/src/save.inc']:assert sha(ROOT/n)==h,n
    b=json.loads((ROOT/'validation/house_patterns_baseline_report.json').read_bytes());assert b['md_sha256']==sha(ROOT/'versions/v0096-0faff7e5/gaw-megadrive-v0096.bin') and len(b['cases'])==4 and all(len(c['difference_frames'])==59 for c in b['cases'])
    reports=[]
    for n in ['house_patterns_report.json','inventory_restore_report.json','merchant_report.json']:
        p=ROOT/'validation'/n;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,n
        if n=='house_patterns_report.json':assert len(d['cases'])==4 and all(c['frames_exact']==118 and not c['difference_frames'] for c in d['cases'])
        elif n=='inventory_restore_report.json':assert len(d['cases'])==6 and all(all(not f for f in c['static_background_pattern_difference_indices'].values()) and not c['early_native_static_pattern_changes_from_before_menu'] for c in d['cases'])
        else:assert len(d['cases'])==7 and d['natural_walk_refusal_exit_without_ram_injection']
        reports.append(dict(file=n,sha256=sha(p)))
    names=['megadrive/src/main.c','tools/validate_house_patterns.py','tools/validate_inventory_restore.py','tools/audit_house_patterns_patch.py','analysis/house_patterns_milestone.md','analysis/house-animation-baseline-v0096/main.c','analysis/house-animation-baseline-v0096/symbol.txt']
    result=dict(md_sha256=digest,source_sha256=sha(ROOT/'input/original.sms'),only_house_animation_destination_lookup_changed=True,source_files={n:sha(ROOT/n) for n in names},reports=reports,baseline_removed_differing_frames=236,baseline_report_sha256=sha(ROOT/'validation/house_patterns_baseline_report.json'),full_game_ported=False,limits=['Four clock-aligned house animation cases, six static inventory-return cases and first-merchant regressions only.','All houses, complete framebuffers/audio, global phase, full gameplay and scroll timing remain unverified or incomplete.'])
    (ROOT/'validation/house_patterns_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('House patterns patch audit passed',digest)
if __name__=='__main__':main()
