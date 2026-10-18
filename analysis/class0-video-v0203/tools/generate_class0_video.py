"""Generate MD pixels and tile attributes from original class0 SMS assets."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def generate():
 rom=(ROOT/'input/original.sms').read_bytes();offset=0x3c010;planes=[]
 for plane in range(4):
  data=bytearray()
  while rom[offset]:
   command=rom[offset];offset+=1;count=command&127 or 256
   if command&128:data.extend(rom[offset:offset+count]);offset+=count
   else:data.extend([rom[offset]]*count);offset+=1
  offset+=1;planes.append(data)
 assert len({len(p) for p in planes})==1 and len(planes[0])==193*8
 packed=[]
 for row in range(len(planes[0])):
  value=0
  for x in range(8):value=(value<<4)|sum(((planes[p][row]>>(7-x))&1)<<p for p in range(4))
  packed.append(value)
 # The raw native-endian word indexes this table directly. Duplicating
 # unused source attribute bits trades ROM space for byte-swap-free68000 code.
 attrs=[]
 for low in range(256):
  for high in range(256):
   w=low|(high<<8);attrs.append(((w>>11)&1)<<13|((w>>12)&1)<<15|((w>>10)&1)<<12|((w>>9)&1)<<11|16+(w&511))
 levels=[0,3,5,7];colors=[levels[w&3]<<1|levels[(w>>2)&3]<<5|levels[(w>>4)&3]<<9 for w in range(64)]
 lines=['#ifndef GAW_CLASS0_VIDEO_ASSETS_H','#define GAW_CLASS0_VIDEO_ASSETS_H','#include <types.h>']
 for name,typ,values,digits in [('gaw_class0_md_patterns','u32',packed,8),('gaw_sms_md_attributes','u16',attrs,4),('gaw_sms_md_colors','u16',colors,4)]:
  lines.append(f'static const {typ} {name}[]={{')
  for pos in range(0,len(values),16):lines.append(' '+','.join(f'0x{v:0{digits}x}'+('UL' if typ=='u32' else '') for v in values[pos:pos+16])+',')
  lines.append('};')
 lines.extend([f'#define GAW_CLASS0_BACKGROUND_COLOR 0x{colors[rom[0x3c000]&63]:04x}',
  'static const u8 gaw_class0_sms_palette[]={'+','.join(map(str,rom[0x3c000:0x3c010]))+'};','#endif'])
 header=ROOT/'megadrive/src/source_class0_video_assets_generated.h';raw=('\n'.join(lines)+'\n').encode()
 if not header.exists() or header.read_bytes()!=raw:header.write_bytes(raw)
 report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),source_offset=0x3c010,source_end=offset,tiles=193,packed_bytes=len(packed)*4,attribute_words=len(attrs),header_sha256=hashlib.sha256(raw).hexdigest(),limits=['ROM-derived base class0 graphics only. Dynamic actor, hero, HUD font and name-table/VRAM alias updates are outside this atlas.'])
 (ROOT/'analysis/class0_video_assets_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Generated class0 atlas193 tiles and65536 native-endian attribute words.')
 return report

if __name__=='__main__':generate()
