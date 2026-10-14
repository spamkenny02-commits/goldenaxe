"""ROM drop classes with outcomes independent of R; no RNG equivalence claim."""
import hashlib,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    md=ROOT/'gaw-megadrive.bin';rom=ROOT/'input/original.sms';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    baseline=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();cases=[]
    for name,original,occupied in [('first-free',0x78,3),('full',0x78,7),('no-drop',0x66,0)]:
        actors=bytearray(768);actors[0]=1;actors[1]=2;actors[3]=3;actors[7]=original;actors[8]=0xcc;actors[9]=0x90;actors[11]=4;actors[12]=5;actors[13]=4;actors[0x11]=64;actors[0x13]=64
        loot=bytearray(336)
        for slot in range(occupied):
            off=slot*48;loot[off]=8;loot[off+1]=4;loot[off+3]=3;loot[off+14]=200;loot[off+0x11]=32;loot[off+0x13]=32+slot*24;loot[off+8]=0xce;loot[off+9]=0x84
        source=ROOT/f'validation/sms-drop-{name}';target=ROOT/f'validation/md-drop-{name}';points=set(range(3741,3745))
        run(rom,3744,source,points,[(200,220,0)]+PRESSES,ram_writes=[(3741,0x600,bytes(actors)),(3741,0x4b0,bytes(loot)),(3741,0xa2,bytes([1]))])
        run(md,3744,target,points,PRESSES,ram_writes=[(3741,symbols['world_actor_state'],bytes(actors)),(3741,symbols['world_loot_state'],bytes(loot)),(3741,symbols['world_actor_count'],(1).to_bytes(2,'big')),(3741,symbols['vtimer'],int(baseline[0x2f]).to_bytes(4,'big'))])
        for frame in points:
            sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
            for symbol,address,length in [('world_actor_state',0x600,768),('world_loot_state',0x4b0,336)]:
                off=symbols[symbol];assert data[off:off+length]==sms[address:address+length],(name,frame,symbol,[(i,x,y) for i,(x,y) in enumerate(zip(data[off:off+length],sms[address:address+length])) if x!=y][:12])
            off=symbols['world_actor_count'];assert int.from_bytes(data[off:off+2],'big')==sms[0xa2]==0
        first=(source/'ram_03741.bin').read_bytes()[0x4b0:0x600]
        if name=='first-free':assert first[3*48]==11 and first[3*48+0x11]==first[3*48+0x13]==64
        else:assert sum(bool(first[slot*48]) for slot in range(7))==occupied
        cases.append(dict(case=name,original_type=original,occupied_slots=occupied,steps_exact=4))
        assert json.loads((target/'capture.json').read_text())['rom_sha256']==hashlib.sha256(md.read_bytes()).hexdigest()
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=cases,actor_and_loot_bytes_exact=True,scope='Exception classes 9 (always large heart) and 7 (never drop), independent of random byte; first-free/full seven-slot allocation',random_stream_exact=False)
    (ROOT/'validation/drop_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
