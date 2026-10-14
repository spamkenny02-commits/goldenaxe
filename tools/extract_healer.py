"""Original bank7 healer portrait and bank3 service texts, Z80 7685."""
import json
from actor_reference import ROOT
from extract_title import rle_planes,map_decode
def main():
 r=(ROOT/'input/original.sms').read_bytes();v=bytearray(0x4000);start=0x1f0f1
 end,_=rle_planes(r,start,v,0,4);map_end,tm,_=map_decode(r,end)
 arrays={'healer_portrait_rle':r[start:end],'healer_portrait_map':tm[:128]}
 for name,offset in [('healer_free_prompt',0xcd3f),('healer_paid_prompt',0xcc7b),('healer_decline',0xccc7),('healer_done',0xccf5)]:arrays[name]=r[offset:r.index(0,offset)+1]
 nodes=[]
 for room in range(256):
  pos=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little')
  while r[pos:pos+1]==b'\x01' and r[pos+3:pos+4]==b'\x1e' and r[pos+5:pos+8]==bytes.fromhex('cd9d66'):
   coord=int.from_bytes(r[pos+1:pos+3],'little')
   if r[pos+4]==2:nodes.append([room,((coord&63)+6)*4,(coord>>6)*8])
   pos+=8
 prices=[list(r[p:p+2]) for p in range(0x7700,0x7716,2)]
 lines=['#include <genesis.h>']
 for name,data in arrays.items():lines+=['const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%x for x in data[n:n+16])+',' for n in range(0,len(data),16)]+['};']
 for name,rows,width in [('healer_nodes',nodes,3),('healer_prices',prices,2)]:
  lines+=['const u8 '+name+'[]['+str(width)+'] = {']+['    {'+','.join(str(v) for v in row)+'},' for row in rows]+['};','const u16 '+name+'_count = '+str(len(rows))+';']
 (ROOT/'megadrive/src/healer_data.c').write_text('\n'.join(lines)+'\n')
 (ROOT/'analysis/healer_assets.json').write_text(json.dumps(dict(provenance='Original ROM-only resources; unconditional service prefixes only',portrait_start=start,portrait_end=end,portrait_map_end=map_end,price_table_rom_offset=0x7700,first_village_price=0,nodes=nodes,prices=prices,arrays={k:len(v) for k,v in arrays.items()}),indent=2)+'\n')
if __name__=='__main__':main()
