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
        assert json.loads((target/'capture.json').read_text())['rom_sha256']==hashlib.sha256(md.read_bytes()).hexdigest()
        for frame in range(3741,3781):
            sms=(source/f'ram_{frame:05}.bin').read_bytes();data=native(target,frame);off=symbols['world_loot_state']
            assert data[off:off+336]==sms[0x4b0:0x600],('loot record',kind,frame,[(i,x,y) for i,(x,y) in enumerate(zip(data[off:off+336],sms[0x4b0:0x600])) if x!=y][:10])
            off_actor=symbols['world_actor_state'];assert data[off_actor:off_actor+768]==sms[0x600:0x900],('freeze/actor state',kind,frame)
            for name,address in [('hero_gold',0xdd),('hero_health',0x318),('hero_magic',0xdb),('world_loot_style',0xa3)]:
                off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address],('loot effect',kind,frame,name,actual,sms[address])
            if frame>=3743:
                a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('loot image',kind,frame,diff);images+=1
        results.append(dict(type=kind,steps=40))
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=results,normalized_images_exact=images,pickup_frames_exact=240,full_game_ported=False,limits=['Controlled six loot pickup/freeze fixtures verify336 loot bytes,768 actor bytes, gold/HP/magic/style and228 normalized images.','Legacy full expiry visual validator is not included in this pickup-only report: its inherited3985 image gap is separately diagnosed againstv0141.'])
    (ROOT/'validation/loot_pickup_regression_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Six pickup fixtures:240 record/stat frames and228 normalized images exact.')

if __name__=='__main__':main()
