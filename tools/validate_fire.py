"""Compare native fire casts with the original Z80 object and normalized frames."""
import argparse,hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',action='append');args=parser.parse_args()
    rom=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    initial=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();results=[];images=0
    for label,direction,level,magic in [('up',0,1,24),('down',1,1,24),('left',2,1,24),('right',3,1,24),('up-level2',0,2,24),('down-level2',1,2,24),('left-level2',2,2,24),('right-level2',3,2,24),('below-cost',0,1,7),('four-charge',0,1,8),('hurt-copy',0,1,24)]:
        if args.case and label not in args.case:continue
        source=ROOT/f'validation/sms-fire-{label}';target=ROOT/f'validation/md-fire-{label}';items=bytearray(17);items[0]=1;items[4]=level
        sw=[(3741,0x600,bytes(768)),(3741,0xdf,b'\x04'),(3741,0xe0,bytes(items)),(3741,0x30a,bytes([direction])),(3741,0xdb,bytes([magic]))]
        tw=[(3741,symbols['world_actor_state'],bytes(768)),(3741,symbols['hero_selected_item'],(4).to_bytes(2,'big')),(3741,symbols['hero_items'],bytes(items)),(3741,symbols['hero_direction'],direction.to_bytes(2,'big')),(3741,symbols['hero_magic'],magic.to_bytes(2,'big')),(3741,symbols['vtimer'],int(initial[0x2f]).to_bytes(4,'big'))]
        if label=='hurt-copy':
            sw.append((3741,0x305,b'\x0a'));tw.append((3741,symbols['hero_hurt'],(10).to_bytes(2,'big')))
        points=set(range(3740,3861));presses=PRESSES+[(3748,3755,8),(3757,3760,8),(3775,3778,8),(3795,3798,8),(3815,3818,8),(3835,3838,8)]
        run(rom,3860,source,points,[(200,220,0)]+presses,ram_writes=sw);run(md,3860,target,points,presses,ram_writes=tw)
        for frame in range(3741,3861):
            sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
            for name,address in [('hero_magic',0xdb),('hero_selected_item',0xdf),('hero_state',0x301),('hero_animation',0x30b),('hero_attack',0x319),('hero_attack_phase',0x30e),('hero_fire_charge',0xc6)]:
                off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address],(label,frame,name,actual,sms[address])
            off=symbols['world_spell_state'];actual=data[off:off+48];expected=sms[0x330:0x360]
            assert actual==expected,(label,frame,'spell',[(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b])
            if frame>=3745:
                a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('fire pixels',label,frame,diff);images+=1
        results.append(dict(case=label,direction=direction,level=level,initial_magic=magic,steps_exact=120))
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=results,normalized_images_exact=images,scope='Exterior fire slot 4, both levels, four directions, held/repeated presses, active projectile guard and charge; controlled ownership/clock/enemies',enemy_collisions_ported=True,sound_ported=False)
    (ROOT/('validation/fire_report.json' if not args.case else 'validation/fire_focus_report.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
