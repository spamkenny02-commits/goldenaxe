"""Reference implementation of Z80 032A, 0BD3 and 0BFE; title assets from bank 7."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def rle_planes(src,pos,dst,start,stride):
    ends=[]
    for plane in range(stride):
        address=start+plane
        while True:
            command=src[pos]; pos+=1
            if command==0: break
            count=(command&127) or 256
            literal=bool(command&128)
            for _ in range(count):
                assert address < len(dst)
                dst[address]=src[pos]
                address+=stride
                if literal: pos+=1
            if not literal: pos+=1
        ends.append(address)
    return pos, ends[-1]+1-stride

def map_decode(src,pos):
    scratch=bytearray()
    while True:
        command=src[pos]; pos+=1
        if command==0: break
        count=(command&127) or 256
        if command&128:
            scratch.extend(src[pos:pos+count]); pos+=count
        else:
            value=src[pos]; pos+=1
            scratch.extend((value+i)&255 for i in range(count))
    scratch.append(0) # actual scratch RAM is reset at startup; bounds checked below
    output=bytearray(0x600)
    end, _=rle_planes(scratch,0,output,0,2)
    assert end <= len(scratch)
    return pos,output,scratch

def main():
    from title_loading_cost import title_cost
    rom=(ROOT/'input/original.sms').read_bytes()
    bank=rom[7*0x4000:8*0x4000]
    vram=bytearray(0x4000)
    pos,pattern_end=rle_planes(bank,16,vram,0,4)
    map_start=pos
    pos,tilemap,scratch=map_decode(bank,pos)
    pos2,second,_=map_decode(bank,pos)
    vram[0x3900:0x3f00]=tilemap
    palette=[((b&3)*85,((b>>2)&3)*85,((b>>4)&3)*85) for b in bank[:16]]
    image=Image.new('RGB',(256,192),palette[0])
    for ty in range(24):
        for tx in range(32):
            addr=0x3800+(ty*32+tx)*2
            entry=int.from_bytes(vram[addr:addr+2],'little')
            tile=entry&511
            for y in range(8):
                sy=7-y if entry&0x400 else y
                planes=vram[tile*32+sy*4:tile*32+sy*4+4]
                for x in range(8):
                    sx=7-x if entry&0x200 else x
                    color=sum(((b>>(7-sx))&1)<<p for p,b in enumerate(planes))
                    image.putpixel((tx*8+x,ty*8+y),palette[color])
    image.save(ROOT/'analysis/title_reference.png')
    (ROOT/'analysis/title_patterns.sms.bin').write_bytes(vram[:pattern_end])
    (ROOT/'analysis/title_map.sms.bin').write_bytes(tilemap)
    meta={'bank':7,'palette_offset':0x1c000,'patterns_start':0x1c010,
          'patterns_end':0x1c000+map_start,'decoded_pattern_bytes':pattern_end,
          'tilemap_start':0x1c000+map_start,'tilemap_end':0x1c000+pos,
          'second_map_end':0x1c000+pos2,'map_vram_destination':0x3900,
          'preview':'Initial title map before Z80 routines 165C..169C animate it; not final title screen.'}
    meta['loading_cost']=title_cost(rom)
    (ROOT/'analysis/title_assets.json').write_text(json.dumps(meta,indent=2))
    # Keep compressed source so native routines perform the same decoding at boot.
    used=bank[:pos2]
    lines=['#include <genesis.h>','const u8 title_bank7[] = {']
    lines += ['    '+','.join('0x%02x'%b for b in used[p:p+16])+',' for p in range(0,len(used),16)]
    lines+=['};','const u32 title_bank7_size = %d;'%len(used)]
    lines+=['const u32 title_loading_tstates = %d;'%meta['loading_cost']['foreground_tstates']]
    target=ROOT/'megadrive/src'; target.mkdir(parents=True,exist_ok=True)
    (target/'title_data.c').write_text('\n'.join(lines)+'\n')
    print(json.dumps(meta,indent=2))

if __name__=='__main__': main()
