"""Host checks for bounded retries of an immutable prepared PSG descriptor."""
import argparse,re
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import subprocess
from validate_md_z80_bridge import Stamp,Mailbox,Clock,Producer,Block,STUB

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',default='');parser.add_argument('--native-prep',action='store_true');options=parser.parse_args();assert not options.variant or re.fullmatch('[a-z0-9-]+',options.variant);assert not options.native_prep or options.variant
    suffix='-'+options.variant if options.variant else ''
    root=ROOT/('validation/md-z80-polled'+suffix);root.mkdir(exist_ok=True)
    stub=STUB.replace('u32 test_now_line,','u32 test_attempts,test_waits;\nu32 test_now_line,')
    stub=stub.replace(' u16 n;if(test_mode)', ' u16 n;test_attempts++;if(test_waits) {test_waits--;return MD_Z80_PSG_WAIT;}if(test_mode)')
    (root/'stub.c').write_text(stub)
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(root/'stub.c'),str(ROOT/'megadrive/src/md_z80_psg.c'),'-o',str(root/'polled.dll')]
    args.insert(1,'-DMD_PSG_NATIVE_PREP='+str(int(options.native_prep)))
    built=subprocess.run(args,env=env,capture_output=True,text=True);(root/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(root/'polled.dll'))
    init=dll.md_z80_psg_init;init.argtypes=[c.POINTER(Producer),c.POINTER(Mailbox),c.POINTER(Clock)];init.restype=c.c_uint8
    poll=dll.md_z80_psg_push_poll;poll.argtypes=[c.POINTER(Producer),c.POINTER(Block),c.c_uint16];poll.restype=c.c_uint8
    push=dll.md_z80_psg_push;push.argtypes=[c.POINTER(Producer),c.POINTER(Block),c.c_uint16];push.restype=c.c_uint8
    attempts=c.c_uint32.in_dll(dll,'test_attempts');waits=c.c_uint32.in_dll(dll,'test_waits')
    mode=c.c_uint8.in_dll(dll,'test_mode');clock_mode=c.c_uint8.in_dll(dll,'test_clock_mode')
    slots=((c.c_uint8*22)*32).in_dll(dll,'test_slots');transfers=c.c_uint32.in_dll(dll,'test_transfers')
    checks=0;rows=[]
    def fresh():
        mb=Mailbox();mb.grant=1;clock=Clock(c.pointer(mb.stamp),0xffff0000,0,0,100,262,0);p=Producer()
        mode.value=clock_mode.value=0;attempts.value=waits.value=transfers.value=0
        assert not init(c.byref(p),c.byref(mb),c.byref(clock))
        return mb,clock,p
    for spacing,count in [(0,1),(315,1),(315,16),(630,1),(630,8)]:
        b=Block((0xffff0000+68400)&0xffffffff,(16-count)*18 if spacing==315 else (8-count)*40 if spacing==630 else 0,count,spacing,0,(c.c_uint8*16)(*range(16)))
        mb,clock,p=fresh();assert not push(c.byref(p),c.byref(b),1);expected=list(slots[0])
        for limit in [0,1,2,8,128,65535]:
            for failures in sorted(set([0,1,max(0,limit-1),limit,limit+1])):
                mb,clock,p=fresh();waits.value=failures
                before=(bytes(slots),mb.head,p.published,p.last_due)
                status=poll(c.byref(p),c.byref(b),limit)
                wanted=1 if not limit else 0 if failures<limit else 5
                assert status==wanted
                assert attempts.value==(0 if not limit else min(failures+1,limit))
                if status:
                    assert before==(bytes(slots),mb.head,p.published,p.last_due) and not transfers.value
                else:
                    assert list(slots[0])==expected and transfers.value==1 and p.published==1 and mb.head==1
                    assert p.last_due==(b.due+(count-1)*spacing)&0xffffffff
                rows.append(dict(spacing=spacing,count=count,limit=limit,waits=failures,status=status,attempts=attempts.value));checks+=1
    b=Block((0xffff0000+68400)&0xffffffff,0,1,0,0,(c.c_uint8*16)(*range(16)))
    for error in [1,2,3,4]:
        mb,clock,p=fresh();mode.value=error;before=(bytes(slots),mb.head,p.published,p.last_due)
        assert poll(c.byref(p),c.byref(b),128)==error and attempts.value==1 and before==(bytes(slots),mb.head,p.published,p.last_due);checks+=1
    for mutation,wanted in [('format',1),('order',3),('full',2),('fault',4),('clock',1),('null',1)]:
        mb,clock,p=fresh();bad=Block.from_buffer_copy(b)
        if mutation=='format':bad.count=17
        if mutation=='order':bad.due=p.last_due-1
        if mutation=='full':mb.head=32
        if mutation=='fault':mb.stamp.error=1
        if mutation=='clock':clock.counter+=1
        before=(bytes(slots),mb.head,p.published,p.last_due)
        assert poll(c.byref(p),None if mutation=='null' else c.byref(bad),128)==wanted
        assert not attempts.value and before==(bytes(slots),mb.head,p.published,p.last_due);checks+=1
    # Exhaustion can be retried with the same unchanged block, and the old
    # public push remains exactly one transfer attempt.
    mb,clock,p=fresh();waits.value=9
    assert poll(c.byref(p),c.byref(b),8)==5 and not p.published
    assert poll(c.byref(p),c.byref(b),8)==0 and p.published==1 and attempts.value==10;checks+=1
    mb,clock,p=fresh();waits.value=2
    assert push(c.byref(p),c.byref(b),1)==5 and attempts.value==1 and not p.published;checks+=1
    report=dict(native_prep=options.native_prep,checks=checks,rows=rows,sources={n:hashlib.sha256((ROOT/'megadrive/src'/n).read_bytes()).hexdigest() for n in ['md_z80_psg.c','md_z80_psg.h']},limits=['Host stub counts exact synchronous attempts/exhaustion and publication atomicity, compares all22payload bytes with one-attempt push for five descriptor shapes. Limits0/1/2/8/128/65535, success after waits, immediate other errors, format/order/FULL/fault/clock rejection and exhaustion retry.', 'No native bus safety claim here; live instrumented kernels check real BUSREQ/grants and original source bytes/deadlines separately.'])
    (ROOT/('analysis/md_z80_polled'+suffix.replace('-','_')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n');print(checks,'polled host checks')


if __name__=='__main__':main()
