"""Continue preserves enlarged maxima, restores HP/magic 24 and redraws six HUD units."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    rom=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    source=ROOT/'validation/sms-resume-capacity';target=ROOT/'validation/md-resume-capacity';points=set(range(4110,4141));presses=PRESSES+[(3960,3964,8)]
    run(rom,4140,source,points,[(200,220,0)]+presses,ram_writes=[(3741,0x318,bytes(1)),(3741,0x600,bytes(768)),(3741,0xda,bytes([48,40,48])),(4080,0x600,bytes(768))])
    run(md,4140,target,points,presses,ram_writes=[(3741,symbols['hero_health'],bytes(2)),(3741,symbols['world_actor_state'],bytes(768)),(3741,symbols['hero_max_health'],(48).to_bytes(2,'big')),(3741,symbols['hero_magic'],(40).to_bytes(2,'big')),(3741,symbols['hero_max_magic'],(48).to_bytes(2,'big')),(3741,symbols['vtimer'],(167).to_bytes(4,'big')),(4080,symbols['world_actor_state'],bytes(768))])
    images=0
    for frame in points:
        sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
        for name,address,expected in [('hero_health',0x318,24),('hero_max_health',0xda,48),('hero_magic',0xdb,24),('hero_max_magic',0xdc,48)]:
            off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address]==expected,('resume capacity',frame,name,actual,sms[address])
        a=Image.open(source/f'frame_{frame:05}.png').convert('RGB').crop((0,160,256,192));b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,176,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('resumed HUD',frame,diff);images+=1
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),states_exact=31,hud_images_exact=images,scope='Initial exterior checkpoint with health/magic capacities 48, initial magic 40, controlled death/clock/enemies; Continue restores both values 24 and retains capacities',full_world_pixels_verified_by_this_test=False,other_checkpoint_classes_ported=False)
    (ROOT/'validation/resume_capacity_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
