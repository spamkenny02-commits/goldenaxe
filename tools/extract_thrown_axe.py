"""Extract fixed-ROM axe descriptors and original bank-5 water poses."""
import hashlib,json
from actor_reference import ROOT

def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    ranges={'world_axe_velocity':[(0x3a1f,0x3a27)],'world_axe_descriptors':[(0x3d8d,0x3da5)],'world_terrain_records':[(0x2530,0x257d)],'world_water_walk':[(0x340e,0x341f),(0x3474,0x3485)],'world_water_bitmaps':[]}
    for i in range(8):
        address=int.from_bytes(rom[0x3d67+i*2:0x3d69+i*2],'little');a=0x14000+(address&0x3fff)
        assert rom[a]==4;ranges['world_water_bitmaps'].append((a,a+97))
    arrays={k:b''.join(rom[a:b] for a,b in values) for k,values in ranges.items()}
    p=ROOT/'megadrive/src/thrown_axe_data.c'
    p.write_text('#include <genesis.h>\n'+''.join('const u8 '+k+'[] = { '+','.join(hex(v) for v in data)+' };\n' for k,data in arrays.items()))
    (ROOT/'analysis/thrown_axe_resources.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(rom).hexdigest(),ranges=ranges,resource_bytes={k:len(v) for k,v in arrays.items()},generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2)+'\n')
if __name__=='__main__':main()
