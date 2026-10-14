"""Extract the source 3441 fast normal-ground movement table."""
import hashlib,json
from actor_reference import ROOT

def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    data=rom[0x3441:0x3452]
    assert len(data)==17 and data[0]==4
    p=ROOT/'megadrive/src/fast_ground_data.c'
    p.write_text('#include <genesis.h>\nconst u8 world_fast_ground_walk[] = { '+','.join(hex(v) for v in data)+' };\n')
    (ROOT/'analysis/fast_ground_resources.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(rom).hexdigest(),ranges={'world_fast_ground_walk':[[0x3441,0x3452]]},resource_bytes=17,generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2)+'\n')
if __name__=='__main__':main()
