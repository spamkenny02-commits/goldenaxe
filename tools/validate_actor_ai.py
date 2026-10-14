"""Isolated native behavior replay with a controlled initial RNG state."""
import hashlib,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from actor_ai_reference import behavior
from actor_tick_reference import common_tick
from extract_world import initial_room


def random_word(seed):
    seed ^= seed>>5
    seed ^= (seed<<9)&65535
    seed ^= seed>>7
    return seed&65535


def main():
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        match=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if match:symbols[match[2].split('.lto_priv.')[0]]=int(match[1],16)&65535
    source=ROOT/'validation/sms-vertical-check'
    rom=(ROOT/'input/original.sms').read_bytes()
    source_hash=hashlib.sha256(rom).hexdigest()
    assert json.loads((source/'capture.json').read_text())['rom_sha256']==source_hash
    initial=(source/'ram_03101.bin').read_bytes()[0x600:0x900]
    initial=initial[:0x30]+bytes(0x300-0x30) # Keep RNG independent of other actors.
    # Choose an initial SGDK state yielding the explicit Up decision. This
    # controls a component test; it does not reproduce the source R stream.
    seed=next(n for n in range(1,65536) if random_word(n)&3==0)
    target=ROOT/'validation/md-actor-ai-test'
    run(ROOT/'gaw-megadrive.bin',3160,target,set(range(3102,3161)),PRESSES,
        ram_writes=[(3102,symbols['world_actor_state'],initial),
                    (3102,symbols['randbase'],seed.to_bytes(2,'big'))])
    for frame in range(3102,3161):
        raw=(target/f'ram_{frame:05}.bin').read_bytes()
        ram=bytes(v for n in range(0,len(raw),2) for v in(raw[n+1],raw[n]))
        start=symbols['world_actor_state']
        actual=ram[start:start+0x30]
        expected=(source/f'ram_{frame:05}.bin').read_bytes()[0x600:0x630]
        assert actual[:0x1b]+actual[0x1d:]==expected[:0x1b]+expected[0x1d:], (frame,actual.hex(),expected.hex())
    # Exercise decision states, limits, walls and both movement sequences.
    tilemap=initial_room(rom,0xa4)[3][:0x500]
    writes=[];expectations=[]
    for batch in range(4):
        data=bytearray(0x300);expected=[];rng=[4+batch]
        def refresh():
            rng[0]=random_word(rng[0]);return rng[0]
        for slot in range(8):
            entity=bytearray(initial[:0x30]);entity[3]=0x28
            entity[0]=0x26+(slot%3);entity[1]=[2,4,6,8][slot%4]
            entity[8:10]=bytes.fromhex('2486');entity[11]=3 if entity[1]==2 else 0
            entity[12]=4 if entity[1]==2 else 2;entity[13]=32;entity[14]=0
            entity[0x20]=1 if slot==7 else 0
            entity[10]=(slot+batch)&3
            entity[0x11]=[16,152,88,88][batch]
            entity[0x13]=[16,232,120,136][batch]
            data[slot*0x30:(slot+1)*0x30]=entity
            behavior(rom,entity,tilemap,refresh);common_tick(entity)
            expected.append(entity)
        frame=3102+batch
        writes.extend([(frame,symbols['world_actor_state'],data),
                       (frame,symbols['randbase'],(4+batch).to_bytes(2,'big'))])
        expectations.append(expected)
    corner=ROOT/'validation/md-actor-ai-branches-test'
    run(ROOT/'gaw-megadrive.bin',3105,corner,set(range(3102,3106)),PRESSES,ram_writes=writes)
    for batch,expected in enumerate(expectations):
        raw=(corner/f'ram_{3102+batch:05}.bin').read_bytes()
        ram=bytes(v for n in range(0,len(raw),2) for v in(raw[n+1],raw[n]))
        for slot,entity in enumerate(expected):
            start=symbols['world_actor_state']+slot*0x30
            assert ram[start:start+0x30]==entity, ('decision case',batch,slot,ram[start:start+0x30].hex(),entity.hex())
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                source_sha256=source_hash,
                frames_checked=59,logic_bytes_per_frame=46,initial_sgdk_seed=seed,
                native_emergence_direction_and_walk_exact=True,
                source_state_injections=1,original_refresh_stream_reproduced=False,
                native_decision_cases=32,native_decision_cases_exact=True,
                spawn_and_damage_ported=False,
                scope='First type26 emergence and Up walk, initialized once in emulator with controlled RNG')
    (ROOT/'validation/actor_ai_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
