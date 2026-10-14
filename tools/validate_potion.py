"""Potion source timeline: incremental refill, no mana cost, consumption/reset."""
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
    baseline=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();cases=[];differences=[];preview=[];images=0
    for label,hp,capacity in [('one-point',23,24),('eight-points',16,24),('low-health',1,24),('larger-capacity',33,48),('already-full',24,24)]:
        items=bytearray(17);items[0]=items[8]=1;source=ROOT/f'validation/sms-potion-{label}';target=ROOT/f'validation/md-potion-{label}';points=set(range(3740,3821));presses=PRESSES+[(3748,3810,8)]
        sw=[(3741,0x600,bytes(768)),(3741,0xdf,bytes([8])),(3741,0xe0,bytes(items)),(3741,0x318,bytes([hp])),(3741,0xda,bytes([capacity]))]
        tw=[(3741,symbols['world_actor_state'],bytes(768)),(3741,symbols['hero_selected_item'],(8).to_bytes(2,'big')),(3741,symbols['hero_items'],bytes(items)),(3741,symbols['hero_health'],hp.to_bytes(2,'big')),(3741,symbols['hero_max_health'],capacity.to_bytes(2,'big')),(3741,symbols['vtimer'],int(baseline[0x2f]).to_bytes(4,'big'))]
        run(rom,3820,source,points,[(200,220,0)]+presses,ram_writes=sw);run(md,3820,target,points,presses,ram_writes=tw)
        timeline=[]
        for frame in range(3741,3821):
            sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
            for name,address in [('hero_health',0x318),('hero_magic',0xdb),('hero_selected_item',0xdf),('hero_state',0x301)]:
                off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address],(label,frame,name,actual,sms[address])
            assert data[symbols['hero_items']+8]==sms[0xe8],('potion consumption',label,frame)
            timeline.append((frame,sms[0x318],sms[0xdf],sms[0xe8]))
            if frame>=3745:
                a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('potion image',label,frame,diff);images+=1
                if label=='eight-points' and frame%2==0:
                    pic=Image.new('RGB',(512,224));pic.paste(a,(0,16));pic.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0));preview.append(pic.resize((1024,448),Image.Resampling.NEAREST))
        assert timeline[-1][1]==capacity and timeline[-1][2:]==((8,1) if hp==capacity else (0,0))
        cases.append(dict(case=label,initial_health=hp,maximum=capacity,steps_exact=80,source_timeline=timeline))
    preview[0].save(ROOT/'validation/potion_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=40,loop=0)
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=cases,normalized_images_exact=images,scope='Potion slot 8, initial normal exterior, controlled ownership/clock, full-health retention, incremental heal and reset to main weapon',sound_ported=False)
    (ROOT/'validation/potion_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
