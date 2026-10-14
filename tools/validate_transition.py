"""SMS/native exterior transition, including each captured scrolling frame."""
import json,re,hashlib
from PIL import Image
from extract_world import ROOT

def main():
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        match=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if match:symbols[match[2].split('.lto_priv.')[0]]=int(match[1],16)&65535
    source=ROOT/'validation/sms-transition-detail';target=ROOT/'validation/md-transition'
    capture=json.loads((source/'capture.json').read_text());native_capture=json.loads((target/'capture.json').read_text())
    assert native_capture['rom_sha256']==hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    state_errors=[];image_errors=[]
    names=['game_state','room_id','hero_y','hero_x','hero_direction','hero_animation','hero_counter']
    frames=sorted(map(int,capture['captures']))
    for frame in frames:
        sms=(source/f'ram_{frame:05d}.bin').read_bytes();md=(target/f'ram_{frame:05d}.bin').read_bytes()
        md=bytes(v for n in range(0,len(md),2)for v in(md[n+1],md[n]))
        actual=[int.from_bytes(md[symbols[name]:symbols[name]+2],'big') for name in names]
        expected=[sms[0x1d],int.from_bytes(sms[0xb9:0xbb],'little'),int.from_bytes(sms[0x310:0x312],'little'),int.from_bytes(sms[0x312:0x314],'little'),sms[0x30a],sms[0x30b],sms[0x304]]
        if actual!=expected:state_errors.append((frame,expected,actual))
        a=Image.open(source/f'frame_{frame:05d}.png').convert('RGB')
        b=Image.open(target/f'frame_{frame:05d}.png').convert('RGB').crop((0,16,256,208))
        palette=set(a.getdata());conversion={v:min(palette,key=lambda t:sum((x-y)**2 for x,y in zip(v,t)))for v in set(b.getdata())}
        errors=sum(x!=conversion[y]for x,y in zip(a.getdata(),b.getdata()))
        if errors:image_errors.append((frame,errors))
    report={'scope':'Exterior transition 0095 -> 0094 -> 0095, left and right, per-frame state and image comparison.',
            'md_sha256':native_capture['rom_sha256'],'frames_compared':len(frames),
            'different_state_frames':len(state_errors),'different_image_frames':len(image_errors),
            'state_examples':state_errors[:10],'image_examples':image_errors[:20]}
    (ROOT/'validation/transition_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    assert not state_errors and not image_errors
    arrivals=[]
    for frame,number in [(2900,0x94),(3130,0x95)]:
        ram=(source/f'ram_{frame:05d}.bin').read_bytes()
        native=(target/f'ram_{frame:05d}.bin').read_bytes()
        native=bytes(v for n in range(0,len(native),2)for v in(native[n+1],native[n]))
        offset=symbols['sms_vram']+0x3800
        assert native[offset:offset+0x600]==ram[0x1600:0x1c00]
        arrivals.append(number)
    report['arrival_maps_identical']=arrivals
    (ROOT/'validation/transition_report.json').write_text(json.dumps(report,indent=2)+'\n')
    images=[]
    for frame in range(2774,2821):
        canvas=Image.new('RGB',(512,224),(0,0,0))
        canvas.paste(Image.open(source/f'frame_{frame:05d}.png'),(0,16))
        canvas.paste(Image.open(target/f'frame_{frame:05d}.png'),(256,0))
        images.append(canvas.resize((1024,448),Image.Resampling.NEAREST))
    images[0].save(ROOT/'validation/transition_sms_vs_md.gif',save_all=True,append_images=images[1:],duration=33,loop=0)

if __name__=='__main__':main()
