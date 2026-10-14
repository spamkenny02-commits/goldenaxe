"""Check ROM fade component order and contour writes against both live cores."""
import hashlib,json,re
from pathlib import Path
from PIL import Image
from run_core import run
from validate_actor_tick import PRESSES
ROOT=Path(__file__).resolve().parents[1]


def main():
    rom=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    source=ROOT/'validation/sms-resume-detail';target=ROOT/'validation/md-resume-detail'
    frames=set(range(3959,4121));inputs=PRESSES+[(3960,3964,8)]
    run(rom,4120,source,frames,[(200,220,0)]+inputs,ram_writes=[(3741,0x318,bytes(1)),(3741,0x600,bytes(768)),(3960,0xdd,bytes([100]))])
    run(md,4120,target,frames,inputs,ram_writes=[(3741,symbols['hero_health'],bytes(2)),(3741,symbols['world_actor_state'],bytes(768)),(3741,symbols['vtimer'],(167).to_bytes(4,'big')),(3960,symbols['hero_gold'],(100).to_bytes(2,'big'))])
    def swap(raw):return bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
    source_ram={f:(source/f'ram_{f:05}.bin').read_bytes() for f in frames}
    native_ram={f:swap((target/f'ram_{f:05}.bin').read_bytes()) for f in frames}
    def value(f,name,size=2):
        offset=symbols[name];return int.from_bytes(native_ram[f][offset:offset+size],'big')
    def palette(f):
        offset=symbols['sms_palette'];return bytes(native_ram[f][offset+n*2+1] for n in range(32))
    def epochs(items):
        result=[]
        for frame,pal in items:
            if not result or result[-1][1]!=pal:result.append((frame,pal))
        return result
    source_out=epochs((f,source_ram[f][0x1ca0:0x1cc0]) for f in range(3960,3978))
    target_out=epochs((f,palette(f)) for f in sorted(frames) if value(f,'resume_phase')==1 and value(f,'resume_fade_step')>0)
    source_in=epochs((f,source_ram[f][0x1ca0:0x1cc0]) for f in range(4014,4032))
    target_in=epochs((f,palette(f)) for f in sorted(frames) if value(f,'resume_phase')==3 and value(f,'resume_fade_step')>0)
    # Count only fully prepared component steps (the diagnostic counter is
    # written after all 32 entries), excluding interrupted initial RAM writes.
    # The observable stage may start before the first changed palette reaches
    # RAM. Retain the initial black hold separately from actual fade steps.
    initial_black_hold=[]
    while target_in and not any(target_in[0][1]):
        initial_black_hold.append(target_in.pop(0)[0])
    assert not any(source_ram[4013][0x1ca0:0x1cc0]), 'source initial black palette'
    assert [x[1] for x in source_out]==[x[1] for x in target_out], 'fade-out palette sequence'
    assert [x[1] for x in source_in]==[x[1] for x in target_in], 'fade-in palette sequence'
    original=rom.read_bytes();table=original[0x2011:0x2051]
    final=source_ram[4012][0x1600:0x1c00];expected=bytearray(bytes.fromhex('ff18')*768)
    contour_checks=[];image_checks=[]
    def converted(word):
        return (((word>>11)&1)<<13)|(((word>>12)&1)<<15)|(((word>>10)&1)<<12)|(((word>>9)&1)<<11)|(16+(word&511))
    def image_difference(a_frame,b_frame):
        a=Image.open(source/f'frame_{a_frame:05}.png').convert('RGB')
        b=Image.open(target/f'frame_{b_frame:05}.png').convert('RGB').crop((0,16,256,208))
        colors=set(a.getdata());conversion={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
        return sum(x!=conversion[y] for x,y in zip(a.getdata(),b.getdata()))
    for contour in range(16):
        part=table[contour*4:contour*4+4];address=int.from_bytes(part[:2],'little');height,width=part[2:]
        for increment,count in ((2,width),(64,height),(-2,width),(-64,height)):
            for n in range(count):
                address+=increment;off=address-0x7800;expected[off:off+2]=final[off:off+2]
        candidates=[f for f in sorted(frames) if value(f,'resume_phase')==4 and value(f,'resume_contour')==contour+1]
        if contour==15:candidates=[f for f in sorted(frames) if value(f,'resume_contour')==16 and value(f,'hero_state')==0]
        assert candidates,('missing contour',contour)
        frame=candidates[-1];regs=(target/f'vdp_regs_{frame:05}.bin').read_bytes();vram=swap((target/f'vram_{frame:05}.bin').read_bytes())
        base_a=(regs[2]&0x38)<<10;base_b=(regs[4]&7)<<13;plane_width=32<<(regs[16]&3)
        for index in range(768):
            word=int.from_bytes(expected[index*2:index*2+2],'little');x=index&31;y=(index>>5)+2
            addr_a=base_a+(y*plane_width+x)*2;addr_b=base_b+(y*plane_width+x)*2
            assert int.from_bytes(vram[addr_a:addr_a+2],'big')==converted(word),('native foreground',contour,frame,index)
            assert int.from_bytes(vram[addr_b:addr_b+2],'big')==((3 if word&0x800 else 2)<<13)|1,('native backdrop',contour,frame,index)
        source_frame=4034+contour*2
        source_vram=(source/f'vram_{source_frame:05}.bin').read_bytes()[0x3800:0x3e00]
        # Source writes may straddle the visible scanlines; VRAM after retro_run
        # must nevertheless contain the same accumulated contours.
        source_mismatches=sum(x!=y for x,y in zip(source_vram,expected))
        assert source_mismatches==0,('source contour',contour,source_frame,source_mismatches)
        contour_checks.append(dict(contour=contour+1,source_frame=source_frame,target_frame=frame,source_vram_byte_mismatches=source_mismatches,native_words_exact=768))
        differences=image_difference(source_frame+1,frame)
        assert differences==0,('contour image',contour,source_frame+1,frame,differences)
        image_checks.append(dict(contour=contour+1,source_frame=source_frame+1,target_frame=frame,normalized_pixel_mismatches=differences))
    preview=[]
    for item in image_checks:
        picture=Image.new('RGB',(512,224));picture.paste(Image.open(source/f"frame_{item['source_frame']:05}.png"),(0,16));picture.paste(Image.open(target/f"frame_{item['target_frame']:05}.png"),(256,0));preview.append(picture.resize((1024,448),Image.Resampling.NEAREST))
    preview[0].save(ROOT/'validation/resume_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=150,loop=0)
    report=dict(source_sha256=hashlib.sha256(original).hexdigest(),md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),fade_in_initial_black_hold_frames=initial_black_hold,fade_out_palette_epochs_exact=len(source_out),fade_in_palette_epochs_exact=len(source_in),fade_out_frame_pairs=[(a[0],b[0]) for a,b in zip(source_out,target_out)],fade_in_frame_pairs=[(a[0],b[0]) for a,b in zip(source_in,target_in)],contours=contour_checks,images=image_checks,absolute_preparation_timing_exact=False,scope='Initial checkpoint: native ROM-driven fades and complete contour transfers; controlled death, clock and gold',other_checkpoint_classes_ported=False)
    (ROOT/'validation/resume_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
