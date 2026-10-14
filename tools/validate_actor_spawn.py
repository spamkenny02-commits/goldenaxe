"""Uninjected native spawning/AI replay, using the port's actual RNG input."""
import hashlib,json,re
from actor_reference import ROOT
from actor_ai_reference import behavior
from actor_tick_reference import common_tick
from extract_world import initial_room
from validate_actor_ai import random_word
from run_core import run
from validate_actor_tick import PRESSES
from shield_reference import present_collision_indices,reflect
from ranged_reference import step_actors


def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    target=ROOT/'validation/md-vertical'
    capture=json.loads((target/'capture.json').read_text())
    md_hash=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    assert capture['rom_sha256']==md_hash and not capture.get('test_ram_writes')
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        match=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if match:symbols[match[2].split('.lto_priv.')[0]]=int(match[1],16)&65535
    def ram(frame):
        raw=(target/f'ram_{frame:05}.bin').read_bytes()
        return bytes(v for n in range(0,len(raw),2) for v in(raw[n+1],raw[n]))
    def word(data,name):
        start=symbols[name];return int.from_bytes(data[start:start+2],'big')
    _,_,cells,tilemap,_,_=initial_room(rom,0xa4)
    previous=ram(3071);events=[];compared=0
    for frame in range(3072,3161):
        current=ram(frame);clock=int.from_bytes(current[symbols['vtimer']:symbols['vtimer']+4],'big')
        rng=[word(previous,'randbase')]
        def refresh():
            rng[0]=random_word(rng[0]);return rng[0]
        records=bytearray(previous[symbols['world_actor_state']:symbols['world_actor_state']+0x300])
        present_collision_indices(rom,records)
        reflect(rom,records,word(previous,'hero_x')>>8,word(previous,'hero_y')>>8,
                word(previous,'hero_direction'),word(previous,'hero_shield_level'),clock,
                word(previous,'hero_animation'))
        step_actors(rom,records,tilemap,cells,word(current,'hero_x')>>8,
                    word(current,'hero_y')>>8,clock,refresh)
        for slot in range(16):
            start=symbols['world_actor_state']+slot*0x30
            before=previous[start+1]
            entity=records[slot*0x30:(slot+1)*0x30]
            actual=current[start:start+0x30]
            assert entity[:0x1b]+entity[0x1d:]==actual[:0x1b]+actual[0x1d:], ('native spawn/AI',frame,slot,entity.hex(),actual.hex())
            if before==0 and entity[1]==2 and entity[0]>=0x20:
                cell=((entity[0x11]-16)&240)|(entity[0x13]>>4)
                assert cells[cell] in rom[0x586d:0x5871]
                assert abs((word(current,'hero_x')>>8)-entity[0x13])>=16
                assert abs((word(current,'hero_y')>>8)-entity[0x11])>=16
                events.append(dict(frame=frame,slot=slot,x=entity[0x13],y=entity[0x11],terrain=cells[cell]))
            compared+=1
        assert word(current,'randbase')==rng[0], ('RNG consumption',frame)
        previous=current
    assert len(events)==5 and len({e['slot'] for e in events})==5
    final=ram(3160);start=symbols['world_actor_state']
    assert all(final[start+slot*0x30+3]&1 and final[start+slot*0x30+1] in (4,6,8,10,12) for slot in range(5))
    # Compare the accepted placement against an actual source state, with
    # controlled equivalent random bits and slot eligibility in a test run.
    seed=next(n for n in range(1,65536)
              if random_word(n)&127==0x78 and random_word(random_word(n))&3==2)
    source=ROOT/'validation/sms-vertical-check'
    initial=(source/'ram_03097.bin').read_bytes()[0x600:0x630]+bytes(0x300-0x30)
    controlled=ROOT/'validation/md-actor-spawn-test'
    run(ROOT/'gaw-megadrive.bin',3102,controlled,{3102},PRESSES,ram_writes=[
        (3102,symbols['world_actor_state'],initial),
        (3102,symbols['randbase'],seed.to_bytes(2,'big')),
        (3102,symbols['vtimer'],(7).to_bytes(4,'big'))])
    raw=(controlled/'ram_03102.bin').read_bytes()
    data=bytes(v for n in range(0,len(raw),2) for v in(raw[n+1],raw[n]))
    start=symbols['world_actor_state']
    source_spawn=(source/'ram_03101.bin').read_bytes()[0x600:0x630]
    assert data[start:start+0x30]==source_spawn, 'Controlled native placement vs source'
    report=dict(md_sha256=md_hash,source_sha256=hashlib.sha256(rom).hexdigest(),
                normal_run_without_injection=True,frames_checked=89,
                entity_steps_checked=compared,spawn_events=events,
                all_five_room_actors_active_and_moving=True,
                native_spawn_and_ai_contract_exact=True,
                controlled_spawn_48_source_bytes_exact=True,
                original_refresh_stream_reproduced=False,combat_ported=False,
                scope='ROM placement/AI rules, with actual SGDK RNG and native frame clock; no source timing equivalence claimed')
    (ROOT/'validation/actor_spawn_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
