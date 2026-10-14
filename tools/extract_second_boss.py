"""Extract literal type65 direction choice and movement tables."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'input/original.sms').read_bytes()
items=[('second_boss_turns',0x4efb,32),('second_boss_fast',0x4f1b,41),('second_boss_slow',0xa949,41)]
(ROOT/'megadrive/src/second_boss_data.c').write_text('#include <genesis.h>\n'+''.join('const u8 %s[]={%s};\n'%(name,','.join('0x%02x'%v for v in rom[start:start+size])) for name,start,size in items))
