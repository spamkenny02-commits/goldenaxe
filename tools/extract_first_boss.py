"""Extract literal movement/attack data; executable behavior stays native C."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'input/original.sms').read_bytes()
items=[('first_boss_movement',0x87cd,17),('first_boss_aimed',0x4405,38),('first_boss_fan',0x443d,26)]
(ROOT/'megadrive/src/first_boss_data.c').write_text('#include <genesis.h>\n'+''.join('const u8 %s[]={%s};\n'%(name,','.join('0x%02x'%v for v in rom[start:start+size])) for name,start,size in items))
