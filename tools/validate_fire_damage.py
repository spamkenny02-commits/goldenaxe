"""Fire projectile: collision parity, damage, direction and lethal conversion."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_damage import FIELDS

def main():
    rom=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    images_exact=0;images_with_uncontrolled_loot=0
    baseline=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();results=[]
    for level,hp,defense in ((1,12,0),(2,12,3),(1,4,0)):
        mode=0
        for direction in range(4):
            label=f'{level}-{hp}-{defense}-{direction}';entity=bytearray(baseline[0x600:0x630]);entity[4]=128;entity[5]=entity[6]=entity[11]=entity[14]=0;entity[0x18]=hp;entity[0x1a]=defense;entity[0x20]=mode;entity[0x1d]=0;entity[0x1e:0x20]=bytes(2);entity[0x10:0x18]=bytes(8)
            entity[0x13]=136+(-24 if direction==2 else 24 if direction==3 else 0);entity[0x11]=112+(-24 if direction==0 else 24 if direction==1 else 0)
            actors=bytes(entity)+bytes(720);source=ROOT/f'validation/sms-fire-hit-{label}';target=ROOT/f'validation/md-fire-hit-{label}'
            items=bytearray(17);items[0]=1;items[4]=level
            source_writes=[(3741,0xdf,b'\x04'),(3741,0xe0,bytes(items)),(3741,0x600,actors),(3741,0x30a,bytes([direction])),(3741,0x310,(0x7000).to_bytes(2,'little')+(0x8800).to_bytes(2,'little'))]
            target_writes=[(3741,symbols['hero_selected_item'],(4).to_bytes(2,'big')),(3741,symbols['hero_items'],bytes(items)),(3741,symbols['world_actor_state'],actors),(3741,symbols['hero_direction'],direction.to_bytes(2,'big')),(3741,symbols['hero_x'],(0x8800).to_bytes(2,'big')),(3741,symbols['hero_y'],(0x7000).to_bytes(2,'big')),(3741,symbols['vtimer'],int(baseline[0x2f]).to_bytes(4,'big'))]
            points=set(range(3740,3781));inputs=PRESSES+[(3748,3755,8)]
            run(rom,3780,source,points,[(200,220,0)]+inputs,ram_writes=source_writes)
            run(md,3780,target,points,inputs,ram_writes=target_writes)
            first_hit=None;steps=0;divergences=[];loot_divergences=[];loot_image_differences=[]
            for frame in range(3741,3781):
                sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]));offset=symbols['world_actor_state']
                beyond_contract=first_hit is not None and (mode==2 and frame>first_hit+1)
                if beyond_contract:
                    a=sms[0x600:0x900];b=data[offset:offset+768]
                    if a!=b:divergences.append((frame,[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y][:12]))
                    continue # Preserve later clone/RNG differences in the report.
                for name,(address,size) in FIELDS.items():
                    off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');expected=int.from_bytes(sms[address:address+size],'little')
                    assert actual==expected,('hero field',label,frame,name,actual,expected)
                spell_offset=symbols['world_spell_state'];assert sms[0x330:0x360]==data[spell_offset:spell_offset+48],('spell record',label,frame,[(i,a,b) for i,(a,b) in enumerate(zip(sms[0x330:0x360],data[spell_offset:spell_offset+48])) if a!=b])
                a=sms[0x600:0x900];b=data[offset:offset+768]
                assert a==b,('enemy bytes',label,frame,[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y][:12])
                loot_off=symbols['world_loot_state'];loot_same=sms[0x4b0:0x600]==data[loot_off:loot_off+336]
                if not loot_same:
                    loot_divergences.append(dict(frame=frame,differences=[(i,x,y) for i,(x,y) in enumerate(zip(sms[0x4b0:0x600],data[loot_off:loot_off+336])) if x!=y]))
                if frame>=3745:
                    image=Image.open(source/f'frame_{frame:05}.png').convert('RGB');native=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(image.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(native.getdata())};diff=sum(x!=conv[y] for x,y in zip(image.getdata(),native.getdata()))
                    if loot_same:
                        assert diff==0,('fire damage pixels',label,frame,diff);images_exact+=1
                    else:
                        images_with_uncontrolled_loot+=1;loot_image_differences.append(dict(frame=frame,pixels=diff))
                steps+=1
                if a[0x18]<hp and first_hit is None:first_hit=frame
            assert first_hit,('no hit',label)
            results.append(dict(level=level,mode=mode,initial_hp=hp,defense=defense,direction=direction,first_hit=first_hit,steps_exact=steps,post_death_particles_and_loot_verified=False,subsequent_actor_divergences=divergences,uncontrolled_loot_divergences=loot_divergences,uncontrolled_loot_image_differences=loot_image_differences))
    report=dict(source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),cases=results,normalized_images_exact=images_exact,images_with_uncontrolled_loot=images_with_uncontrolled_loot,scope='Fire projectile: HP, minimum damage, hurt interval, terrain knockback, paired clones and first lethal conversion',loot_records_verified_by_this_test=False,death_particle_actor_states_verified=True,original_random_stream_reproduced=False,fire_sound_effect_ported=False)
    (ROOT/'validation/fire_damage_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
