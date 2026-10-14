"""Save/cold-load actual clear-reward and collected-key state through normal menus.

Door state comes from the live gameplay comparison. A fixture transfers it to
the established save-point route; travel from dungeon to that save point is
not implied. Production save and cold-boot loading execute without ROM edits.
"""
import contextlib,hashlib,io,json,re
from validate_save import ROUTE,native
from run_core import ROOT,run


def main():
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in
        (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    source=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin'
    digest=hashlib.sha256(md.read_bytes()).hexdigest()
    game_report=json.loads((ROOT/'validation/item_rewards_gameplay_report.json').read_bytes())
    assert game_report['md_sha256']==digest
    results=[]
    for case in game_report['cases']:
        if not case['reward_window_tile_words_exact']:continue
        slot=0;inventory=f"{case['room']:03x}"
        sf=ROOT/f'validation/sms-clear-gameplay-{inventory}-False-item-rewards-0'
        nf=ROOT/f'validation/md-clear-gameplay-{inventory}-False-item-rewards-0'
        assert json.loads((nf/'capture.json').read_bytes())['rom_sha256']==digest
        s=(sf/'ram_03900.bin').read_bytes();n=native(nf,3900)
        flags=s[0x100:0x200];keys=s[0xde];items=s[0xe0:0xf1]
        assert n[sy['game_save_state']+0x50:sy['game_save_state']+0x150]==flags
        assert int.from_bytes(n[sy['hero_keys']:sy['hero_keys']+2],'big')==keys
        assert bytes([int.from_bytes(n[sy['hero_basic_level']:sy['hero_basic_level']+2],'big'),int.from_bytes(n[sy['hero_weapon_level']:sy['hero_weapon_level']+2],'big')])+n[sy['hero_items']+2:sy['hero_items']+17]==items
        assert flags[case['room']&255]&4
        srams={}
        for tag,path in [('sms',source),('md',md)]:
            out=ROOT/f'validation/{tag}-item-reward-save-{inventory}';sr=out.with_suffix('.srm')
            writes=[(3340,0x100,flags),(3340,0xde,bytes([keys])),(3340,0xe0,items)] if tag=='sms' else [
                (3340,sy['game_save_state']+0x50,flags),(3340,sy['hero_keys'],keys.to_bytes(2,'big')),
                (3340,sy['hero_items'],items),(3340,sy['hero_basic_level'],items[0].to_bytes(2,'big')),(3340,sy['hero_weapon_level'],items[1].to_bytes(2,'big'))]
            inputs=ROUTE+[(3700,3710,8)]+([(3820,3825,5)] if slot else [])+[(3900,3910,8),(4200,4210,8)]
            with contextlib.redirect_stdout(io.StringIO()):
                run(path,4400,out,{4400},([(200,220,0)] if tag=='sms' else [])+inputs,ram_writes=writes,sram_out=sr)
            raw=sr.read_bytes();srams[tag]=(raw[1::2] if tag=='md' else raw).ljust(8192,b'\xff')
            cold=ROOT/f'validation/{tag}-item-reward-save-reload-{inventory}'
            with contextlib.redirect_stdout(io.StringIO()):
                run(path,1920,cold,{1920},([(200,220,0)] if tag=='sms' else [])+
                    [(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)],sram_in=sr)
            r=(cold/'ram_01920.bin').read_bytes() if tag=='sms' else native(cold,1920)
            actual_flags=r[0x100:0x200] if tag=='sms' else r[sy['game_save_state']+0x50:sy['game_save_state']+0x150]
            actual_keys=r[0xde] if tag=='sms' else int.from_bytes(r[sy['hero_keys']:sy['hero_keys']+2],'big')
            actual_items=r[0xe0:0xf1] if tag=='sms' else bytes([int.from_bytes(r[sy['hero_basic_level']:sy['hero_basic_level']+2],'big'),int.from_bytes(r[sy['hero_weapon_level']:sy['hero_weapon_level']+2],'big')])+r[sy['hero_items']+2:sy['hero_items']+17]
            assert actual_flags==flags and actual_keys==keys and actual_items==items,(inventory,tag,'cold load')
            actual_speed=r[0xee] if tag=='sms' else int.from_bytes(r[sy['hero_attack_speed']:sy['hero_attack_speed']+2],'big')
            assert actual_speed==items[14],(inventory,tag,'boots speed after cold load')
        base=0x400+slot*0x400
        assert srams['sms'][base:base+592]==srams['md'][base:base+592],(inventory,'full save payload')
        results.append(dict(inventory=inventory,slot=slot+1,save_payload_bytes_exact=592,
                            persistent_room_flag_bytes_cold_loaded=256,keys_cold_loaded=keys,inventory_bytes_cold_loaded=items.hex(),running_boots_speed_cold_loaded=items[14]))
        print(inventory,'reward state saved and cold-loaded through normal menus',flush=True)
    report=dict(md_sha256=digest,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cases=results,
                state_provenance='Actual controller-triggered item reward snapshots, transferred to save-point route by fixture.',
                production_save_and_cold_load_by_normal_input=True,
                uninterrupted_dungeon_to_save_point_route_verified=False,full_game_ported=False)
    (ROOT/'validation/item_rewards_save_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
