"""Live 43..45 state/choice matrices and 70 trajectories in both room classes."""
import hashlib,json,sys
from actor_reference import ROOT
from actor_pair_validation import ActorPair
from validate_actor_ai import random_word


def main():
    pair=ActorPair('dungeon-walkers','--pal' in sys.argv);sy=pair.sy
    def record(t,state,d=0,counter=0,pose=0,x=120,y=80):
        e=bytearray(48);e[:5]=bytes([t,state,6,0x28,counter])
        e[8:10]=bytes.fromhex('0291');e[10:14]=bytes([d,pose,2,10])
        e[0x11]=y;e[0x13]=x;e[0x18]=64
        return e
    cases=[record(t,s,d,c,p) for t in [0x43,0x44,0x45]
           for s,c,p in [(2,0,2),(6,0,0),(8,3,0),(10,3,0)] for d in range(4)]
    sw=[];tw=[];frames=set()
    for batch in range(6):
        f=3102+batch;data=b''.join(cases[batch*8:batch*8+8])+bytes(384)
        sw.append((f,0x600,data));tw.append((f,sy['world_actor_state'],data));frames.add(f)
    pair.compare(pair.execute(False,'matrix',frames,sw),pair.execute(True,'matrix',frames,tw),frames,range(16),'matrix')
    print('48 nonrandom state/direction cases OK',flush=True)
    sw=[];tw=[];frames=set()
    blocked=[record(t,s,d) for t in [0x43,0x44,0x45] for s in [8,10] for d in range(4)]
    for batch in range(3):
        f=3102+batch;data=b''.join(blocked[batch*8:batch*8+8])+bytes(384)
        sw += [(f,0x600,data),(f,0x1600,bytes([0,0xa0])*768)]
        tw += [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,bytes([0,0xa0])*768)]
        frames.add(f)
    pair.compare(pair.execute(False,'blocked',frames,sw),pair.execute(True,'blocked',frames,tw),frames,range(16),'blocked')
    print('24 blocked-direction cases OK',flush=True)
    sw=[];frames=set();fixtures={}
    targets=[(32,80),(216,80),(120,32),(120,144),(152,112),(120,80)]
    for t in [0x43,0x44,0x45]:
        for state in [2,4,8,10]:
            for hx,hy in targets:
                for d in range(4):
                    f=3102+len(fixtures);data=bytes(record(t,state,d,pose=3 if state==2 else 0))+bytes(720)
                    fixtures[f]=(t,state,hx,hy,data)
                    sw += [(f,0x600,data),(f,0x1600,bytes(1536)),(f,0x1b,b'\0'),
                           (f,0x312,(hx<<8).to_bytes(2,'little')),(f,0x310,(hy<<8).to_bytes(2,'little'))]
                    frames.add(f)
    source=pair.execute(False,'choices',frames,sw);tw=[];decisions=[]
    for f in sorted(frames):
        t,state,hx,hy,data=fixtures[f];e=source[f][:48]
        if state in [2,4]: valid=lambda q:q&3==e[10]
        elif state==8: valid=lambda q:(6 if q&15<4 else 10)==e[1]
        else: valid=lambda q:(4 if q&15<10 else 6)==e[1]
        seed=next(n for n in range(1,65536) if valid(random_word(n)))
        tw += [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,bytes(1536)),
               (f,sy['hero_x'],(hx<<8).to_bytes(2,'big')),(f,sy['hero_y'],(hy<<8).to_bytes(2,'big')),
               (f,sy['randbase'],seed.to_bytes(2,'big'))]
        decisions.append(dict(type=t,state=state,next_state=e[1],direction=e[10],shot=source[f][384]==0x70))
    pair.compare(source,pair.execute(True,'choices',frames,tw),frames,range(16),'observed choices')
    assert any(d['shot'] for d in decisions)
    assert not any(d['shot'] for d in decisions if d['type']==0x43)
    print('288 source-observed RNG choices and aimed-axis decisions OK',flush=True)
    culls=[]
    for room_class in [0,1]:
        data=bytes(384)+b''.join(record(0x70,0,d) for d in range(4))+bytes(192)
        frames=set(range(3102,3234))
        sw=[(3102,0x600,data),(3102,0xba,bytes([room_class]))]
        tw=[(3102,sy['world_actor_state'],data),(3102,sy['actor_room_class'],room_class.to_bytes(2,'big'))]
        a=pair.execute(False,f'flight-{room_class}',frames,sw);b=pair.execute(True,f'flight-{room_class}',frames,tw)
        pair.compare(a,b,frames,range(8,12),'70 free flight')
        culls += [dict(room_class=room_class,slot=slot,frame=next(f for f in sorted(frames) if not a[f][slot*48])) for slot in range(8,12)]
    print('8 projectile70 trajectories through original culls OK',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                deterministic_cases=48,blocked_cases=24,controlled_decisions=decisions,
                projectile_culls=culls,record_comparisons=pair.comparisons,
                original_rng_stream_verified=False,natural_dungeon_progression_verified=False,
                collision_descriptor_bytes_excluded=[27,28])
    (ROOT/f'validation/dungeon_walkers{pair.suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
