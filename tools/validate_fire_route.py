"""Normal menu input reaches fire usage; only initial possession/stats injected."""
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
    for kind in [4]:
        route=[(2800,2805,0),(2825,2827,5)]
        route +=[(2830,2833,8),(2845,2850,0),(2890,2895,8),(2920,2925,8),(2950,2955,8),(2980,2985,8)]
        source=ROOT/f'validation/sms-fire-route-{kind}';target=ROOT/f'validation/md-fire-route-{kind}';items=bytearray(17);items[0]=items[kind]=1
        run(rom,3010,source,set(range(2885,3011)),[(200,220,0)]+PRESSES[:8]+route,ram_writes=[(2750,0xe0,bytes(items)),(2750,0x318,bytes([8])),(2750,0x600,bytes(768))])
        run(md,3010,target,set(range(2885,3011)),PRESSES[:8]+route,ram_writes=[(2750,symbols['hero_items'],bytes(items)),(2750,symbols['hero_health'],(8).to_bytes(2,'big')),(2750,symbols['world_actor_state'],bytes(768))])
        sms=(source/'ram_03010.bin').read_bytes();raw=(target/'ram_03010.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
        expected={'hero_health':8,'hero_magic':16,'hero_selected_item':4,'hero_fire_charge':0}
        for name,address in [('hero_health',0x318),('hero_magic',0xdb),('hero_selected_item',0xdf),('hero_fire_charge',0xc6)]:
            off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address]==expected[name],('route result',kind,name,actual,sms[address],expected[name])
        assert data[symbols['hero_items']+kind]==sms[0xe0+kind]==1
        assert json.loads((target/'capture.json').read_text())['rom_sha256']==hashlib.sha256(md.read_bytes()).hexdigest()
        for directory,native in [(source,False),(target,True)]:
            active=False;shots=0
            for frame in range(2885,3011):
                raw=(directory/f'ram_{frame:05}.bin').read_bytes()
                if native:
                    ram=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]));present=ram[symbols['world_spell_state']]==3
                else:present=raw[0x330]==3
                if present and not active:shots+=1
                active=present
            assert shots==4,('fire route shots',native,shots)
        cases.append(dict(item=kind,menu_and_action_reached_by_normal_input=True,final=expected,initial_mutations='Ownership, HP, cleared enemies only; no selected index, clock, action state or post-action mutation'))
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=cases,source_and_native_final_states_exact=True,acquisition_scripts_ported=False,absolute_menu_timing_exact=False)
    (ROOT/'validation/fire_route_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
