import hashlib,json
from actor_reference import ROOT
def main():
 s=(ROOT/'input/original.sms').read_bytes();towns=[];prices=[];p=0x6087;price=0
 while p<0x6093:
  town=s[p];p+=1
  if not town:price=s[p];p+=1;continue
  towns.append(town);prices.append(price)
 routes=[]
 for p in range(0x61a8,0x61ba,3):routes.append([s[p],*s[p+9:p+12]])
 p=0xd11e;text=s[p:s.index(0,p)+1]
 out='#include <genesis.h>\n'
 for n,a in [('paid_passage_towns',towns),('paid_passage_prices',prices),('paid_passage_text',text)]:out+='const u8 '+n+'[]={'+','.join(str(v) for v in a)+'};\n'
 out+='const u8 paid_passage_routes[][4]={'+','.join('{'+','.join(map(str,r))+'}' for r in routes)+'};\n'
 (ROOT/'megadrive/src/paid_passage_data.c').write_text(out)
 (ROOT/'analysis/paid_passage_reference.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(s).hexdigest(),room=159,script=0xb19e,pay_handler=0x6036,exit_handler=0x616f,towns=towns,prices=prices,routes=routes,text_pc=0x911e,native_implemented=True),indent=2)+'\n')
if __name__=='__main__':main()
