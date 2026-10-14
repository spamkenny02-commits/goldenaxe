"""Export original card tables, confirmation glyphs and nine dialogue strings."""
import hashlib,json
from actor_reference import ROOT
def main():
 source=(ROOT/'input/original.sms').read_bytes();pcs=[0xb90e,0xb930,0xb94d,0xb95f,0xb982,0xb9bf,0xb9d7,0xba20,0xba8e]
 arrays={'minigame_weights':source[0x6776:0x6796],'minigame_pairs':source[0x6796:0x67a2],'minigame_inverse':source[0x67f9:0x6809],'minigame_lucky':source[0x6801:0x6809],'minigame_scores':source[0x68c3:0x68c7],'minigame_coordinates':source[0x68ec:0x68f6],'minigame_confirm_words':source[0x614e:0x6160]}
 arrays['minigame_confirm_font']=b''.join(source[0xc7c6+(c-65)*8:0xc7c6+(c-65)*8+8] for c in b'OUIN')
 texts=[];offsets=[]
 for pc in pcs:
  a=0xc000+(pc&0x3fff);offsets.append(len(texts));texts.extend(source[a:source.index(0,a)+1])
 arrays['minigame_text']=bytes(texts)
 out='#include <genesis.h>\n'+''.join('const u8 '+name+'[]={'+','.join('0x%02x'%v for v in data)+'};\n' for name,data in arrays.items())
 out+='const u16 minigame_text_index[]={'+','.join(map(str,offsets))+'};\n'
 (ROOT/'megadrive/src/minigame_data.c').write_text(out)
 reference=dict(source_sha256=hashlib.sha256(source).hexdigest(),entry_room=95,game_room=11,entry_script=0xb00a,entry_handler=0x66b5,dispatch=0x66f6,cost=10,text_pcs=pcs,text_offsets=offsets,weights=list(arrays['minigame_weights']),pairs=list(arrays['minigame_pairs']),scores=list(arrays['minigame_scores']),rng_exact=False,native_implemented=True)
 (ROOT/'analysis/minigame_reference.json').write_text(json.dumps(reference,indent=2)+'\n')
if __name__=='__main__':main()
