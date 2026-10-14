"""Service/save resources from known source routines 7390, 77B7 and 782C."""
import json
from actor_reference import ROOT
from extract_title import rle_planes,map_decode

def main():
 r=(ROOT/'input/original.sms').read_bytes();v=bytearray(0x4000)
 end,_=rle_planes(r,0x124fc,v,0x1400,4)
 pos=int.from_bytes(r[0x1eb2b:0x1eb2d],'little')+0x14000
 pe,_=rle_planes(r,pos,v,0,4);me,tm,_=map_decode(r,pe)
 arrays={'save_font_rle':r[0x124fc:end],'save_portrait_rle':r[pos:pe],'save_portrait_map':tm[:128],'save_text_charset':r[0xca94:0xcae4],'save_cursor_frame':r[0x7383:0x7390],'save_colors':r[0x73d5:0x73dd]}
 for name,a in [('save_prompt',0xcd70),('save_select_text',0xcda7),('save_done_text',0xcddd),('save_decline_text',0xcdb6),('save_continue_text',0x1fe26)]:arrays[name]=r[a:r.index(0,a)+1]
 nodes=[]
 for room in range(256):
  pos=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little')
  while r[pos:pos+1]==b'\x01' and r[pos+3:pos+4]==b'\x1e' and r[pos+5:pos+8]==bytes.fromhex('cd9d66'):
   coord=int.from_bytes(r[pos+1:pos+3],'little')
   if r[pos+4]==0:nodes.append([room,((coord&63)+6)*4,(coord>>6)*8])
   pos+=8
 lines=['#include <genesis.h>']
 for name,data in arrays.items():lines+=['const u8 %s[] = {'%name]+['    '+','.join('0x%02x'%b for b in data[n:n+16])+',' for n in range(0,len(data),16)]+['};']
 lines+=['const u8 save_nodes[][3] = {']+['    {'+','.join(str(v) for v in row)+'},' for row in nodes]+['};','const u16 save_nodes_count = '+str(len(nodes))+';']
 (ROOT/'megadrive/src/save_data.c').write_text('\n'.join(lines)+'\n')
 (ROOT/'analysis/save_assets.json').write_text(json.dumps(dict(source='ROM-only service UI resources and unconditional669D prefixes',portrait_rom_offset=int.from_bytes(r[0x1eb2b:0x1eb2d],'little')+0x14000,portrait_rle_end=pe,portrait_map_end=me,nodes=nodes,arrays={k:len(v) for k,v in arrays.items()}),indent=2)+'\n')
if __name__=='__main__':main()
