"""Export original ending references; no rendered or recorded substitutions."""
import hashlib,json
from actor_reference import ROOT
def main():
 source=(ROOT/'input/original.sms').read_bytes()
 end=int.from_bytes(source[0xcae4:0xcae6],'little');count=int.from_bytes(source[0xcae6:0xcae8],'little')
 assert count==80 and source[0xcae8]==0xb0
 arrays=dict(ending_text=source[0x3334e:0x3384e]+bytes(1),ending_credit_glyphs=source[0xc000+(end&0x3fff)-count+1:0xc000+(end&0x3fff)+1])
 def sprite(address,base=0):
  data=source[0x30000+(address&0x3fff):];count=data[0]&127
  frame=bytearray([count])+bytearray(data[3:3+count*3])
  for n in range(count):frame[1+count+n*2+1]=(frame[1+count+n*2+1]+base)&255
  return bytes(frame)
 arrays.update(ending_held_frame=sprite(0x84b3),ending_axe_frame=sprite(0x84eb,0xbc),ending_held_bitmap=source[0x12241:0x12241+145],ending_gem_bitmap=source[0x12a81:0x12b01])
 lines=['#include <genesis.h>']
 for name,data in arrays.items():
  lines+=['const u8 '+name+'[]={']+[' '+','.join('0x%02x'%v for v in data[i:i+16])+',' for i in range(0,len(data),16)]+['};']
 (ROOT/'megadrive/src/ending_data.c').write_text('\n'.join(lines)+'\n')
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),entry=0x6ebe,credits_row_entry=0x7061,credits_scroll_entry=0x7027,text_physical_address=0x3334e,text_bytes=1280,glyph_end_cpu=end,glyph_count=count,arrays={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in arrays.items()},production_ending_integrated=True)
 (ROOT/'analysis/ending_assets.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
