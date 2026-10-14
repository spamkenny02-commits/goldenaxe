"""Normal menu input reaches heal/potion usage; only initial possession/stats injected."""
import hashlib,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    rom=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    cases=[]
    for kind in [7,8]:
        route=[(2800,2805,0),(2825,2827,5)]
        if kind==7:route +=[(2830,2832,7),(2835,2837,7),(2840,2842,7),(2845,2847,8),(2860,2865,0),(2900,2906,8)]
        else:route +=[(2830,2832,5),(2835,2837,8),(2850,2855,0),(2890,2908,8)]
        source=ROOT/f'validation/sms-healing-route-{kind}';target=ROOT/f'validation/md-healing-route-{kind}';items=bytearray(17);items[0]=items[kind]=1
        run(rom,2960,source,{2960},[(200,220,0)]+PRESSES[:8]+route,ram_writes=[(2750,0xe0,bytes(items)),(2750,0x318,bytes([8])),(2750,0x600,bytes(768))])
        run(md,2960,target,{2960},PRESSES[:8]+route,ram_writes=[(2750,symbols['hero_items'],bytes(items)),(2750,symbols['hero_health'],(8).to_bytes(2,'big')),(2750,symbols['world_actor_state'],bytes(768))])
        sms=(source/'ram_02960.bin').read_bytes();raw=(target/'ram_02960.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
        expected={'hero_health':24,'hero_magic':0 if kind==7 else 24,'hero_selected_item':7 if kind==7 else 0}
        for name,address in [('hero_health',0x318),('hero_magic',0xdb),('hero_selected_item',0xdf)]:
            off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address]==expected[name],('route result',kind,name,actual,sms[address],expected[name])
        assert data[symbols['hero_items']+kind]==sms[0xe0+kind]==(1 if kind==7 else 0)
        assert json.loads((target/'capture.json').read_text())['rom_sha256']==hashlib.sha256(md.read_bytes()).hexdigest()
        cases.append(dict(item=kind,menu_and_action_reached_by_normal_input=True,final=expected,initial_mutations='Ownership, HP, cleared enemies only; no selected index, clock, action state or post-action mutation'))
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=cases,source_and_native_final_states_exact=True,acquisition_scripts_ported=False,absolute_menu_timing_exact=False)
    (ROOT/'validation/healing_route_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
