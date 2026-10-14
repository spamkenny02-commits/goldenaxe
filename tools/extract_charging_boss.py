"""Literal pursuit vectors, charge vectors/facing and eight-way lookup."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'input/original.sms').read_bytes()
items=[('charging_boss_walk',0x548a,33),('charging_boss_vectors',0x54ab,32),('charging_boss_facing',0x54cb,8),('charging_boss_chase',0x57db,16)]
(ROOT/'megadrive/src/charging_boss_data.c').write_text('#include <genesis.h>\n'+''.join('const u8 %s[]={%s};\n'%(name,','.join('0x%02x'%v for v in rom[start:start+size])) for name,start,size in items))
