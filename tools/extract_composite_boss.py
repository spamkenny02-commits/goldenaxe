"""Three five-position formations from bank2 AB1C..AB3F."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rom=(ROOT/'input/original.sms').read_bytes();data=bytearray()
for i in range(3):
 start=int.from_bytes(rom[0xab1c+i*2:0xab1e+i*2],'little');data.extend(rom[start:start+10])
(ROOT/'megadrive/src/composite_boss_data.c').write_text('#include <genesis.h>\nconst u8 composite_boss_positions[]={'+','.join('0x%02x'%v for v in data)+'};\n')
