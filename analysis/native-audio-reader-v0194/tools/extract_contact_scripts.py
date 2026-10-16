"""Inventory original contact-gated room scripts before native translation.

Only explicit immediate operands are propagated. Every call invalidates them;
this avoids inventing values across a routine with unknown register clobbers.
"""
import hashlib,json
from extract_room_clear import ROOT,z80
TARGETS={0x5c96:'stationary_up_passages',0x5cc7:'stationary_up_cell',0x5cec:'empty_cell_passages',0x5cfb:'moving_aligned_portal'}

def extract(r,targets=None):
    targets=TARGETS if targets is None else targets
    result=[]
    for room in range(512):
        entry=int.from_bytes(r[0xb762+2*room:0xb764+2*room],'little')
        if entry in targets:
            raise AssertionError(('direct entry needs register analysis',room,entry))
        if entry<0x8000:continue
        scan=entry;has_contact=False
        for _ in range(64):
            ins=z80.decode(r[scan:scan+8],scan);assert ins.len
            if r[scan]==0xcd and int.from_bytes(r[scan+1:scan+3],'little') in targets:has_contact=True
            if r[scan] in (0xc9,0xc3,0x18,0xe9):break
            scan+=ins.len
        if not has_contact:continue
        p=entry;registers={};sequence=[]
        for _ in range(64):
            instruction=z80.decode(r[p:p+8],p);assert instruction.len
            raw=r[p:p+instruction.len];sequence.append(dict(pc=p,bytes=raw.hex()))
            if raw[0] in (0xc9,0xc3,0x18,0xe9):break
            if raw[0] in (0x01,0x11):
                pair=('b','c') if raw[0]==1 else ('d','e')
                registers[pair[0]]=raw[2];registers[pair[1]]=raw[1]
            elif raw[0] in (0x06,0x0e,0x16,0x1e,0x3e):
                registers[{6:'b',14:'c',22:'d',30:'e',62:'a'}[raw[0]]]=raw[1]
            elif raw[0]==0xcd:
                target=int.from_bytes(raw[1:3],'little')
                if target in targets:
                    args=dict(registers)
                    required={0x5c96:('b','c','d','e'),0x5cc7:('e',),0x5cec:('c',),0x5cfb:('b','c','e'),0x5d59:('b','c'),0x5dee:('b','c','e'),0x5e01:('b','c'),0x5e0d:('b','c','e'),0x5e29:('b','c'),0x5e45:('b','c')}[target]
                    assert all(k in args for k in required),(room,target,args)
                    record=dict(room=room,entry=entry,call_site=p,target=target,kind=targets[target],explicit_registers=args)
                    if 'b' in args and 'c' in args:record['coordinate']=args['b']*256+args['c']
                    if target==0x5cfb:record['destination_room']=0x100|args['e']
                    result.append(record)
                registers={}
            else:raise AssertionError(('unsupported pre-call instruction',room,p,raw.hex()))
            p+=instruction.len
        else:raise AssertionError(('unterminated script',room))
    return result

def main():
    source=(ROOT/'input/original.sms').read_bytes();records=extract(source)
    counts={name:sum(r['kind']==name for r in records) for name in TARGETS.values()}
    contacts=[r for r in records if r['target']!=0x5cfb]
    lines=['/* Source 5C96 / 5CC7 / 5CEC contact scripts. */','static const u16 world_room_contacts[11][5] = {']
    for r in contacts:
        a=r['explicit_registers'];kind={0x5c96:1,0x5cc7:2,0x5cec:3}[r['target']]
        values=[r['room'],kind,r.get('coordinate',0x168 if kind==2 else 0),a.get('e',a.get('c',0)),a.get('d',0)]
        lines.append('    {'+','.join(str(v) for v in values)+'},')
    lines.append('};');(ROOT/'megadrive/src/room_contact.inc').write_text('\n'.join(lines)+'\n')
    from extract_room_clear import extract as extract_clear,extract_rewards,extract_completions
    clears={r['room']:r for r in extract_clear(source)+extract_rewards(source)+extract_completions(source)}
    portals=[r for r in records if r['target']==0x5cfb]
    lines=['/* Source portal room / coordinate / destination / after-clear stage. */','static const u16 world_room_portals[36][4] = {']
    for r in portals:
        stage=int(r['room'] in clears and clears[r['room']]['call_site']<r['call_site'])
        lines.append('    {'+','.join(str(v) for v in [r['room'],r['coordinate'],r['destination_room'],stage])+'},')
    lines.append('};');(ROOT/'megadrive/src/room_portals.inc').write_text('\n'.join(lines)+'\n')
    report=dict(source_sha256=hashlib.sha256(source).hexdigest(),records=records,handler_counts=counts,native_implemented=False,
        findings=['5C96 requires C0A6 & 77 == 14: aligned, stationary coordinate, unchanged direction, facing up with UP held. It marks the class-specific persistent bit before marking D-selected sides of the room in E and redrawing the current room. It is not a generic movable-block routine.',
        '5CC7 uses the same flag gate at coordinate 0168; changes DC1B to 4D after E-selected passage action.',
        '5CEC tests current persistent class bit and cell DC00+C == 0 before marking the flag and opening blocked passages.',
        '5CFB requires C0A6 & 30 == 30 and C060 == BC; it discards the room-script return address, loads room E, and places the hero on its first cell 0C or defaults to 128,88. Transition/load timing must be translated, not just the room id.',
        'Complete native contact flags were validated in v0050. This inventory alone does not enable contact effects.'])
    (ROOT/'analysis/contact_script_reference.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(counts));print(len(records),'contact calls inventoried; none enabled by this extraction')
if __name__=='__main__':main()
