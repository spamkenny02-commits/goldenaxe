"""Bind full-layer actor assets, native loader execution and 43..45 behavior."""
import hashlib,json,re
from actor_reference import ROOT,load_room_actors
from finalize_md_rom import md_checksum


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(data)
    assert len(data)==524288
    assert int.from_bytes(data[0x18e:0x190],'big')==md_checksum(data)
    for alias in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
        assert (ROOT/alias).read_bytes()==data
    original=(ROOT/'input/original.sms').read_bytes()
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    types=original[0x3234e:0x3334e];base=sy['actor_room_types']
    assert data[base:base+4096]==types
    assets=json.loads((ROOT/'analysis/actor_assets.json').read_bytes())
    assert assets['room_count']==512 and assets['pattern_offset_bytes']==4
    assert assets['unique_graphic_types']==80 and assets['pattern_bytes']==89408
    total=0
    for item in assets['resources']:
        t=item['type'];room=next(i for i in range(512) if t in types[i*8:i*8+8])
        _,patterns,_,_,entries=load_room_actors(original,room)
        entry=next(e for e in entries if e['type']==t)
        start=0x2000+entry['tile_base']*32;size=entry['tile_count']*32
        p=sy['actor_pattern_index']+t*4
        assert int.from_bytes(data[p:p+4],'big')==total
        assert data[sy['actor_tile_counts']+t]==entry['tile_count']
        p=sy['actor_patterns']+total
        assert data[p:p+size]==patterns[start:start+size]
        total+=size
    assert total==89408 and total>65535
    p=sy['actor_projectile_templates']+9*22
    assert data[p:p+22]==original[0x4399:0x43af]
    names=['dungeon_walkers','dungeon_walkers-pal','dungeon_walker_spawns','dungeon_walker_spawns-pal',
           'actor_loader_harness','sprite_overflow','walker40','scroll_objects','scroll_objects-pal',
           'timing','timing-pal','title_cadence','title_cadence-pal','intro','intro-pal']
    evidence=[]
    for name in names:
        path=ROOT/f'validation/{name}_report.json';raw=path.read_bytes();r=json.loads(raw)
        assert r['md_sha256']==digest,name
        if name in ['dungeon_walkers','dungeon_walkers-pal']:
            assert r['deterministic_cases']==48 and r['blocked_cases']==24
            assert len(r['controlled_decisions'])==288 and len(r['projectile_culls'])==8
            assert r['record_comparisons']==5808
        if name.startswith('dungeon_walker_spawns'):
            assert len(r['accepted'])==3 and len(r['rejected'])==12
        if name=='actor_loader_harness':
            assert r['native_68000_loader_executed'] and r['room_mask_cases']==1536
            assert r['source_copies_exact'] and r['pattern_bytes_compared']==50331648
            for file in ['actors.c','actors.h','actor_data.c']:
                assert r['source_files'][file]==sha((ROOT/f'megadrive/src/{file}').read_bytes())
        evidence.append(dict(file=path.name,sha256=sha(raw)))
    audit=dict(md_sha256=digest,source_sha256=sha(original),evidence=evidence,
               rom_bytes=len(data),additive_checksum_valid=True,aliases_equal=True,
               actor_asset_rooms=512,actor_graphic_types=80,actor_pattern_bytes=total,
               actor_pattern_offset_bytes=4,actor_assets=assets['resources'],
               native_loader_cases=1536,behavior_record_comparisons=11616,
               natural_dungeon_entry_verified=False,story_conditionals_ported=False,
               all_enemy_behaviors_ported=False,full_game_ported=False,
               source_files={name:sha((ROOT/name).read_bytes()) for name in
                   ['megadrive/src/actors.c','megadrive/src/actor_data.c','tools/extract_actors.py',
                    'tools/validate_dungeon_walkers.py','tools/validate_actor_loader_harness.py']})
    (ROOT/'validation/dungeon_walkers_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(f'{len(evidence)} reports, 80 source-exact graphic types, 1536 native loader cases: {digest}')


if __name__=='__main__':main()
