"""Vertical scrolling milestone; also expose unported destination object work."""
import hashlib,json,re
from PIL import Image
from extract_world import ROOT

def main():
    source=ROOT/'validation/sms-vertical';target=ROOT/'validation/md-vertical'
    if (ROOT/'validation/sms-vertical-check/capture.json').exists():source=ROOT/'validation/sms-vertical-check'
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        match=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if match:symbols[match[2].split('.lto_priv.')[0]]=int(match[1],16)&65535
    capture=json.loads((target/'capture.json').read_text())
    assert capture['rom_sha256']==hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    states=[];pixels=[];images=[]
    for frame in range(3000,3161):
        sms=(source/f'ram_{frame:05d}.bin').read_bytes();raw=(target/f'ram_{frame:05d}.bin').read_bytes()
        md=bytes(v for n in range(0,len(raw),2)for v in(raw[n+1],raw[n]))
        names=['game_state','room_id','hero_y','hero_x','hero_direction','hero_animation','hero_counter']
        actual=[int.from_bytes(md[symbols[name]:symbols[name]+2],'big')for name in names]
        expected=[sms[0x1d],int.from_bytes(sms[0xb9:0xbb],'little'),int.from_bytes(sms[0x310:0x312],'little'),int.from_bytes(sms[0x312:0x314],'little'),sms[0x30a],sms[0x30b],sms[0x304]]
        if actual!=expected:states.append(frame)
        assert actual[1:]==expected[1:],('room/hero state',frame,expected,actual)
        a=Image.open(source/f'frame_{frame:05d}.png').convert('RGB');b=Image.open(target/f'frame_{frame:05d}.png').convert('RGB').crop((0,16,256,208))
        palette=set(a.getdata());conversion={v:min(palette,key=lambda t:sum((x-y)**2 for x,y in zip(v,t)))for v in set(b.getdata())}
        differences=sum(x!=conversion[y]for x,y in zip(a.getdata(),b.getdata()))
        if differences:pixels.append((frame,differences))
        if 3044<=frame<=3071:
            canvas=Image.new('RGB',(512,224));canvas.paste(a,(0,16));canvas.paste(b,(256,16));images.append(canvas.resize((1024,448),Image.Resampling.NEAREST))
        if frame==3070:
            address=symbols['sms_vram']+0x3800
            assert md[address:address+0x600]==sms[0x1600:0x1c00]
    # Scrolling geometry is proven; initialization and subsequent entities are
    # deliberately reported as incomplete rather than counted as passing.
    assert not [f for f in states if f<=3069]
    assert not [(f,n)for f,n in pixels if f<=3070]
    report={'md_sha256':capture['rom_sha256'],'route':'0094 -> 00A4, south',
            'verified_state_frames':161-len(states),
            'loading_state_timing_exact':not states,
            'verified_image_frames':161-len(pixels),
            'verified_scroll_image_frames':71,'arrival_map_identical':True,
            'verified_room_and_hero_state_frames':161,
            'first_remaining_state_difference':min(states)if states else None,
            'first_remaining_image_difference':pixels[0]if pixels else None,
            'remaining_different_state_frames':len(states),'remaining_different_image_frames':len(pixels),
            'remaining_work':'Types20..22 and 26..28 spawn/move natively; ranged types create exterior projectiles10..12. Loading state timing matches on this route. Spawn positions still differ because SGDK random replaces the original R stream; general IRQ/VDP loading budgets, sprite overflow and original randomness remain incomplete.',
            'whole_vertical_room_entry_complete':False}
    (ROOT/'validation/vertical_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    images[0].save(ROOT/'validation/vertical_sms_vs_md.gif',save_all=True,append_images=images[1:],duration=33,loop=0)

if __name__=='__main__':main()
