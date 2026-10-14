"""Compare guarded versus direct projectile allocation under real hardware overflow from actor fixtures."""
import hashlib,json,sys
from actor_reference import ROOT
from actor_pair_validation import ActorPair


def main():
    pair=ActorPair('overflow-allocation','--pal' in sys.argv);sy=pair.sy
    sw=[];tw=[];frames=set();cases=[]
    template=bytearray((ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630])
    for t in [0x20,0x2a,0x40,0x38,0x42]:
        for dense in [False,True]:
            start=3102+len(cases)*8;f=start+4
            e=bytearray(48);e[:5]=bytes([t,6 if t==0x42 else 10,6,0x28,120])
            e[8:10]=bytes.fromhex('428e');e[12:14]=bytes([2,7])
            e[0x11]=80;e[0x13]=120;e[0x18]=64
            data=bytearray(768);data[:48]=e
            for slot in range(1,6 if dense else 1):
                frozen=bytearray(template);frozen[3]=1;frozen[4]=120;frozen[5]=0;frozen[6]=255
                frozen[0x10:0x18]=bytes(8);frozen[0x11]=64;frozen[0x13]=80
                data[slot*48:(slot+1)*48]=frozen
            e[4]=0
            sw += [(start,0x600,bytes(data)),(start,0x1600,bytes(1536)),(f,0x600,bytes(e))]
            tw += [(start,sy['world_actor_state'],bytes(data)),(start,sy['sms_vram']+0x3800,bytes(1536)),(f,sy['world_actor_state'],bytes(e))]
            cases.append(dict(frame=f,type=t,dense=dense,guarded=t in [0x20,0x2a,0x40]))
            frames.add(f)
    source=pair.execute(False,'status',frames,sw)
    native=pair.execute(True,'status',frames,tw)
    pair.compare(source,native,frames,range(16),'overflow allocation')
    for case in cases:
        f=case['frame'];types=list(source[f][384::48]);case['projectile_types']=types
        blocked=case['guarded'] and case['dense']
        assert any(types)!=blocked,case
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                cases=cases,record_comparisons=pair.comparisons,
                explicit_test_status_ram_writes=False, frozen_actor_ram_fixtures=True,guarded_and_direct_paths_verified=True)
    (ROOT/f'validation/overflow_allocation{pair.suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(cases)} allocation cases, {pair.comparisons} record comparisons')


if __name__=='__main__':main()
