"""Successful native shield reflection: source trace and isolated edge cases."""
import hashlib,json,re
from actor_reference import ROOT
from actor_tick_reference import common_tick
from ranged_reference import projectile
from shield_reference import reflect,present_collision_indices,hero_collision
from run_core import run
from validate_actor_tick import PRESSES


def main():
    rom=(ROOT/'input/original.sms').read_bytes();md=ROOT/'gaw-megadrive.bin'
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    def native(folder,frame):
        raw=(folder/f'ram_{frame:05}.bin').read_bytes()
        return bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
    source=ROOT/'validation/sms-shield-detail'
    run(ROOT/'input/original.sms',3760,source,set(range(3740,3761)),[(200,220,0)]+PRESSES)
    assert json.loads((source/'capture.json').read_text())['rom_sha256']==hashlib.sha256(rom).hexdigest()
    source_ram=(source/'ram_03740.bin').read_bytes()
    initial=source_ram[0x780:0x7b0];records=bytearray(0x300)
    records[0x180:0x1b0]=initial
    target=ROOT/'validation/md-shield-detail'
    run(md,3760,target,set(range(3741,3761)),PRESSES,ram_writes=[
        (3741,symbols['world_actor_state'],records),
        (3741,symbols['vtimer'],source_ram[0x2f].to_bytes(4,'big'))])
    flips=[]
    for frame in range(3741,3761):
        sms=(source/f'ram_{frame:05}.bin').read_bytes()
        actual=native(target,frame);off=symbols['world_actor_state']+0x180
        assert actual[off:off+48]==sms[0x780:0x7b0],('SMS/native shield',frame)
        # Independent ROM-semantic replay, including descriptor collision fields.
        present_collision_indices(rom,records)
        hit=reflect(rom,records,sms[0x313],sms[0x311],sms[0x30a],sms[0xf2],sms[0x2f],sms[0x30b])
        if hit is not None:flips.append(frame)
        e=bytearray(records[0x180:0x1b0])
        if e[0]:projectile(rom,e);common_tick(e)
        records[0x180:0x1b0]=e
        assert e==sms[0x780:0x7b0],('shield reference',frame)
    assert flips==[3745]
    # Fresh states in one controlled run; each case resets hero and projectile.
    cases=[]
    for direction in range(4):
        cases.extend([dict(name=f'direction-{direction}-incoming',direction=direction,expected=True),
                      dict(name=f'direction-{direction}-departing',direction=direction,reverse=True,expected=False)])
    cases.extend([dict(name='weak-shield',attack=9,expected=False),
                  dict(name='equal-strength',attack=8,expected=True),
                  dict(name='strong-shield',attack=12,shield=2,expected=True),
                  dict(name='too-strong',attack=15,shield=3,expected=False),
                  dict(name='odd-frame',clock=171,expected=False),
                  dict(name='zero-velocity',zero=True,expected=False),
                  dict(name='delayed-projectile',delay=1,expected=False),
                  dict(name='collision-disabled',flags=0x11,expected=False),
                  dict(name='outside-box',outside=True,expected=False),
                  dict(name='earlier-contact-blocks-later',earlier=True,expected=False)])
    writes=[];expected=[];case_frames=[]
    for number,case in enumerate(cases):
        frame=3103+number*2+(1 if case.get('clock',170)&1 else 0);case_frames.append(frame)
        direction=case.get('direction',1);shield=case.get('shield',1);clock=frame-25
        index=hero_collision(rom,direction);box=rom[0x8100+index*4:0x8104+index*4]
        x=((120+box[0])&255)+3;y=((80+box[2])&255)+7
        e=bytearray(initial);e[0x10:0x14]=bytes((0,y,0,x));e[3]=case.get('flags',0x13)
        e[6]=case.get('delay',0);e[0x19]=case.get('attack',8)
        e[0x14:0x18]=bytes(4);axis=0x14 if direction<2 else 0x16
        velocity=384 if direction in (0,2) else -384
        if case.get('reverse'):velocity=-velocity
        if case.get('zero'):velocity=0
        e[axis:axis+2]=(velocity&65535).to_bytes(2,'little')
        if case.get('outside'):e[0x13]=220
        r=bytearray(0x300);r[0x180:0x1b0]=e
        if case.get('earlier'):
            first=bytearray(e);first[0x19]=9;r[0x150:0x180]=first
        for name,value,size in [('hero_x',120<<8,2),('hero_y',80<<8,2),('hero_direction',direction,2),
                                ('hero_animation',0,2),('hero_counter',0,2),('hero_pending',0,2),
                                ('hero_health',24,2),('hero_hurt',0,2),('hero_flags',3,2),('hero_state',1,2),
                                ('hero_dx',0,2),('hero_dy',0,2),('hero_shield_level',shield,2)]:
            writes.append((frame,symbols[name],value.to_bytes(size,'big')))
        writes.append((frame,symbols['world_actor_state'],bytes(r)))
        present_collision_indices(rom,r);hit=reflect(rom,r,120,80,direction,shield,clock)
        assert (hit is not None)==case['expected'],case
        if hit is None:
            for slot in range(16):
                off=slot*48
                if r[off+3]&4 and r[off+3]&16:
                    r[off:off+48]=bytes(48);break
        for slot in range(16):
            off=slot*48;e=bytearray(r[off:off+48])
            if e[0]:
                if not e[6]:projectile(rom,e)
                common_tick(e);r[off:off+48]=e
        expected.append(r)
    corner=ROOT/'validation/md-shield-cases'
    run(md,max(case_frames),corner,set(case_frames),PRESSES,ram_writes=writes)
    for number,r in enumerate(expected):
        actual=native(corner,case_frames[number]);off=symbols['world_actor_state']
        assert actual[off:off+0x300]==r,('native shield edge case',cases[number],[(i,a,b) for i,(a,b) in enumerate(zip(actual[off:off+0x300],r)) if a!=b])
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),
                source_frames_checked=20,source_projectile_bytes_per_frame=48,source_reflection_frame=3745,
                controlled_native_reflection_and_expiry_exact=True,edge_cases_checked=cases,
                damage_and_knockback_ported=True,water_and_other_hero_states_ported=False,
                shield_inventory_progression_ported=False,sound_ported=False,
                scope='Successful shield branch; controlled entity and clock, no complete combat or natural timing equivalence claimed')
    (ROOT/'validation/shield_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
