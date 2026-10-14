"""Fixed-ROM55D0 movement,468E shot and4745 satellite path literals."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'input/original.sms').read_bytes()
(ROOT/'megadrive/src/sword_boss_data.c').write_text('#include <genesis.h>\n'+''.join('const u8 %s[]={%s};\n'%(name,','.join('0x%02x'%v for v in rom[start:start+size])) for name,start,size in [('sword_boss_walk',0x55d0,33),('sword_boss_shot',0x468e,38),('sword_boss_paths',0x4745,0xb2)]))
