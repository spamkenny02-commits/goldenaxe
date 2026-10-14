"""Native ranged attack/projectile state test from ROM semantics."""
import hashlib,json,re
from actor_reference import ROOT,load_room_actors
from extract_world import initial_room
from shield_reference import present_collision_indices,reflect
from ranged_reference import step_actors,projectile
from actor_tick_reference import common_tick
from validate_actor_ai import random_word
from validate_actor_tick import PRESSES
from run_core import run


def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        match=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if match:symbols[match[2].split('.lto_priv.')[0]]=int(match[1],16)&65535
    records=bytearray(0x300)
    for slot in range(3):
        start=slot*0x30;entity=bytearray(0x30)
        entity[0]=0x20+slot;entity[1]=10;entity[2]=6;entity[3]=0x28
        entity[8:10]=bytes.fromhex('2e85');entity[10]=[0,3,2][slot]
        entity[12]=2;entity[13]=10;entity[0x11]=80+slot*16;entity[0x13]=120+slot*8
        records[start:start+0x30]=entity
    target=ROOT/'validation/md-ranged-test'
    run(ROOT/'gaw-megadrive.bin',3200,target,set(range(3102,3201)),PRESSES,ram_writes=[
        (3102,symbols['world_actor_state'],records),(3102,symbols['randbase'],(4).to_bytes(2,'big'))])
    def native(folder,frame):
        raw=(folder/f'ram_{frame:05}.bin').read_bytes()
        return bytes(v for n in range(0,len(raw),2) for v in(raw[n+1],raw[n]))
    _,_,cells,tilemap,_,_=initial_room(rom,0xa4)
    rng=[4];births=[];deaths=[]
    def refresh():rng[0]=random_word(rng[0]);return rng[0]
    for frame in range(3102,3201):
        data=native(target,frame)
        clock=int.from_bytes(data[symbols['vtimer']:symbols['vtimer']+4],'big')
        before=bytes(records)
        present_collision_indices(rom,records)
        reflect(rom,records,120,16,1,1,clock)
        step_actors(rom,records,tilemap,cells,120,16,clock,refresh)
        start=symbols['world_actor_state'];actual=data[start:start+0x300]
        for slot in range(16):
            offset=slot*0x30
            assert actual[offset:offset+0x1b]+actual[offset+0x1d:offset+0x30]==records[offset:offset+0x1b]+records[offset+0x1d:offset+0x30], ('ranged/projectile',frame,slot)
            if slot>=8:
                if not before[offset] and records[offset]:births.append((frame,slot,records[offset]))
                if before[offset] and not records[offset]:deaths.append((frame,slot,before[offset]))
        assert int.from_bytes(data[symbols['randbase']:symbols['randbase']+2],'big')==rng[0]
    assert {event[2] for event in births}=={0x10,0x11,0x12}
    assert {event[2] for event in deaths}=={0x10,0x11,0x12}
    # A full projectile pool still advances the shooter's recovery state.
    full=bytearray(0x300);full[:0x30]=before[:0x30]
    full[1]=10;full[4]=0
    for slot in range(8,16):
        off=slot*0x30;full[off]=0x10;full[off+1]=2;full[off+4]=128
        full[off+0x11]=80;full[off+0x13]=120
    expected=bytearray(full)
    step_actors(rom,expected,tilemap,cells,120,16,0,lambda:0)
    corner=ROOT/'validation/md-ranged-full-pool-test'
    run(ROOT/'gaw-megadrive.bin',3102,corner,{3102},PRESSES,
        ram_writes=[(3102,symbols['world_actor_state'],full)])
    data=native(corner,3102);start=symbols['world_actor_state']
    for slot in range(16):
        off=slot*0x30
        assert data[start+off:start+off+0x1b]+data[start+off+0x1d:start+off+0x30]==expected[off:off+0x1b]+expected[off+0x1d:off+0x30]
    observed=ROOT/'validation/sms-ranged-observe'
    source_meta=json.loads((observed/'capture.json').read_text())
    assert source_meta['rom_sha256']==hashlib.sha256(rom).hexdigest()
    source_entity=bytearray((observed/'ram_03680.bin').read_bytes()[0x780:0x7b0])
    for frame in range(3690,3741,10):
        for _ in range(10):projectile(rom,source_entity);common_tick(source_entity)
        assert source_entity==(observed/f'ram_{frame:05}.bin').read_bytes()[0x780:0x7b0], ('observed SMS projectile',frame)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(rom).hexdigest(),frames_checked=99,
                entity_steps_checked=99*16,projectile_births=births,projectile_deaths=deaths,
                native_ranged_and_projectile_logic_exact=True,full_pool_recovery_exact=True,
                observed_sms_projectile_steps_exact=60,observed_sms_entity_bytes_exact=48,
                complete_combat_ported=False,normal_ground_hero_damage_ported=True,source_sprite_overflow_suppression_ported=False,
                dungeon_projectile_bounds_ported=False,
                scope='Isolated state fixtures, all three projectile types, controlled SGDK RNG; ROM-semantic reference')
    (ROOT/'validation/ranged_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
