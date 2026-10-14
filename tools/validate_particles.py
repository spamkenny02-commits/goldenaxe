"""Type-1 explosion poses and deterministic original-type-zero cleanup."""
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
    initial=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();entity=bytearray(768);entity[0]=1;entity[3]=0x2b;entity[8]=0x24;entity[9]=0x86;entity[0x11]=64;entity[0x13]=64
    source=ROOT/'validation/sms-particles';target=ROOT/'validation/md-particles';points=set(range(3740,3771))
    run(rom,3770,source,points,[(200,220,0)]+PRESSES,ram_writes=[(3741,0x600,bytes(entity))])
    run(md,3770,target,points,PRESSES,ram_writes=[(3741,symbols['world_actor_state'],bytes(entity)),(3741,symbols['vtimer'],int(initial[0x2f]).to_bytes(4,'big'))])
    images=0;preview=[];removed=None
    for frame in range(3741,3771):
        sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]));off=symbols['world_actor_state'];a=sms[0x600:0x900];b=data[off:off+768]
        assert a==b,('particle state',frame,[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y][:12])
        off=symbols['world_actor_count'];assert int.from_bytes(data[off:off+2],'big')==sms[0xa2]
        if not a[0] and removed is None:removed=frame
        if frame>=3743:
            left=Image.open(source/f'frame_{frame:05}.png').convert('RGB');right=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(left.getdata());cv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(right.getdata())};diff=sum(x!=cv[y] for x,y in zip(left.getdata(),right.getdata()));assert diff==0,('particle image',frame,diff);images+=1
            picture=Image.new('RGB',(512,224));picture.paste(left,(0,16));picture.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0));preview.append(picture.resize((1024,448),Image.Resampling.NEAREST))
    assert removed is not None
    preview[0].save(ROOT/'validation/particles_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=33,loop=0)
    report=dict(source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),states_exact=30,normalized_images_exact=images,removed_at=removed,scope='Five explosion poses, original type zero, no random loot branch',random_drop_branch_exact=False)
    (ROOT/'validation/particles_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
