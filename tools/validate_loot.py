"""Seven loot records, pickup effects/HUD and deterministic explosion without RNG."""
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
    baseline=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();results=[];images=0
    def native(folder,frame):
        raw=(folder/f'ram_{frame:05}.bin').read_bytes();return bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
    for kind in range(8,14):
        source=ROOT/f'validation/sms-loot-{kind}';target=ROOT/f'validation/md-loot-{kind}'
        loot=bytearray(336);loot[0]=kind;loot[0x11]=112;loot[0x13]=136
        actors=bytearray(768)
        if kind==13:
            actors[:48]=baseline[0x600:0x630];actors[4]=128;actors[0x10:0x18]=bytes(8);actors[0x11]=64;actors[0x13]=32
        sw=[(3741,0x4b0,bytes(loot)),(3741,0x600,bytes(actors)),(3741,0x310,(0x7000).to_bytes(2,'little')+(0x8800).to_bytes(2,'little')),(3741,0xdd,bytes([253])),(3741,0x318,bytes([16])),(3741,0xdb,bytes([4]))]
        tw=[(3741,symbols['world_loot_state'],bytes(loot)),(3741,symbols['world_actor_state'],bytes(actors)),(3741,symbols['hero_x'],(0x8800).to_bytes(2,'big')),(3741,symbols['hero_y'],(0x7000).to_bytes(2,'big')),(3741,symbols['hero_gold'],(253).to_bytes(2,'big')),(3741,symbols['hero_health'],(16).to_bytes(2,'big')),(3741,symbols['hero_magic'],(4).to_bytes(2,'big')),(3741,symbols['vtimer'],int(baseline[0x2f]).to_bytes(4,'big'))]
        points=set(range(3740,3781));run(rom,3780,source,points,[(200,220,0)]+PRESSES,ram_writes=sw);run(md,3780,target,points,PRESSES,ram_writes=tw)
        for frame in range(3741,3781):
            sms=(source/f'ram_{frame:05}.bin').read_bytes();data=native(target,frame);off=symbols['world_loot_state']
            assert data[off:off+336]==sms[0x4b0:0x600],('loot record',kind,frame,[(i,x,y) for i,(x,y) in enumerate(zip(data[off:off+336],sms[0x4b0:0x600])) if x!=y][:10])
            off_actor=symbols['world_actor_state'];assert data[off_actor:off_actor+768]==sms[0x600:0x900],('freeze/actor state',kind,frame)
            for name,address in [('hero_gold',0xdd),('hero_health',0x318),('hero_magic',0xdb),('world_loot_style',0xa3)]:
                off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address],('loot effect',kind,frame,name,actual,sms[address])
            if frame>=3743:
                a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('loot image',kind,frame,diff);images+=1
        results.append(dict(type=kind,steps=40))
    # Fill all seven slots away from the hero and let their entire lifetime run.
    loot=bytearray(336)
    for slot in range(7):
        loot[slot*48]=8;loot[slot*48+0x11]=32+slot*16;loot[slot*48+0x13]=32+slot*28
    source=ROOT/'validation/sms-loot-expiry';target=ROOT/'validation/md-loot-expiry';points=set(range(3740,4111))
    run(rom,4110,source,points,[(200,220,0)]+PRESSES,ram_writes=[(3741,0x4b0,bytes(loot)),(3741,0x600,bytes(768)),(3741,0x310,(0x7000).to_bytes(2,'little')+(0x8800).to_bytes(2,'little'))])
    run(md,4110,target,points,PRESSES,ram_writes=[(3741,symbols['world_loot_state'],bytes(loot)),(3741,symbols['world_actor_state'],bytes(768)),(3741,symbols['hero_x'],(0x8800).to_bytes(2,'big')),(3741,symbols['hero_y'],(0x7000).to_bytes(2,'big')),(3741,symbols['vtimer'],int(baseline[0x2f]).to_bytes(4,'big'))])
    removed=None;expiry_images=0;preview=[]
    for frame in range(3741,4111):
        sms=(source/f'ram_{frame:05}.bin').read_bytes()[0x4b0:0x600];data=native(target,frame);off=symbols['world_loot_state'];assert data[off:off+336]==sms,('expiry',frame,[(i,x,y) for i,(x,y) in enumerate(zip(data[off:off+336],sms)) if x!=y][:12])
        if not any(sms) and removed is None:removed=frame
        if frame>=3743:
            a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('expiry image',frame,diff);expiry_images+=1
            if frame%3==0:
                picture=Image.new('RGB',(512,224));picture.paste(a,(0,16));picture.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0));preview.append(picture.resize((1024,448),Image.Resampling.NEAREST))
    assert removed is not None
    preview[0].save(ROOT/'validation/loot_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=50,loop=0)
    for folder in [ROOT/f'validation/md-loot-{kind}' for kind in range(8,14)]+[target]:
        assert json.loads((folder/'capture.json').read_text())['rom_sha256']==hashlib.sha256(md.read_bytes()).hexdigest()
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=results,normalized_images_exact=images,scope='Direct controlled loot allocation, pickup stats/graphics/HUD; normal exterior initial equipment',drop_random_stream_exact=False,expiry_and_slot_capacity_verified=True,expiry_steps_exact=370,expiry_images_exact=expiry_images,all_seven_slots_removed_at=removed,freeze_on_active_enemy_verified=True)
    (ROOT/'validation/loot_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
