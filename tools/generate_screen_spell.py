"""Export ROM-only assets for both 6AFB/6C2E full-screen magic levels."""
import json,hashlib
from pathlib import Path
from extract_title import rle_planes
ROOT=Path(__file__).resolve().parents[1]
def main():
    rom=(ROOT/'input/original.sms').read_bytes();arrays={}
    for level,start in [(1,0x1633b),(2,0x16d48)]:
        buf=bytearray(16384);end,size=rle_planes(rom,start,buf,0,4)
        arrays[f'screen_spell_patterns{level}']=buf[:size]
    arrays.update(screen_spell_grid=rom[0x6bf6:0x6c22],screen_spell_cells1=rom[0x16293:0x1633b],screen_spell_blocks=rom[0x6cf0:0x6d2c],screen_spell_cells2=rom[0x16800:0x16d48],screen_spell_hero_bitmap=rom[0x12241:0x122d2])
    lines=['/* Original 30A7/6AFB/6C2E assets; no captured states. */']
    for name,data in arrays.items():
        lines+=['static const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%x for x in data[n:n+16])+',' for n in range(0,len(data),16)]+['};']
    raw=('\r\n'.join(lines)+'\r\n').encode();path=ROOT/'megadrive/src/screen_spell_assets.inc'
    if not path.exists() or path.read_bytes()!=raw:path.write_bytes(raw)
    (ROOT/'analysis/screen_spell_assets.json').write_bytes((json.dumps(dict(source_sha256=hashlib.sha256(rom).hexdigest(),arrays={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in arrays.items()},captured_states_used=False),indent=2)+'\n').encode())
    print('Both source full-screen spell assets exported.')
if __name__=='__main__':main()
