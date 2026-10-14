"""Original heal spell: magic threshold, clamping, fresh presses and HUD capacity."""
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
    initial=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();results=[];images=0;preview=[]
    for label,hp,maximum,magic,capacity in [('no-magic',1,24,0,24),('below-cost',9,24,23,24),('minimum',1,24,24,24),('clamped',23,24,24,24),('already-full',24,24,24,24),('larger-capacity',9,48,48,48),('capacity-only',24,48,48,48)]:
        source=ROOT/f'validation/sms-heal-{label}';target=ROOT/f'validation/md-heal-{label}';items=bytearray(17);items[0]=items[7]=1
        sw=[(3741,0x600,bytes(768)),(3741,0xdf,bytes([7])),(3741,0xe0,bytes(items)),(3741,0x318,bytes([hp])),(3741,0xda,bytes([maximum,magic,capacity]))]
        tw=[(3741,symbols['world_actor_state'],bytes(768)),(3741,symbols['hero_selected_item'],(7).to_bytes(2,'big')),(3741,symbols['hero_items'],bytes(items)),(3741,symbols['hero_health'],hp.to_bytes(2,'big')),(3741,symbols['hero_max_health'],maximum.to_bytes(2,'big')),(3741,symbols['hero_magic'],magic.to_bytes(2,'big')),(3741,symbols['hero_max_magic'],capacity.to_bytes(2,'big')),(3741,symbols['vtimer'],int(initial[0x2f]).to_bytes(4,'big'))]
        points=set(range(3740,3806));presses=PRESSES+[(3748,3765,8),(3790,3793,8)]
        run(rom,3805,source,points,[(200,220,0)]+presses,ram_writes=sw);run(md,3805,target,points,presses,ram_writes=tw)
        for frame in range(3741,3806):
            sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
            for name,address in [('hero_health',0x318),('hero_magic',0xdb),('hero_selected_item',0xdf),('hero_state',0x301),('hero_animation',0x30b),('hero_attack',0x319)]:
                off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address],(label,frame,name,actual,sms[address])
            if frame>=3745:
                a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('heal pixels',label,frame,diff);images+=1
                if label=='larger-capacity' and frame%2==0:
                    pic=Image.new('RGB',(512,224));pic.paste(a,(0,16));pic.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0));preview.append(pic.resize((1024,448),Image.Resampling.NEAREST))
        final=(source/'ram_03805.bin').read_bytes();expected_activations=min(2,magic//24);assert final[0xdb]==magic-expected_activations*24;assert final[0x318]==min(maximum,hp+expected_activations*16)
        assert json.loads((target/'capture.json').read_text())['rom_sha256']==hashlib.sha256(md.read_bytes()).hexdigest()
        results.append(dict(case=label,initial_health=hp,max_health=maximum,magic=magic,max_magic=capacity,steps_exact=65,activations=expected_activations))
    preview[0].save(ROOT/'validation/heal_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=40,loop=0)
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=results,normalized_images_exact=images,scope='Heal slot 7, initial exterior, magic 0/23/24/48, health capacity 24/48, held/repeated button, controlled ownership/clock',other_classes_heal_behavior_ported=False,sound_ported=False)
    (ROOT/'validation/heal_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
