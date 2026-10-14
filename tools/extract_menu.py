"""ROM-derived menu/font resources and Python reference for Z80 0877/0812."""
import json
from pathlib import Path
from extract_title import rle_planes
ROOT=Path(__file__).resolve().parents[1]

def frame(dst,offset,width,height,tiles):
    for y in range(height):
        for x in range(width):
            kind=(0 if y==0 else 2 if y==height-1 else 1)*3+(0 if x==0 else 2 if x==width-1 else 1)
            dst[offset+y*64+x*2:offset+y*64+x*2+2]=tiles[kind*2:kind*2+2]

def text(dst,offset,message,charset,base=0xd0,attribute=8):
    line=offset
    for value in message:
        if value==0: break
        if value==255: line+=64; offset=line; continue
        index=charset.find(bytes([value]))
        assert index>=0, f'unknown text byte {value:02x}'
        dst[offset]=(index+base)&255; dst[offset+1]=attribute; offset+=2

def mono(vram,offset,bitmap,mask,background=False):
    for n,value in enumerate(bitmap):
        for plane in range(4): vram[offset+n*4+plane]=value if mask&(1<<plane) else 0
        if background: vram[offset+n*4]=255

def main():
    rom=(ROOT/'input/original.sms').read_bytes(); vram=bytearray(0x4000)
    mono(vram,0x1400,rom[0xc776:0xc776+0x180],2)
    mono(vram,0x1a00,rom[0xc7c6:0xc7c6+0x100],3,True)
    mono(vram,0x3000,rom[0x1435:0x1435+0x38],3)
    end_numbers,_=rle_planes(rom,0x1274c,vram,0x1e00,4)
    end_symbols,_=rle_planes(rom,0x12707,vram,0x1f40,4)
    end,_=rle_planes(rom,0x13701,vram,0x3040,4)
    for n in range(0x3800,0x3e00,2): vram[n:n+2]=bytes.fromhex('fa01')
    tiles=rom[0x902:0x914]; charset=rom[0xca5e:0xca8e]
    message=rom[0xfe13:rom.index(0,0xfe13)+1]
    frame(vram,0x3a52,14,4,tiles)
    text(vram,0x3a98,message,charset)
    vram[0x3a96:0x3a98]=bytes.fromhex('8209')
    vram[0x3ad6:0x3ad8]=bytes.fromhex('ff18')
    (ROOT/'analysis/menu_reference.sms.vram.bin').write_bytes(vram)
    arrays={'menu_rle':rom[0x13701:end], 'font_bitmap':rom[0xc776:0xc776+0x180],
            'number_font_rle':rom[0x1274c:end_numbers],'symbol_font_rle':rom[0x12707:end_symbols],
            'normal_font':rom[0xc7c6:0xc7c6+0x100],'menu_cursor_bitmap':rom[0x1435:0x1435+0x38],
            'menu_frame_tiles':tiles,'text_charset':charset,'menu_text':message,
            'menu_palette':rom[0x1e20:0x1e30]}
    arrays.update({'name_text':rom[0xcaea:0xcb19],'name_grid':rom[0xcb19:0xcb48],
                   'name_typed_tiles':rom[0xcb48:0xcb70],'name_ascii':rom[0xcb70:0xcb98],
                   'name_positions':rom[0x1398:0x13ec],'name_caret_positions':rom[0x1388:0x1398],
                   'name_cursor_frame':rom[0x13ec:0x13f9],'name_delete_frame':rom[0x13f9:0x1418],
                   'name_finish_frame':rom[0x1418:0x1431],'name_caret_frame':rom[0x1431:0x1435]})
    arrays.update({'dialog_font':rom[0xc000:0xc776],'dialog_charset':rom[0xc8d6:0xc995],
                   'dialog_widths':rom[0xc995:0xca54],
                   'opening_text':rom[0xeb68:rom.index(0,0xeb68)+1]})
    lines=['#include <genesis.h>']
    for name,data in arrays.items():
        lines+=['const u8 %s[] = {'%name]+['    '+','.join('0x%02x'%b for b in data[p:p+16])+',' for p in range(0,len(data),16)]+['};']
    (ROOT/'megadrive/src/menu_data.c').write_text('\n'.join(lines)+'\n')
    report={'menu_patterns':{'offset':0x13701,'end':end},'text':message.decode('latin1'),
            'frame_destination':0xd852,'text_destination':0xd898,'width':14,'height':4,
            'font_descriptor':list(rom[0xca8e:0xca94]),'charset':charset.decode('ascii')}
    (ROOT/'analysis/menu_assets.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
