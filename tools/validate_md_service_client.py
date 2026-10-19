"""Exercise the native clock client against independent physical HV tables."""
import ctypes as c
import hashlib
import json
import os
import random
import re
import subprocess
from actor_reference import ROOT


class Stamp(c.Structure):
    _fields_=[(n,c.c_uint8) for n in ['sequence','v','counter_hi','counter_lo','ready','error']]


class Clock(c.Structure):
    _fields_=[('stamp',c.POINTER(Stamp))]+[(n,c.c_uint32) for n in ['base','reads','retries']]+[(n,c.c_uint16) for n in ['counter','lines','error']]


class Output(c.Structure):
    _fields_=[('master',c.c_uint32)]+[(n,c.c_uint16) for n in ['vertical','horizontal','lines','error']]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    folder=ROOT/'validation/md-service-client';folder.mkdir(parents=True,exist_ok=True)
    sdk=ROOT.parents[1]/'work/sgdk';core=ROOT.parents[1]/'work/genesis-plus-gx/core'
    hvc=(core/'hvc.h').read_bytes();ctrl=(core/'vdp_ctrl.c').read_bytes()
    h=[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',hvc.decode().split('static const uint8 cycle2hc32[3420] =')[1].split('};')[0])]
    section=ctrl.decode().split('static const uint16 vc_table[4][2] =')[1].split('};')[0]
    maxima=[tuple(int(x,16) for x in pair) for pair in re.findall(r'\{\s*0x([0-9a-fA-F]+)\s*,\s*0x([0-9a-fA-F]+)',section)][1]
    assert len(h)==3420
    (folder/'host.c').write_text('#include "md_service_clock.h"\nu16 test_hv;u16 md_service_clock_hv(void){return test_hv;}\n')
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'host.c'),str(ROOT/'megadrive/src/md_service_clock.c'),'-o',str(folder/'host.dll')]
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'host-build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'host.dll'));hv=c.c_uint16.in_dll(dll,'test_hv')
    init=dll.md_service_clock_init;init.argtypes=[c.POINTER(Clock),c.POINTER(Stamp),c.c_uint16,c.c_uint32];init.restype=c.c_uint8
    now=dll.md_service_clock_now;now.argtypes=[c.POINTER(Clock),c.POINTER(Output)];now.restype=c.c_uint8
    results=[];checks=0
    for lines,maximum in zip([262,313],maxima):
        v=lambda line:((line%lines) if line%lines<=maximum else line%lines-lines)&255
        stamp=Stamp();clock=Clock();out=Output();epoch=0xffff0000
        assert init(c.byref(clock),c.byref(stamp),lines,epoch)==0
        stamp.ready=1;absolute=100;wraps=0;last_counter=100;rng=random.Random(lines)
        # All physical lines, all 171 H32 phases, all supported publication ages.
        cases=[(100+line,age,phase) for line in range(lines) for age in range(5) for phase in range(0,3420,20)]
        # Long foreground gaps and many 16-bit line counter / 32-bit master wraps.
        for _ in range(16000):
            absolute+=rng.randrange(0,65531)
            cases.append((absolute,rng.randrange(5),rng.randrange(3420)))
        # The exhaustive grid advances monotonically; restart the epoch before random cases.
        for i,(sample,age,phase) in enumerate(cases):
            if i==lines*5*171:
                assert init(c.byref(clock),c.byref(stamp),lines,epoch)==0
                last_counter=100
            stamp.sequence=(i*2)&255;stamp.v=v(sample);stamp.counter_hi=(sample>>8)&255;stamp.counter_lo=sample&255
            hv.value=(v(sample+age)<<8)|h[phase]
            status=now(c.byref(clock),c.byref(out));expected=(epoch+(sample+age-100)*3420+phase//20*20)&0xffffffff
            assert status==0 and out.master==expected and out.vertical==hv.value&0xff00 and out.horizontal==phase//20*20 and out.lines==lines and not out.error,(lines,i,sample,age,phase,status,out.master,expected)
            counter=sample&65535;wraps+=counter<last_counter;last_counter=counter;checks+=1
        # Invalid, not-ready, odd sequence, stale/future stamp and sticky fault:
        # rejected reads may update diagnostic retries but never time/output.
        def reject(status):
            nonlocal checks
            before=(clock.base,clock.counter,clock.reads,bytes(out))
            assert now(c.byref(clock),c.byref(out))==status
            assert before==(clock.base,clock.counter,clock.reads,bytes(out));checks+=1
        stamp.ready=0;reject(2);stamp.ready=1
        stamp.sequence=1;reject(2);stamp.sequence=2
        stamp.v=100;stamp.counter_hi=0;stamp.counter_lo=100
        hv.value=99<<8|h[0];reject(2)  # publication one line in the future
        hv.value=105<<8|h[0];reject(2) # stale by five lines
        hv.value=100<<8|0x94;reject(1)
        stamp.error=1;reject(3);stamp.error=0;reject(3)
        assert init(c.byref(clock),c.byref(stamp),lines,epoch)==0
        hv.value=100<<8|h[0];assert now(c.byref(clock),c.byref(out))==0 and out.master==epoch
        before=bytes(clock);assert init(c.byref(clock),c.byref(stamp),263,0)==1 and bytes(clock)==before
        assert init(None,c.byref(stamp),lines,epoch)==1 and init(c.byref(clock),None,lines,epoch)==1
        assert now(None,c.byref(out))==1 and now(c.byref(clock),None)==1
        results.append(dict(lines=lines,cases=len(cases),counter_wraps=wraps,rejected_cases=7))
    report=dict(checks=checks,results=results,sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['md_service_clock.c','md_service_clock.h']},references={'hvc.h':sha(hvc),'vdp_ctrl.c':sha(ctrl)},
                limits=['Host C arithmetic/client rejection tests use independent emulator H32/VC tables. Hardware concurrency and native ABI are covered separately by validate_md_service_clock; no DMA, interrupt scheduler or full-game claim.'])
    (ROOT/'analysis/md_service_client_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
