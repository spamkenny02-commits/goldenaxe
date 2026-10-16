"""Instruction-count model for title RAM map decoders 0BD3 / 0BFE."""
from actor_loading_cost import rle_cost

def map_cost(rom,source,destination):
 start=source;total=11+10;scratch=bytearray()
 while True:
  command=rom[source];source+=1;total+=7+6+4
  if not command:total+=12;break
  total+=7+10;count=(command&127) or 256
  if command&128:
   total+=7+4
   for i in range(count):
    scratch.append(rom[source]);source+=1;total+=7+7+6+6+(13 if i+1<count else 8)
   total+=12
  else:
   total+=4+7;value=rom[source];source+=1
   for i in range(count):scratch.append((value+i)&255);total+=7+6+4+(13 if i+1<count else 8)
   total+=6+12
 total+=10+11+10+17
 # 0BFE helper, command stream is the first decoder's reconstructed bytes.
 total+=7+4;cursor=0;decoded=bytearray(1536)
 for plane in range(2):
  dst=destination+plane;total+=11+11
  while True:
   command=scratch[cursor];cursor+=1;total+=7+4
   if not command:total+=12;break
   total+=7+10;count=(command&127) or 256;literal=bool(command&128)
   total+=7+4 if literal else 4+6
   for i in range(count):
    value=scratch[cursor]
    if literal:total+=6+7;cursor+=1
    else:total+=7
    decoded[dst-destination]=value;total+=7+4+4+4
    total+=12 if (dst&255)+2<256 else 7+4
    dst+=2;total+=13 if i+1<count else 8
   cursor+=0 if literal else 1;total+=6+12
  total+=10+10+6+6+(13 if plane==0 else 8)
 total+=10+10+10
 return dict(tstates=total,source_end=source,packed_bytes=source-start,decoded_bytes=len(decoded),scratch_bytes=len(scratch))


def ldir_cost(count):
 return (count-1)*21+16

def fill_words_cost(words):
 chunks=(words+255)//256
 total=59+4+4+(12 if words%256==0 else 7+4)
 return total+words*67-chunks*5+(chunks-1)*13+8+10

def upload_cost(byte_count):
 chunks=(byte_count+255)//256
 return 59+4+4+(12 if byte_count%256==0 else 7+4)+4+4+7+byte_count*32-chunks*5+chunks*(4+12)-5+10

def title_cost(rom):
 rle=rle_cost(rom,0x1c010,0x4000)
 first=map_cost(rom,rle['source_end'],0xd600)
 second=map_cost(rom,first['source_end'],0xc900)
 # 0B56..0B91: registers, two word-fill calls, visible map and palette LDIRs.
 clear=(10+59+4+59+10+16+10+10+17+fill_words_cost(32)
        +10+10+10+17+fill_words_cost(896)+16+10+10+10+ldir_cost(1534)
        +10+10+10+7+ldir_cost(31)+10)
 # 1473..1487: stack/bank selection and first sixteen palette bytes.
 setup=20+7+13+10+10+10+ldir_cost(16)
 assets=10+17+rle['tstates']+10+17+first['tstates']+10+17+second['tstates']
 # 1499..14CF: palette selection, initial colors, and 1536-byte tilemap upload.
 tail=(10+7+10*(15+6+6)+9*13+8+7+13+10+10+16+16
       +4+13+10+10+10+7+ldir_cost(9)+10+10+10+17+upload_cost(1536))
 return dict(clear_tstates=clear,setup_tstates=setup,assets_tstates=assets,tail_tstates=tail,
             foreground_tstates=clear+setup+assets+tail,
             resources=[rle,first,second])
