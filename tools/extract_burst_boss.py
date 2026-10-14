"""Type74 eight-way projectile initializer/facing literals."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'input/original.sms').read_bytes()
(ROOT/'megadrive/src/burst_boss_data.c').write_text('#include <genesis.h>\n'+''.join('const u8 %s[]={%s};\n'%(name,','.join('0x%02x'%v for v in rom[start:start+size])) for name,start,size in [('burst_boss_shot_template',0x44f2,38),('burst_boss_shot_facing',0x44ea,8)]))
