"""Extract 1733..1756 class-2 animation stream copied into SMS SRAM 9000."""
import hashlib,json
from extract_title import ROOT,rle_planes

def extract(rom):
    pointer=int.from_bytes(rom[0x175d:0x175f],'little');start=0x2c000+(pointer&0x3fff)
    decoded=bytearray(0x400);end,size=rle_planes(rom,start,decoded,0,4)
    assert size==576 and rom[0x6aeb:0x6af3]==bytes.fromhex('0090c0908091c090')
    return start,end,decoded

def main():
    rom=(ROOT/'input/original.sms').read_bytes();start,end,decoded=extract(rom);blob=decoded[:576]
    lines=['#include <genesis.h>','/* Class-2 animation stream decoded into original SRAM 9000..93FF. */','const u8 dungeon_animation_bitmaps[] = {']+['    '+','.join('0x%02x'%b for b in blob[n:n+16])+',' for n in range(0,len(blob),16)]+['};']
    (ROOT/'megadrive/src/dungeon_animation_data.c').write_text('\n'.join(lines)+'\n')
    (ROOT/'analysis/dungeon_bitmap_reference.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(rom).hexdigest(),compressed_start=start,compressed_end=end,decoded_sram_start=0x9000,decoded_bytes=1024,frames=3,tiles_per_frame=6,source_pointer_table=0x6aeb,order=[0,1,2,1],period_frames=8),indent=2)+'\n')
    print('Original class-2 SRAM animation extracted:',hex(start),hex(end))
if __name__=='__main__':main()
