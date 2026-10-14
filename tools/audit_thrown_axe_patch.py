"""Bind native water/axe resources and bounded original-ROM runtime comparisons."""
import hashlib,json,re
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535
    assert checksum==int.from_bytes(rom[0x18e:0x190],'big') and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    assert rom[0x1b0:0x1bc]==bytes.fromhex('5241f8200020000100203fff')
    previous=json.loads((ROOT/'versions/v0084-7de7d76b/second_spell_patch_audit.json').read_bytes())
    for name in ['main.c','actors.c']:assert sha(ROOT/'analysis/thrown-axe-baseline-v0084'/name)==previous['source_files']['megadrive/src/'+name]
    for name in ['megadrive/src/actors.h','megadrive/src/second_spell_data.c']:assert sha(ROOT/name)==previous['source_files'][name]
    old=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    for name,h in old['unchanged_production_assets'].items():
        if name not in ['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/rom_header.c']:assert sha(ROOT/name)==h,name
    old80=json.loads((ROOT/'versions/v0080-6aee1373/dialogue_publication_patch_audit.json').read_bytes())
    for name in ['build.ps1','megadrive/src/rom_header.c']:assert sha(ROOT/name)==old80['source_files'][name]
    original=(ROOT/'input/original.sms').read_bytes();resource=json.loads((ROOT/'analysis/thrown_axe_resources.json').read_bytes());p=ROOT/'megadrive/src/thrown_axe_data.c'
    assert sha(p)==resource['generated_sha256'] and resource['source_sha256']==hashlib.sha256(original).hexdigest()
    for name,ranges in resource['ranges'].items():
        body=re.search(r'\b'+name+r'\[\]\s*=\s*\{([^}]+)',p.read_text())[1]
        assert bytes(int(v,16) for v in re.findall(r'0x([0-9a-fA-F]+)',body))==b''.join(original[a:b] for a,b in ranges)
    assert int.from_bytes(original[0x2ee1:0x2ee3],'little')==0x2fd2
    assert original[0x2de2:0x2de5]==bytes.fromhex('cd4230')
    reports=[]
    for name,count in [('thrown_axe_report.json',22),('thrown_axe_walk_report.json',16),('thrown_axe_walk_fast_report.json',16),('second_spell_report.json',22),('second_spell_fire_regression_report.json',22),('timing_report.json',None),('timing-pal_report.json',None)]:
        p=ROOT/'validation'/name;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,name
        if count is not None:assert len(d['cases'])==count
        if name.startswith('thrown_axe'):
            assert all(c['frames_exact']==121 and c['hero_water_pattern_frames_exact']==118 for c in d['cases'])
            if name=='thrown_axe_report.json':assert all(c['active_projectile_pattern_frames_exact']>0 for c in d['cases'])
            else:assert all(c['active_projectile_pattern_frames_exact']==0 for c in d['cases']) and d['water_walking']
        elif name=='second_spell_report.json':assert all(c['frames_exact']==121 for c in d['cases'])
        elif name=='second_spell_fire_regression_report.json':assert all(c['frames_exact']==121 and not c['source_differences'] for c in d['cases'])
        else:assert all(c['differing_state_frames']==0 for c in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        reports.append(dict(file=name,sha256=sha(p)))
    paths=['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/thrown_axe_data.c','tools/validate_second_spell.py','tools/extract_thrown_axe.py','tools/audit_thrown_axe_patch.py','analysis/thrown_axe_resources.json','analysis/thrown_axe_milestone.md','analysis/thrown-axe-main.c.diff','analysis/thrown-axe-actors.c.diff','validation/thrown-axe-walk-fast.log']
    result=dict(md_sha256=digest,source_sha256=hashlib.sha256(original).hexdigest(),md_bytes=len(rom),checksum=hex(checksum),resource_bytes_original_exact=sum(resource['resource_bytes'].values()),source_files={name:sha(ROOT/name) for name in paths},reports=reports,controlled_water_cases=54,full_game_ported=False,limits=['Within-room controlled water map/equipment/position/clock, not natural water arrival, shoreline collisions, combat damage, acquisition, save/re-entry or complete playthrough.','Longer fast downward exploratory run crosses a room boundary and exposes mutable-cell loading-phase mismatch; preserved in log.','Other terrain contexts are classified but not fully implemented. Previously observed fire PAL state differences do not recur in these 22 current cases; full fire images have not been revalidated.','Full enemy/boss behavior, remaining abilities, quests, ending, global timing and audio waveforms remain unfinished.'])
    (ROOT/'validation/thrown_axe_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Water/axe audit passed',digest)
if __name__=='__main__':main()
