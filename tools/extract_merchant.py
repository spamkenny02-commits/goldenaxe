"""Original-ROM merchant tables and resources; no captured state embedded."""
import json
from actor_reference import ROOT
from extract_title import rle_planes,map_decode

def main():
 r=(ROOT/'input/original.sms').read_bytes();v=bytearray(0x4000)
 start=0x1ee69;end,_=rle_planes(r,start,v,0,4);map_end,tm,_=map_decode(r,end)
 arrays={'merchant_portrait_rle':r[start:end],'merchant_portrait_map':tm[:128]}
 addresses=[('merchant_prompt',0xcb98),('merchant_thanks',0xcbc2),('merchant_poor',0xcbcd),('merchant_owned',0xcbea),('merchant_better',0xcc01),('merchant_full',0xcc45),('merchant_potion_prompt',0xcfe3),('merchant_magic_prompt',0xcffd),('merchant_keys_label',0xfed1),('merchant_feather_label',0xfec3),('merchant_oil_label',0xfeb5)]
 for name,offset in addresses:arrays[name]=r[offset:r.index(0,offset)+1]
 nodes=[]
 for room in range(256):
  pos=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little')
  while r[pos:pos+1]==b'\x01' and r[pos+3:pos+4]==b'\x1e' and r[pos+5:pos+8]==bytes.fromhex('cd9d66'):
   coord=int.from_bytes(r[pos+1:pos+3],'little')
   if r[pos+4]==1:nodes.append([room,((coord&63)+6)*4,(coord>>6)*8])
   pos+=8
 towns=[[r[p],0,r[p+1]] for p in range(0x796a,0x7986,2)]
 towns += [[r[0x752e+n],1,r[0x7533+n]] for n in range(5)]
 towns += [[r[0x75a8+n],2,0] for n in range(4)]
 goods=[];labels=[];label_ids={};prompts=[]
 for group in range(6):
  row=[]
  for n in range(3):
   p=0x7986+group*14+n*4;cpu=int.from_bytes(r[p:p+2],'little');offset=cpu+0x4000
   if cpu not in label_ids:
    label_ids[cpu]=len(labels);labels.append(cpu)
    if cpu==0xbed5:
     # 0818 crosses BFFF into C000/C001. The trailing FF lines advance DE
     # from D660 to1EE0, where writes hit fixed ROM and have no effect.
     # Keep the nine glyphs that are actually written to the tilemap.
     assert r[offset:offset+10]==b'POMME\xffD&OR' and set(r[offset+10:0x10000])=={255}
     data=r[offset:offset+10]+b'\0'
    else:data=r[offset:r.index(0,offset)+1]
    arrays['merchant_label_'+str(label_ids[cpu])]=data
   row.append([r[p+2],r[p+3],label_ids[cpu]])
  goods.append(row)
  prompt=int.from_bytes(r[0x7992+group*14:0x7994+group*14],'little')+0x4000
  arrays['merchant_group_prompt_'+str(group)]=r[prompt:r.index(0,prompt)+1];prompts.append(prompt)
 arrays['merchant_extra_icons']=r[0x12801+27*128:0x12801+29*128]
 arrays['merchant_magic_counts']=r[0x75ac:0x75af];arrays['merchant_magic_prices']=r[0x75af:0x75b2]
 lines=['#include <genesis.h>']
 for name,data in arrays.items():
  lines+=['const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%x for x in data[n:n+16])+',' for n in range(0,len(data),16)]+['};']
 lines+=['const u8 * const merchant_labels[] = {'+','.join('merchant_label_'+str(n) for n in range(len(labels)))+'};',
         'const u8 * const merchant_group_prompts[] = {'+','.join('merchant_group_prompt_'+str(n) for n in range(6))+'};',
         'const u16 merchant_potion_label = '+str(label_ids[0xbed5])+';', 'const u8 merchant_goods[6][3][3] = {']
 lines+=['    {'+','.join('{'+','.join(str(v) for v in item)+'}' for item in row)+'},' for row in goods]+['};']
 for name,rows in [('merchant_nodes',nodes),('merchant_towns',towns)]:
  lines+=['const u8 '+name+'[][3] = {']+['    {'+','.join(str(v) for v in row)+'},' for row in rows]+['};','const u16 '+name+'_count = '+str(len(rows))+';']
 (ROOT/'megadrive/src/merchant_data.c').write_text('\n'.join(lines)+'\n')
 (ROOT/'analysis/merchant_assets.json').write_text(json.dumps(dict(provenance='Original ROM-only slices and declarative tables',portrait_bank=7,portrait_start=start,portrait_end=end,portrait_map_end=map_end,text_offsets=dict(addresses),nodes=nodes,towns=towns,goods=goods,label_cpu_addresses=labels,group_prompt_rom_offsets=prompts,pomme_tail='Only visible nine glyphs; FF advances target into ROM, writes ignored',arrays={k:len(v) for k,v in arrays.items()}),indent=2)+'\n')
if __name__=='__main__':main()
