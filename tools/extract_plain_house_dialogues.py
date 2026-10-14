"""Extract linear immediate667E call operands and original context text tables."""
import hashlib,json
from actor_reference import ROOT
from extract_room_clear import z80
def main():
 source=(ROOT/'input/original.sms').read_bytes();nodes=[]
 for room in range(256):
  p=int.from_bytes(source[0xb762+room*2:0xb764+room*2],'little');bc=de=None
  if p<0x8000:continue
  for _ in range(128):
   ins=z80.decode(source[p:p+8],p);raw=source[p:p+ins.len]
   if not raw or raw[0] in [0xc9,0xc3,0x18,0xe9]:break
   if raw[0]==1:bc=int.from_bytes(raw[1:3],'little')
   elif raw[0]==0x11:de=int.from_bytes(raw[1:3],'little')
   elif raw[0]==0xcd:
    if raw[1:]==bytes.fromhex('7e66'):
     assert bc is not None and de is not None;nodes.append((room,bc,de,p))
    bc=de=None
   p+=ins.len
 ends={x[2] for x in nodes};records=[]
 for room,coordinate,table,site in nodes:
  p=table;n=0
  while p==table or p not in ends:
   outside=source[p];pc=int.from_bytes(source[p+1:p+3],'little')
   if outside<16 or outside&15==15 or not 0x8000<=pc<0xc000:break
   a=0xc000+(pc&0x3fff);end=source.find(0,a,0x10000);assert end>=0
   records.append(dict(room=room,coordinate=coordinate,outside=outside,text_pc=pc,text_bytes=end-a,table=table,call_site=site));p+=3;n+=1;assert n<256
 assert len(nodes)==21 and len(records)==65
 text=bytearray();offsets={};rows=[];legacy=[0x9acc,0x9b3d,0x9b72,0x9bc5,0x9bfe,0x9c09]
 for n,r in enumerate(records):
  pc=r['text_pc']
  if pc not in offsets:
   offsets[pc]=len(text);a=0xc000+(pc&0x3fff);text.extend(source[a:source.index(0,a)+1])
  rows.append([r['room'],r['coordinate'],r['outside'],offsets[pc],legacy.index(pc) if pc in legacy else n+6])
 lines=['#include <genesis.h>','const u8 plain_house_text[]={']+[' '+','.join('0x%02x'%v for v in text[i:i+16])+',' for i in range(0,len(text),16)]+['};','const u16 plain_house_dialogues[][5]={']+[' {'+','.join(map(str,r))+'},' for r in rows]+['};','const u16 plain_house_dialogue_count='+str(len(rows))+';']
 (ROOT/'megadrive/src/plain_house_data.c').write_text('\n'.join(lines)+'\n')
 report=dict(nodes=nodes,contexts=records,plain_handler=0x667e,full_game_ported=False,source_sha256=hashlib.sha256(source).hexdigest(),native_implemented=True,unique_texts=len(offsets),native_text_bytes=len(text),limits=['Linear immediate BC/DE operands only; every call invalidates tracked registers, scanning stops at unconditional control flow.','Finite context rows stop at another known table or invalid outside/text pointer. Independent original667E tests validate every exported selection, not all quest reachability.'])
 (ROOT/'analysis/plain_house_dialogue_reference.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
