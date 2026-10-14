"""Export quest-giver strings and original623F tables for the native translation."""
import hashlib,json
from actor_reference import ROOT
def main():
 source=(ROOT/'input/original.sms').read_bytes();pcs=[0xac1e,0xa52f,0x8e5c,0x8e94,0x8ed9,0x8bea,0x8fe3,0x90bf,0x905b];text=bytearray();idx=bytearray();labels=bytearray();labelidx=[0]*27
 strings=[]
 for pc in pcs:
  idx.extend(len(text).to_bytes(2,'little'));a=0xc000+(pc&0x3fff);value=source[a:source.index(0,a)+1];text.extend(value);strings.append(dict(cpu=pc,bytes=len(value)-1))
 for item in [2,3,6,12,22,23,26]:
  labelidx[item]=len(labels);pc=int.from_bytes(source[0x63b3+item*2:0x63b5+item*2],'little');a=0xc000+(pc&0x3fff);labels.extend(source[a:source.index(0,a)+1])
 lines=['#include <genesis.h>']
 for name,data in [('house_quest_text',text),('house_quest_text_index',idx),('house_quest_labels',labels)]:lines+=['const u8 '+name+'[]={']+[' '+','.join('0x%02x'%v for v in data[i:i+16])+',' for i in range(0,len(data),16)]+['};']
 for name,data in [('house_quest_text_pcs',pcs),('house_quest_label_index',labelidx)]:lines+=['const u16 '+name+'[]={'+','.join(str(v) for v in data)+'};']
 lines+=['const u16 house_quest_text_count=9;'];(ROOT/'megadrive/src/house_quest_data.c').write_text('\n'.join(lines)+'\n')
 tables={}
 for pc,count in [(0x62e9,5),(0x62f8,3),(0x624c,5)]:tables[f'{pc:04X}']=[dict(outside=source[pc+n*3],handler=int.from_bytes(source[pc+n*3+1:pc+n*3+3],'little')) for n in range(count)]
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),script_entries=[0xada1,0xadf2,0xaf88],nodes=[dict(room=9,coordinate=0x1e4),dict(room=15,coordinate=0x1d4),dict(room=79,coordinate=0x258)],tables=tables,strings=strings,longest_dialogue_bytes=max(x['bytes'] for x in strings),reward_items=[2,3,6,12,22,23,26],native_implemented=True,full_natural_progression_verified=False)
 (ROOT/'analysis/house_quest_reference.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
