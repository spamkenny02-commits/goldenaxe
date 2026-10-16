"""Native shared counters, with one initial injection followed by free evolution."""
import hashlib,json,re
from actor_reference import ROOT
from actor_tick_reference import common_tick,emergence_reference
from run_core import run

PRESSES=[(920,935,0),(1050,1065,0),(1200,1204,8),(1280,1340,5),
         (1360,1420,7),(1450,1460,8),(2200,2210,8),(2400,2410,8),
         (2600,2649,6),(2700,2714,4),(2750,2900,6),(3000,3060,5)]


def main():
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        match=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if match:symbols[match[2].split('.lto_priv.')[0]]=int(match[1],16)&65535
    address=symbols['world_actor_state']
    source=ROOT/'validation/sms-vertical-check'
    source_hash=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest()
    assert json.loads((source/'capture.json').read_text())['rom_sha256']==source_hash
    initial=(source/'ram_03101.bin').read_bytes()[0x600:0x900]
    initial=initial[:0x30]+bytes(0x300-0x30) # Isolate one actor from other spawns.
    target=ROOT/'validation/md-actor-tick-test'
    run(ROOT/'gaw-megadrive.bin',3148,target,set(range(3102,3149)),PRESSES,
        ram_writes=[(3102,address,initial)])
    def native_entity(folder,frame,slot=0):
        raw=(folder/f'ram_{frame:05}.bin').read_bytes()
        ram=bytes(v for n in range(0,len(raw),2) for v in(raw[n+1],raw[n]))
        start=address+slot*0x30
        return ram[start:start+0x30]
    for frame in range(3102,3149):
        expected=(source/f'ram_{frame:05}.bin').read_bytes()[0x600:0x630]
        actual=native_entity(target,frame)
        # Collision indices are committed by the separately tested renderer.
        assert actual[:0x1b]+actual[0x1d:]==expected[:0x1b]+expected[0x1d:], (frame,actual.hex(),expected.hex())
    fixture=bytearray(0x300)
    cases=[(0,0,0,16),(1,1,0,16),(2,2,0,0),(128,3,0,16),
           (129,128,0,16),(255,129,0,16),(2,3,3,16),(1,0,0,1)]
    expected_cases=[]
    for slot,(movement,hurt,delay,period) in enumerate(cases):
        entity=bytearray(initial[:0x30])
        entity[3]=0x28;entity[4]=movement;entity[5]=hurt;entity[6]=delay
        entity[11]=1;entity[13]=period;entity[14]=0
        entity[0x10:0x18]=bytes.fromhex('01900388'+'67fe9a01')
        fixture[slot*0x30:(slot+1)*0x30]=entity
        common_tick(entity);expected_cases.append(entity)
    corner=ROOT/'validation/md-actor-counter-test'
    run(ROOT/'gaw-megadrive.bin',3102,corner,{3102},PRESSES,
        ram_writes=[(3102,address,fixture)])
    for slot,expected in enumerate(expected_cases):
        actual=native_entity(corner,3102,slot)
        assert actual==expected, ('counter corner case',slot,actual.hex(),expected.hex())
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                source_sha256=source_hash,
                emergence_frames=emergence_reference(),source_logic_bytes_per_frame=46,
                native_emergence_logic_exact=True,source_injections=1,
                counter_corner_cases=len(cases),counter_corner_cases_exact=True,
                includes_movement_fraction_reset=True,includes_delay_and_hurt_blink=True,
                actor_behavior_states_ported=[2,4,6,8],actor_behavior_complete=False,
                scope='Common counters only; initial states injected in emulator, spawning/original random/combat dispatch pending')
    (ROOT/'validation/actor_tick_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
