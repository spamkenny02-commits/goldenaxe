"""Original ACB9/AD55 conditional6603 branches and nine ROM strings."""
import hashlib,json
from actor_reference import ROOT
def main():
 source=(ROOT/'input/original.sms').read_bytes();pcs=[0xa7ce,0xac65,0xa852,0xacb5,0xa887,0xace3,0xa077,0xa0e6,0xa17f];text=bytearray();offsets=[]
 for pc in pcs:
  a=0xc000+(pc&0x3fff);offsets.append(len(text));text.extend(source[a:source.index(0,a)+1])
 out='#include <genesis.h>\nconst u8 conditional_house_text[]={'+','.join('0x%02x'%v for v in text)+'};\n'
 out+='const u16 conditional_house_pcs[]={'+','.join(map(str,pcs))+'};\nconst u16 conditional_house_offsets[]={'+','.join(map(str,offsets))+'};\n'
 (ROOT/'megadrive/src/conditional_house_data.c').write_text(out)
 reference=dict(source_sha256=hashlib.sha256(source).hexdigest(),nodes=[[2,0xce,0x25c,0x6614],[2,0xce,0x2e0,0x661c],[2,0xce,0x344,0x6624],[7,0x22,0x2d4,0x6634]],text_pcs=pcs,text_offsets=offsets,native_implemented=True,source_script_entries=[0xacb9,0xad55],story_save_offset=0x27,prerequisite_save_offset=0x22,reward_save_offset=0x47)
 (ROOT/'analysis/conditional_house_reference.json').write_text(json.dumps(reference,indent=2)+'\n')
if __name__=='__main__':main()
