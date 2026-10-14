"""Compare normal movement state and rendered images on SMS vs native 68000."""
import json,re,hashlib
from PIL import Image
from extract_world import ROOT

def main():
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        match=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if match:symbols[match[2].split('.lto_priv.')[0]]=int(match[1],16)&65535
    names=['hero_y','hero_x','hero_direction','hero_animation','hero_counter']
    source=ROOT/'validation/sms-movement';target=ROOT/'validation/md-movement'
    capture=json.loads((source/'capture.json').read_text());differences=[];image_differences=[]
    native_capture=json.loads((target/'capture.json').read_text())
    assert capture['rom_sha256']==hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest()
    assert native_capture['rom_sha256']==hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    for frame in sorted(map(int,capture['captures'])):
        sms=(source/f'ram_{frame:05d}.bin').read_bytes()
        md=(target/f'ram_{frame:05d}.bin').read_bytes()
        md=bytes(v for n in range(0,len(md),2) for v in (md[n+1],md[n]))
        actual=[int.from_bytes(md[symbols[name]:symbols[name]+2],'big') for name in names]
        expected=[int.from_bytes(sms[0x310:0x312],'little'),int.from_bytes(sms[0x312:0x314],'little'),sms[0x30a],sms[0x30b],sms[0x304]]
        if actual!=expected:differences.append((frame,expected,actual))
        a=Image.open(source/f'frame_{frame:05d}.png').convert('RGB')
        b=Image.open(target/f'frame_{frame:05d}.png').convert('RGB').crop((0,16,256,208))
        palette=set(a.getdata())
        conversion={v:min(palette,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
        pixels=sum(x!=conversion[y] for x,y in zip(a.getdata(),b.getdata()))
        if pixels:image_differences.append((frame,pixels))
    report={'frames_compared':len(capture['captures']),'state_fields':names,'state_different_frames':len(differences),
            'md_sha256':native_capture['rom_sha256'],
            'image_different_frames':len(image_differences),'state_examples':differences[:12],
            'image_examples':image_differences[:12],
            'scope':'Normal-ground movement, wall collision, sliding, four directions and walking poses in room 0095.'}
    (ROOT/'validation/movement_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    assert not differences and not image_differences
    # Actual gameplay frames at integer scale, including the wall encounter.
    preview=Image.new('RGB',(512,224),(0,0,0));frames=[]
    for number in range(2600,2971,2):
        preview.paste(Image.open(source/f'frame_{number:05d}.png'),(0,16))
        preview.paste(Image.open(target/f'frame_{number:05d}.png'),(256,0))
        frames.append(preview.resize((1024,448),Image.Resampling.NEAREST))
    frames[0].save(ROOT/'validation/movement_sms_vs_md.gif',save_all=True,append_images=frames[1:],duration=33,loop=0)

if __name__=='__main__':main()
