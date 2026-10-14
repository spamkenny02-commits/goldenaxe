"""Attack during a walk, held action, mixed directions and a second fresh action."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_damage import FIELDS

def main():
    sms_rom=ROOT/'input/original.sms';md_rom=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    source=ROOT/'validation/sms-attack-motion';target=ROOT/'validation/md-attack-motion'
    points=set(range(2800,2871));inputs=PRESSES[:8]+[(2801,2850,4),(2803,2840,8),(2810,2814,7),(2855,2858,8)]
    baseline=(ROOT/'validation/sms-world/ram_02800.bin').read_bytes()
    run(sms_rom,2870,source,points,[(200,220,0)]+inputs,ram_writes=[(2801,0x600,bytes(768))])
    run(md_rom,2870,target,points,inputs,ram_writes=[(2801,symbols['world_actor_state'],bytes(768)),(2801,symbols['vtimer'],int(baseline[0x2f]).to_bytes(4,'big'))])
    fields=dict(FIELDS,hero_attack_phase=(0x30e,1),hero_attack=(0x319,1));images=0;preview=[]
    for frame in range(2801,2871):
        sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
        for name,(offset,size) in fields.items():
            off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');expected=int.from_bytes(sms[offset:offset+size],'little');assert actual==expected,('moving attack',frame,name,actual,expected)
        a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conversion={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};differences=sum(x!=conversion[y] for x,y in zip(a.getdata(),b.getdata()));assert differences==0,('moving attack image',frame,differences);images+=1
        picture=Image.new('RGB',(512,224));picture.paste(a,(0,16));picture.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0));preview.append(picture.resize((1024,448),Image.Resampling.NEAREST))
    preview[0].save(ROOT/'validation/attack_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=17,loop=0)
    report=dict(source_sha256=hashlib.sha256(sms_rom.read_bytes()).hexdigest(),md_sha256=hashlib.sha256(md_rom.read_bytes()).hexdigest(),states_exact=70,normalized_images_exact=images,fields=list(fields),scope='One controlled actor-clear/clock initial state, then free motion: action during a walk, held action, mixed direction mask and a fresh second action')
    (ROOT/'validation/attack_motion_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
