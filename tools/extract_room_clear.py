"""Decode room-script call sites; emit native clear-event metadata, no Z80 runtime."""
import hashlib,json,sys
from actor_reference import ROOT
sys.path.insert(0,str(ROOT.parents[1]/'work/z80dis'))
from z80dis import z80

def extract(r):
    records=[]
    for room in range(512):
        entry=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little')
        p=entry;e=None;event=None
        if entry==0x5d4c:event=(1,entry)
        elif entry>=0x8000:
            for _ in range(64):
                if r[p] in (0xc9,0xc3,0x18,0xe9):break
                if r[p]==0x1e:e=r[p+1]
                if r[p]==0xcd:
                    target=int.from_bytes(r[p+1:p+3],'little')
                    if target==0x5d4c:event=(1,p)
                    elif target==0x5eb1:
                        assert e in (0,1,2,3),(room,e)
                        event=(2 if e<2 else e+1,p)
                ins=z80.decode(r[p:p+8],p);assert ins.len;p+=ins.len
            else:raise AssertionError(hex(entry))
        if event:records.append(dict(room=room,entry=entry,call_site=event[1],kind=event[0]))
    assert len(records)==49 and all(x['room']>=256 for x in records)
    return records

def extract_rewards(r):
    records=[];targets={0x5e75:5,0x5e9c:6,0x5fb1:7}
    for room in range(512):
        entry=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little');p=entry;event=None
        if entry in targets:event=(targets[entry],entry)
        elif entry>=0x8000:
            for _ in range(64):
                if r[p] in (0xc9,0xc3,0x18,0xe9):break
                if r[p]==0xcd:
                    target=int.from_bytes(r[p+1:p+3],'little')
                    if target in targets:event=(targets[target],p)
                ins=z80.decode(r[p:p+8],p);assert ins.len;p+=ins.len
            else:raise AssertionError(hex(entry))
        if event:records.append(dict(room=room,entry=entry,call_site=event[1],kind=event[0]))
    assert len(records)==20
    return records

def extract_completions(r):
    records=[]
    for room in range(256,512):
        entry=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little');p=entry;event=None
        if entry==0x5ecd:event=(9,entry)
        elif entry>=0x8000:
            for _ in range(64):
                if r[p] in (0xc9,0xc3,0x18,0xe9):break
                if r[p]==0xcd:
                    target=int.from_bytes(r[p+1:p+3],'little')
                    if target in (0x5f0d,0x5ecd):event=(8 if target==0x5f0d else 9,p)
                ins=z80.decode(r[p:p+8],p);assert ins.len;p+=ins.len
        if event:records.append(dict(room=room,entry=entry,call_site=event[1],kind=event[0]))
    assert len(records)==27
    return records

def extract_shutters(r):
    records=[]
    for room in range(256,512):
        entry=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little');p=entry;e=None
        if entry<0x8000:continue
        for _ in range(64):
            if r[p] in (0xc9,0xc3,0x18,0xe9):break
            if r[p]==0x1e:e=r[p+1]
            if r[p:p+3]==bytes.fromhex('cd2b5f'):
                assert e in (0,1,2,3)
                records.append(dict(room=room,entry=entry,call_site=p,direction=e))
            ins=z80.decode(r[p:p+8],p);assert ins.len;p+=ins.len
    assert len(records)==13
    return records

def main():
    r=(ROOT/'input/original.sms').read_bytes();records=extract(r)+extract_rewards(r)+extract_completions(r);shutters=extract_shutters(r)
    kinds={x['room']:x['kind'] for x in records}
    lines=['/* Generated source room-clear dispatch: 1 all, 2 top, 3 left, 4 right; 5/6/7 clear rewards. */','static const u8 world_room_clear_kind[512] = {']
    for start in range(0,512,16):lines.append('    '+','.join(str(kinds.get(n,0)) for n in range(start,start+16))+',')
    lines+=['};','static const u8 world_room_shutter_direction[256] = {']
    directions={x['room']:x['direction']+1 for x in shutters}
    for start in range(256,512,16):lines.append('    '+','.join(str(directions.get(n,0)) for n in range(start,start+16))+',')
    lines+=['};'];(ROOT/'megadrive/src/room_clear.inc').write_text('\n'.join(lines)+'\n')
    (ROOT/'analysis/room_clear_reference.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(r).hexdigest(),records=records,shutters=shutters,other_script_events_ported=False),indent=2)+'\n')
    print('Room-clear passage handlers:',len(records))
if __name__=='__main__':main()
