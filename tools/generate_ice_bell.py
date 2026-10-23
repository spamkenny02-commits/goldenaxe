"""Extract untouched exterior metatiles and source bell passage list."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def decode(rom,pos,planes):
    out=bytearray(16384)
    for plane in range(planes):
        address=plane
        while True:
            command=rom[pos];pos+=1
            if not command:break
            count=(command&127) or 256
            for _ in range(count):
                out[address]=rom[pos];address+=planes
                if command&128:pos+=1
            if not command&128:pos+=1
    return pos,out

def main():
    rom=(ROOT/'input/original.sms').read_bytes();end,_=decode(rom,0x3c010,4);_,meta=decode(rom,end,2)
    animation_start=0x2c000+(int.from_bytes(rom[0x1759:0x175b],'little')&0x3fff)
    _,animation=decode(rom,animation_start,4)
    arrays=dict(exterior_water_bitmaps=animation[:512],ice_bell_metatiles=meta[0x1c0:0x1c8]+meta[0x1f0:0x1f8],ice_bell_passages=rom[0x1a79:0x1a7c])
    lines=['/* ROM class0 RLE metatiles38/3E before1A30, and1A79 passage rooms. */']
    for name,data in arrays.items():lines+=['static const u8 '+name+'[] = {', '    '+','.join('0x%02x'%x for x in data),'};']
    raw=('\r\n'.join(lines)+'\r\n').encode();p=ROOT/'megadrive/src/ice_bell_assets.inc'
    if not p.exists() or p.read_bytes()!=raw:p.write_bytes(raw)
    (ROOT/'analysis/ice_bell_assets.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(rom).hexdigest(),arrays={k:dict(bytes=len(v),hex=v.hex()) for k,v in arrays.items()},captured_states_used=False),indent=2)+'\n')
    print('Original ice bell metatiles/passages exported')

if __name__=='__main__':main()
