"""Audit native slot-5 translation and bounded original-ROM comparisons."""
import hashlib,json,re
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535
    assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
    assert int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
    assert rom[0x1b0:0x1bc]==bytes.fromhex('5241f8200020000100203fff')
    old=json.loads((ROOT/'versions/v0082-365b546d/dialogue_controls_patch_audit.json').read_bytes())
    assets=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())['unchanged_production_assets']
    basepath=ROOT/'analysis/second-spell-baseline-v0082'
    assert sha(basepath/'main.c')==old['source_files']['megadrive/src/main.c']
    current=(ROOT/'megadrive/src/main.c').read_text();base=(basepath/'main.c').read_text()
    start='static void activate_hero_item(';stop='static void attack_hero('
    a=current.index(start);b=current.index(stop,a);x=base.index(start);y=base.index(stop,x)
    current=current[:a]+base[x:y]+current[b:]
    a=current.index('extern const u8 world_second_spell_terrain[]');b=current.index('/* 5C96 marks passages',a)
    current=current[:a]+current[b:]
    current=current.replace('tick_world_spell(sms_vram+0x3800,world_spell_state[0]==4?hero_items[5]:hero_items[4]);','tick_world_spell(sms_vram+0x3800,hero_items[4]);')
    assert current==base,'Main changes outside the declared spell translation'
    assert sha(basepath/'actors.c')==assets['megadrive/src/actors.c']
    current=(ROOT/'megadrive/src/actors.c').read_text();base=(basepath/'actors.c').read_text()
    a=current.index('void tick_world_spell(');b=current.index('static u16 descriptor_word(u16 address)\n{',a)
    x=base.index('void tick_world_spell(');y=base.index('static u16 descriptor_word(u16 address)\n{',x)
    current=current[:a]+base[x:y]+current[b:]
    current=current.replace('extern const u8 world_second_spell_velocity[];\n','').replace('extern bool mutate_world_spell_terrain(u8 *entity,u16 level);\n','')
    assert current==base,'Actor changes outside the declared spell translation'
    for name,h in assets.items():
        if name not in ['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/rom_header.c']:assert sha(ROOT/name)==h,name
    old80=json.loads((ROOT/'versions/v0080-6aee1373/dialogue_publication_patch_audit.json').read_bytes())
    for name in ['build.ps1','megadrive/src/rom_header.c']:assert sha(ROOT/name)==old80['source_files'][name]
    original=(ROOT/'input/original.sms').read_bytes();resource=json.loads((ROOT/'analysis/second_spell_resources.json').read_bytes())
    generated=ROOT/'megadrive/src/second_spell_data.c';assert sha(generated)==resource['generated_sha256']
    for name,(a,b) in resource['resource_offsets'].items():
        body=re.search(r'\b'+name+r'\[\]\s*=\s*\{([^}]+)',generated.read_text())[1]
        assert bytes(int(v,16) for v in re.findall(r'0x([0-9a-fA-F]+)',body))==original[a:b]
    reports=[]
    for name,count in [('second_spell_report.json',22),('second_spell_terrain_report.json',20),('second_spell_terrain_special_report.json',4),('second_spell_fire_regression_report.json',22),('timing_report.json',None),('timing-pal_report.json',None),('fire_beam_diagnostic.json',6)]:
        p=ROOT/'validation'/name;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,name
        if count is not None:assert len(d['cases'])==count,name
        if name=='second_spell_report.json':assert all(c['frames_exact']==121 for c in d['cases'])
        elif 'terrain' in name:assert all(c['frames_exact']==61 and c['stable_hardware_map_bytes_exact']==1280 for c in d['cases'])
        elif name=='second_spell_fire_regression_report.json':
            bad=[c for c in d['cases'] if c['source_differences']]
            assert len(bad)==2 and all(c['known_baseline_difference'] and c['region']=='pal' and c['initial_magic'] in [0,7] and c['source_differences']==[[2810,['fields']]] for c in bad)
        elif name.startswith('timing'):assert all(c['differing_state_frames']==0 for c in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        else:assert d['diagnostic_only'] and d['baseline_rebuild_byte_exact']
        reports.append(dict(file=name,sha256=sha(p)))
    paths=['megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/actors.h','megadrive/src/second_spell_data.c','tools/validate_second_spell.py','tools/validate_second_spell_terrain.py','tools/extract_second_spell.py','tools/audit_second_spell_patch.py','analysis/second_spell_resources.json','analysis/second-spell-baseline-v0082/main.c','analysis/second-spell-baseline-v0082/actors.c','tools/profile_fire_beam.py','validation/fire_insufficient_baseline_pal-0-1-0.json','validation/fire_insufficient_baseline_pal-0-1-7.json']
    result=dict(md_sha256=digest,source_sha256=hashlib.sha256(original).hexdigest(),md_bytes=len(rom),checksum=hex(checksum),baseline_v0082_restored_exactly_outside_declared_spell_changes=True,original_resource_bytes_exact=54,source_files={p:sha(ROOT/p) for p in paths},reports=reports,full_game_ported=False,limits=['Controlled ownership/position/clock, terrain fixtures; no natural acquisition, damage, complete dungeon route, save/re-entry or complete playthrough proof.','Fire insufficient-magic PAL attack-strength update differs on one frame in two cases, also present in exact v0082.','Fire image comparison remains imperfect: 190 differing normalized pixels at frame 3749 in v0082 and current; current has five additional differences at frame 3751. Diagnostic only.','Audio waveforms, global scanline timing, complete enemies/bosses, remaining abilities, quests and ending remain unfinished.'])
    (ROOT/'validation/second_spell_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Second spell audit passed',digest)
if __name__=='__main__':main()
