"""Native hero damage, knockback and blinking compared to controlled SMS runs."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from shield_reference import hero_collision

FIELDS={'hero_x':(0x312,2),'hero_y':(0x310,2),'hero_direction':(0x30a,1),
        'hero_animation':(0x30b,1),'hero_counter':(0x304,1),'hero_hurt':(0x305,1),
        'hero_state':(0x301,1),'hero_flags':(0x303,1),'hero_health':(0x318,1),
        'hero_dx':(0x316,2),'hero_dy':(0x314,2),'hero_defense':(0x31a,1)}


def main():
    rom=(ROOT/'input/original.sms').read_bytes();md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    baseline=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes()
    projectile=baseline[0x780:0x7b0]
    def native(folder,frame,name='ram'):
        raw=(folder/f'{name}_{frame:05}.bin').read_bytes()
        return bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
    def compare(source,target,frame):
        sms=(source/f'ram_{frame:05}.bin').read_bytes();data=native(target,frame)
        for name,(offset,size) in FIELDS.items():
            a=int.from_bytes(data[symbols[name]:symbols[name]+2],'big')
            b=int.from_bytes(sms[offset:offset+size],'little')
            assert a==b,(frame,name,a,b)
        off=symbols['world_actor_state']
        assert data[off:off+0x300]==sms[0x600:0x900],('actor records',frame)
    def fixture(frame,case):
        x=case.get('x',120);y=case.get('y',80);direction=case.get('direction',1)
        hero=dict(hero_x=x<<8,hero_y=y<<8,hero_direction=direction,hero_animation=0,
                  hero_counter=case.get('counter',0),hero_dx=case.get('dx',0),hero_dy=0,
                  hero_hurt=case.get('hurt',0),hero_state=1,hero_flags=3,hero_health=case.get('hp',24),
                  hero_defense=case.get('defense',(case.get('shield',1)-1)*2+(case.get('armor',1)-1)*4))
        records=bytearray(0x300);e=bytearray(projectile)
        e[0x10:0x14]=bytes((0,case.get('target_y',y-8),0,case.get('target_x',x)))
        e[10]=case.get('target_direction',0);e[0x19]=case.get('attack',9);e[3]=case.get('flags',0x13)
        e[0x14:0x18]=bytes(4);axis=0x14 if e[10]<2 else 0x16
        e[axis:axis+2]=(-384&65535).to_bytes(2,'little');records[0x180:0x1b0]=e
        source_writes=[(frame,0x600,bytes(records)),(frame,0x31b,bytes((hero_collision(rom,direction),)))]
        target_writes=[(frame,symbols['world_actor_state'],bytes(records))]
        for name,value in hero.items():
            off,size=FIELDS[name]
            source_writes.append((frame,off,(value&((1<<(size*8))-1)).to_bytes(size,'little')))
            target_writes.append((frame,symbols[name],(value&65535).to_bytes(2,'big')))
        for name,off,value in [('hero_shield_level',0xf2,case.get('shield',1)),('hero_armor_level',0xf1,case.get('armor',1))]:
            source_writes.append((frame,off,bytes((value,))))
            target_writes.append((frame,symbols[name],value.to_bytes(2,'big')))
        tilemap=bytearray(baseline[0x1600:0x1c00])
        if case.get('wall'):
            offset=((y-12)&248)*8+(((x-12)>>2)&62)
            cache_index=case['wall']-1
            tilemap[offset+(cache_index//4)*64+(cache_index%4)*2+1]|=128
        source_writes.append((frame,0x1600,bytes(tilemap)))
        target_writes.append((frame,symbols['sms_vram']+0x3800,bytes(tilemap)))
        return source_writes,target_writes
    source=ROOT/'validation/sms-damage-detail';target=ROOT/'validation/md-damage-detail'
    sw,tw=fixture(3741,{})
    tw.append((3741,symbols['vtimer'],(167).to_bytes(4,'big')))
    run(ROOT/'input/original.sms',3800,source,set(range(3741,3801)),[(200,220,0)]+PRESSES,ram_writes=sw)
    run(md,3800,target,set(range(3741,3801)),PRESSES,ram_writes=tw)
    image_frames=[]
    for frame in range(3741,3801):
        compare(source,target,frame)
        sms_vram=(source/f'vram_{frame:05}.bin').read_bytes();vram=native(target,frame,'vram')
        regs=(target/f'vdp_regs_{frame:05}.bin').read_bytes();base=(regs[2]&0x38)<<10
        for n in range(3):
            low,high=sms_vram[0x3d5e+n*2:0x3d60+n*2]
            word=(high<<8)|low
            expected=((word>>11)&1)<<13|((word>>12)&1)<<15|((word>>10)&1)<<12|((word>>9)&1)<<11|16+(word&511)
            address=base+(23*64+15+n)*2
            assert int.from_bytes(vram[address:address+2],'big')==expected,('life HUD',frame,n)
        if frame>=3743:
            a=Image.open(source/f'frame_{frame:05}.png').convert('RGB')
            b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208))
            palette=set(a.getdata());conversion={v:min(palette,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
            assert all(x==conversion[y] for x,y in zip(a.getdata(),b.getdata())),('damage image',frame)
            image_frames.append(frame)
    cases=[dict(name='down'),dict(name='up',target_y=83,direction=2),
           dict(name='left',target_x=128,target_direction=2),dict(name='right',target_x=116,target_direction=2),
           dict(name='upper-boundary',y=16,target_y=20,direction=2),
           dict(name='lower-boundary',y=160,target_y=152),
           dict(name='left-boundary',x=16,target_x=20,target_direction=2),
           dict(name='right-boundary',x=240,target_x=236,target_direction=2),
           dict(name='wall-up',target_y=83,direction=2,wall=2),
           dict(name='wall-down',wall=10),
           dict(name='wall-left',target_x=128,target_direction=2,wall=5),
           dict(name='wall-right',target_x=116,target_direction=2,wall=8),
           dict(name='already-hurt',hurt=6),dict(name='armored',shield=2,armor=2,direction=2),
           dict(name='defense-exceeds-attack',shield=3,armor=3,direction=2),
           dict(name='one-damage',attack=7,shield=2,armor=2,direction=2),
           dict(name='zero-attack',attack=0,direction=2),dict(name='health-clamps-zero',hp=1),
           dict(name='hit-during-walk',counter=2,dx=410),
           dict(name='equipment-changed-this-frame',shield=2,armor=2,direction=2,defense=0),
           dict(name='contact-without-projectile-flag',flags=3)]
    sw=[];tw=[];frames=set()
    for number,case in enumerate(cases):
        frame=3741+number*2;frames.add(frame);a,b=fixture(frame,case);sw.extend(a);tw.extend(b)
    source_cases=ROOT/'validation/sms-damage-cases';target_cases=ROOT/'validation/md-damage-cases'
    run(ROOT/'input/original.sms',max(frames),source_cases,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
    run(md,max(frames),target_cases,frames,PRESSES,ram_writes=tw)
    for frame in sorted(frames):compare(source_cases,target_cases,frame)
    images=[]
    for frame in range(3743,3791,2):
        image=Image.new('RGB',(512,224),(0,0,0))
        image.paste(Image.open(source/f'frame_{frame:05}.png'),(0,16))
        image.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0))
        images.append(image.resize((1024,448),Image.Resampling.NEAREST))
    images[0].save(ROOT/'validation/damage_sms_vs_md.gif',save_all=True,append_images=images[1:],duration=33,loop=0)
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),
                continuous_steps_checked=60,hero_fields_checked=list(FIELDS),actor_bytes_per_frame=768,
                normalized_images_exact=len(image_frames),hud_frames_exact=60,source_edge_cases_exact=cases,
                scope='Controlled initial hero/projectile states in both emulators; surviving normal-ground hurt branch',
                death_animation_and_menu_ported=True,complete_death_and_respawn_timing_exact=False,enemy_damage_from_hero_attacks_ported=False,
                other_terrain_damage_ported=False,sound_ported=False)
    (ROOT/'validation/damage_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
