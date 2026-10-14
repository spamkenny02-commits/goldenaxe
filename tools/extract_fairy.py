"""Original602A capacity contexts, two texts/labels and original reward icons."""
import hashlib,json
from actor_reference import ROOT
from extract_title import rle_planes
def main():
 s=(ROOT/'input/original.sms').read_bytes();arrays={};pcs=[0x9021,0x9035];labels=[]
 for name,pc in zip(['fairy_life_text','fairy_magic_text'],pcs):
  p=0xc000+(pc&0x3fff);arrays[name]=s[p:s.index(0,p)+1]
 for name,item in [('fairy_life_label',42),('fairy_magic_label',28)]:
  pc=int.from_bytes(s[0x63b3+item*2:0x63b5+item*2],'little');p=0xc000+(pc&0x3fff);arrays[name]=s[p:s.index(0,p)+1];labels.append(pc)
 icon=bytearray(128);end,_=rle_planes(s,0x13bb9,icon,0,4);arrays['fairy_heart_icon']=bytes(icon);arrays['fairy_magic_icon']=s[0x12801+28*128:0x12801+29*128]
 records=[];p=0x602a;kind=0
 while p<0x6036:
  town=s[p];p+=1
  if not town:kind=s[p];p+=1;continue
  records.append([town,kind])
 arrays['fairy_towns']=bytes(t for t,k in records);arrays['fairy_kinds']=bytes(k for t,k in records)
 (ROOT/'megadrive/src/fairy_data.c').write_text('#include <genesis.h>\n'+''.join('const u8 '+n+'[]={'+','.join('0x%02x'%v for v in a)+'};\n' for n,a in arrays.items()))
 (ROOT/'analysis/fairy_reference.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(s).hexdigest(),room=175,script=0xb205,handler=0x5fc7,coordinate=0x25c,records=records,text_pcs=pcs,label_pcs=labels,heart_rle_start=0x13bb9,heart_rle_end=end,magic_icon_start=0x12801+28*128,native_implemented=True),indent=2)+'\n')
if __name__=='__main__':main()
