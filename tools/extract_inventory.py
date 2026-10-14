"""Original-ROM inventory resource extraction; no captured state assets."""
from pathlib import Path
import json
from extract_title import rle_planes
ROOT=Path(__file__).resolve().parents[1]
def main():
    r=(ROOT/'input/original.sms').read_bytes();v=bytearray(0x4000)
    e,_=rle_planes(r,0x17609,v,0,4);e2,_=rle_planes(r,e,v,0x3840,2)
    m,_=rle_planes(r,0x177b5,v,0x100,4);m2,_=rle_planes(r,m,bytearray(0x1000),0,2)
    arrays={'inventory_header_rle':r[0x17609:e2],'inventory_map_rle':r[0x177b5:m2],'inventory_icons':r[0x12801:0x12801+27*128],'inventory_cursor_bitmap':r[0x124d4:0x124fc],'inventory_cursor_frame':r[0x7383:0x7390],'inventory_marker_frame':r[0x13c91:0x13c95],'inventory_positions':r[0x736b:0x7383],'inventory_charset':r[0xca94:0xcae4],'inventory_equipment_words':r[0xfe3c:0xfeb2]}
    lines=['#include <genesis.h>']
    for name,data in arrays.items():
        lines+=['const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%b for b in data[p:p+16])+',' for p in range(0,len(data),16)]+['};']
    (ROOT/'megadrive/src/inventory_data.c').write_text('\n'.join(lines)+'\n')
    (ROOT/'analysis/inventory_assets.json').write_text(json.dumps(dict(header_start=0x17609,header_end=e2,map_start=0x177b5,map_end=m2,icons_start=0x12801,icons_count=27,provenance='Original ROM resource slices; no emulator capture embedded'),indent=2)+'\n')
if __name__=='__main__':main()
