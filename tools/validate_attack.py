"""Native attack trigger, pose streams, graphics and base contact against SMS."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_damage import FIELDS

def main():
    source_rom=ROOT/'input/original.sms';md_rom=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    baseline=(ROOT/'validation/sms-world/ram_02800.bin').read_bytes();initial_clock=baseline[0x2f]
    cases=[];fields=dict(FIELDS,hero_attack_phase=(0x30e,1),hero_attack=(0x319,1));images=0
    def native(folder,frame):
        raw=(folder/f'ram_{frame:05}.bin').read_bytes();return bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
    boot=PRESSES[:8];frames=set(range(2800,2835))
    for item,level,speed in ((0,1,0),(0,1,1),(1,1,0),(1,2,1)):
        for direction in range(4):
            label=f'{item}-{level}-{speed}-{direction}';source=ROOT/f'validation/sms-attack-{label}';target=ROOT/f'validation/md-attack-{label}'
            presses=boot+[(2801,2816,8)]
            sw=[(2801,0x600,bytes(768)),(2801,0x30a,bytes([direction])),(2801,0xdf,bytes([item])),(2801,0xe0+(item==1),bytes([level])),(2801,0xee,bytes([speed]))]
            tw=[(2801,symbols['world_actor_state'],bytes(768)),(2801,symbols['hero_direction'],direction.to_bytes(2,'big')),(2801,symbols['hero_selected_item'],item.to_bytes(2,'big')),(2801,symbols['hero_weapon_level' if item else 'hero_basic_level'],level.to_bytes(2,'big')),(2801,symbols['hero_attack_speed'],speed.to_bytes(2,'big')),(2801,symbols['vtimer'],int(initial_clock).to_bytes(4,'big'))]
            run(source_rom,2834,source,frames,[(200,220,0)]+presses,ram_writes=sw)
            run(md_rom,2834,target,frames,presses,ram_writes=tw)
            for frame in range(2801,2835):
                sms=(source/f'ram_{frame:05}.bin').read_bytes();data=native(target,frame)
                for name,(offset,size) in fields.items():
                    off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');expected=int.from_bytes(sms[offset:offset+size],'little')
                    assert actual==expected,('attack field',label,frame,name,actual,expected)
                if frame>=2803:
                    a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conversion={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
                    diff=sum(x!=conversion[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('attack image',label,frame,diff);images+=1
            cases.append(dict(item=item,level=level,speed_flag=speed,direction=direction,steps=34))
    report=dict(md_sha256=hashlib.sha256(md_rom.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source_rom.read_bytes()).hexdigest(),cases=cases,fields=list(fields),normalized_images_exact=images,scope='Primary/secondary attacks, four directions, two speed sequences and weapon variants; controlled initial equipment/clock',enemy_damage_verified=False,inventory_selection_ported=False,sound_ported=False)
    (ROOT/'validation/attack_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
