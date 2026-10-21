"""Bind source IRQ terrain-publication correction and gameplay checks to v0225."""
import json
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols

def main():
    rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom);evidence={};cases=[]
    for suffix in ['', '-pal']:
        oldname=f'analysis/cell_publication_v0224{suffix}_report.json';newname=f'analysis/cell_publication_v0225{suffix}_report.json'
        old=json.loads((ROOT/oldname).read_bytes());new=json.loads((ROOT/newname).read_bytes())
        assert old['md_sha256']=='6be955fdd0efeeb549b3b1a77f697989bed45b79b545c2d7f2ddd7bad8235549' and not old['passed']
        assert new['md_sha256']==digest and new['passed'] and not new['diagnostic_only']
        assert old['cases'][0]['publication_delay']==new['cases'][0]['publication_delay']==1
        assert old['cases'][1]['publication_delay']==0 and new['cases'][1]['publication_delay']==1
        assert new['framebuffer_mismatching_frames']==0 and len(new['records']['md'])==133
        assert all(r['framebuffer_pixels_compared']>0 for r in new['records']['md'].values())
        for report in [old,new]:
            a=bytes.fromhex(report['records']['sms']['2632']['physical_words']);b=bytes.fromhex(report['records']['md']['2632']['physical_words']);expected=b''
            for n in range(0,8,2):
                w=int.from_bytes(a[n:n+2],'little');attr=((w>>11)&1)<<13|((w>>12)&1)<<15|((w>>10)&1)<<12|((w>>9)&1)<<11|16+(w&511);expected+=attr.to_bytes(2,'big')
            assert b==expected and report['records']['sms']['2632']['software_words']==report['records']['md']['2632']['software_words']
        cases.append(dict(region=new['region'],source_publication_delay_frames=1,previous_native_publication_delay_frames=0,current_native_publication_delay_frames=1,coherent_native_patch_frames=133))
        for name in [oldname,newname]:evidence[name]=sha((ROOT/name).read_bytes())
    for suffix in ['', '-pal']:
        name=f'validation/puzzles_gameplay{suffix}_report.json';r=json.loads((ROOT/name).read_bytes());assert r['md_sha256']==digest and len(r['cases'])==62
        assert all(c['settled_cells_maps_flags_loot_counter_keys_exact'] and c['trigger_timing_exact'] for c in r['cases']);evidence[name]=sha((ROOT/name).read_bytes())
    name='validation/second_spell_terrain_report.json';r=json.loads((ROOT/name).read_bytes());assert r['md_sha256']==digest and len(r['cases'])==20
    assert all(c['frames_exact']==61 and c['stable_hardware_map_bytes_exact']==1280 for c in r['cases']);evidence[name]=sha((ROOT/name).read_bytes())
    name='analysis/natural_dungeon_progress_v0225_report.json';r=json.loads((ROOT/name).read_bytes());assert r['md_sha256']==digest and r['passed'] and not r['ram_mutations'];evidence[name]=sha((ROOT/name).read_bytes())
    assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535;assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');end=sy['_bend'];assert end<0xe800
    result=dict(md_sha256=digest,passed=True,checksum=f'{checksum:04X}',publication_cases=cases,controlled_stationary_puzzle_cases=124,controlled_spell_terrain_cases=20,natural_ntsc_dungeon_combat_rooms=9,natural_key_rewards=2,natural_keys_consumed=1,source_native_final_flags_equal_bytes=256,source_native_final_map_equal_bytes=1280,source_native_fresh_replay_final_ram_equal_bytes=73728,bss_end=end,bytes_above_bss=65536-end,evidence=evidence,source_files={n:sha((ROOT/n).read_bytes()) for n in ['megadrive/src/main.c','tools/validate_cell_publication.py','tools/natural_dungeon_combat.py','tools/verify_natural_dungeon_progress.py']},full_game_validated=False,first_dungeon_cleared=False,source_rng_exact=False,limits=['Cell mutation publication delay is measured on the controlled actor2B branch in PAL/NTSC; this is not proof of every IRQ boundary or VDP mutation family.','The framebuffer check covers opaque pixels of the16x16 terrain patch, not complete frames. The previous ROM already had coherent patch pixels but exposed the change one IRQ early.','Nine-room natural progression is NTSC; feedback inputs, route times, combat and HP differ from SMS. Boss/gem/full dungeon remain unfinished.'])
    (ROOT/'analysis/terrain_publication_v0225_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result['publication_cases'])

if __name__=='__main__':main()
