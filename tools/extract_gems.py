"""Extract gem descriptors, labels and the original 2B2C glyph copy."""
import hashlib,json
from pathlib import Path
from extract_title import rle_planes
ROOT=Path(__file__).resolve().parents[1]
def main():
 r=(ROOT/'input/original.sms').read_bytes();v=bytearray(16384);rle_planes(r,0x13701,v,0x3040,4)
 labels=bytearray();indices=bytearray();icons=bytearray();records=[]
 for dungeon in range(1,10):
  tile=r[0x1edc+(dungeon-1)*2];item=(tile+0x9f)&255;assert 0x21<=item<=0x29
  p=int.from_bytes(r[0x63b3+item*2:0x63b5+item*2],'little');a=0xc000+(p&0x3fff);text=r[a:r.index(0,a)+1]
  indices.extend(len(labels).to_bytes(2,'little'));labels.extend(text)
  glyph=v[0x3040+(item-0x21)*32:0x3060+(item-0x21)*32]
  icons.extend(glyph)
  records.append(dict(dungeon=dungeon,tile=tile,item=item,label_pointer=p,label_hex=text.hex()))
 descriptor=0x304a1;count=r[descriptor]&127;assert count==5
 arrays=dict(gem_descriptor_data=r[0x2acd:0x2add],gem_tile_table=r[0x1edc:0x1fdc],gem_labels=labels,gem_label_index=indices,gem_window_icons=icons,gem_reward_hero_frame=bytes([count])+r[descriptor+3:descriptor+3+count*3])
 c=['#include <genesis.h>']
 for name,data in arrays.items():c+=['const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%b for b in data[p:p+16])+',' for p in range(0,len(data),16)]+['};']
 (ROOT/'megadrive/src/gem_data.c').write_text('\n'.join(c)+'\n')
 (ROOT/'analysis/gem_resources.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(r).hexdigest(),records=records,gem_descriptors='2ACD..2ADC',window_icon_bytes_written=32,window_icon_remaining_bytes_preserved=96,reward_hero_frame=descriptor),indent=2)+'\n')
if __name__=='__main__':main()
