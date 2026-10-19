"""Differential batch dequeue checks against the existing one-event consumer."""
from pathlib import Path
import ctypes as c
import hashlib
import json
import os
import random
import subprocess

ROOT=Path(__file__).resolve().parents[1]


class Event(c.Structure):
    _fields_=[('due',c.c_uint32),('value',c.c_uint8)]


class Queue(c.Structure):
    _fields_=[('events',c.POINTER(Event)),('capacity',c.c_uint16),('mask',c.c_uint16),
              ('read',c.c_uint16),('write',c.c_uint16)]


def main():
    folder=ROOT/'validation/psg-queue-bulk';folder.mkdir(exist_ok=True)
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',
          '-I',str(sdk/'inc'),str(ROOT/'megadrive/src/source_psg_queue.c'),'-o',str(folder/'queue.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'queue.dll'))
    qp=c.POINTER(Queue);ep=c.POINTER(Event)
    init=dll.source_psg_queue_init;init.argtypes=[qp,ep,c.c_uint16];init.restype=c.c_uint8
    push=dll.source_psg_queue_push;push.argtypes=[qp,ep,c.c_uint16];push.restype=c.c_uint8
    take=dll.source_psg_queue_take;take.argtypes=[qp,c.c_uint32,ep];take.restype=c.c_uint8
    batch=dll.source_psg_queue_take_many;batch.argtypes=[qp,c.c_uint32,ep,c.c_uint16,c.POINTER(c.c_uint16)];batch.restype=c.c_uint8
    rng=random.Random(0x5a80b017);cases=events=errors=0;trace=hashlib.sha256()
    for power in range(16):
        capacity=1<<power
        for turn in range(256):
            storage=(Event*capacity)();queue=Queue();assert not init(c.byref(queue),storage,capacity)
            origin=[0,65530,65535,rng.randrange(65536)][turn%4]
            queue.read=queue.write=origin
            count=rng.randrange(min(capacity,512)+1)
            time=rng.randrange(2**32);incoming=(Event*count)()
            for i in range(count):
                time=(time+rng.choice([0,1,315,630,9405,65536]))&0xffffffff
                incoming[i].due=time;incoming[i].value=rng.randrange(256)
            assert not push(c.byref(queue),incoming,count)
            baseline_storage=(Event*capacity).from_buffer_copy(storage)
            baseline=Queue(baseline_storage,capacity,capacity-1,origin,queue.write)
            now=(time+rng.choice([-65537,-9405,-1,0,1]))&0xffffffff
            limit=rng.choice([0,1,2,7,16,128,512,65535])
            output=(Event*max(1,min(limit,count)+1))()
            c.memset(output,0xa5,c.sizeof(output));before=bytes(output)
            expected=[]
            while len(expected)<limit:
                e=Event();status=take(c.byref(baseline),now,c.byref(e))
                if status:
                    assert status in [4,5]
                    break
                expected.append((e.due,e.value))
            taken=c.c_uint16(0x5aa5)
            assert not batch(c.byref(queue),now,output if limit else None,limit,c.byref(taken))
            assert taken.value==len(expected)
            assert [(output[i].due,output[i].value) for i in range(taken.value)]==expected
            assert bytes(output)[taken.value*c.sizeof(Event):]==before[taken.value*c.sizeof(Event):]
            assert queue.read==baseline.read and queue.write==baseline.write
            assert bytes(storage)==bytes(baseline_storage)
            trace.update(json.dumps([capacity,origin,count,now,limit,expected,queue.read]).encode())
            events+=taken.value;cases+=1
    storage=(Event*8)();queue=Queue();assert not init(c.byref(queue),storage,8)
    output=(Event*8)();c.memset(output,0xa5,c.sizeof(output))
    for mutation in ['null_queue','null_output','null_taken','null_storage','capacity_zero','capacity_three','mask','used']:
        assert not init(c.byref(queue),storage,8)
        if mutation=='null_storage':queue.events=None
        if mutation=='capacity_zero':queue.capacity=0
        if mutation=='capacity_three':queue.capacity=3
        if mutation=='mask':queue.mask=3
        if mutation=='used':queue.write=9
        before=bytes(output);queue_before=bytes(queue);count=c.c_uint16(0x5aa5)
        status=batch(None if mutation=='null_queue' else c.byref(queue),0,
                     None if mutation=='null_output' else output,8,
                     None if mutation=='null_taken' else c.byref(count))
        assert status==1 and bytes(output)==before and bytes(queue)==queue_before and count.value==0x5aa5
        errors+=1
    report=dict(cases=cases,events=events,atomic_invalid_cases=errors,trace_sha256=trace.hexdigest(),
        sources={n:hashlib.sha256((ROOT/'megadrive/src'/n).read_bytes()).hexdigest()
                 for n in ['source_psg_queue.c','source_psg_queue.h']},
        limits=['Host ABI differential check against unchanged source_psg_queue_take; capacities1..32768, cursor/u32date wrap, equal dates, future/empty, zero/oversized output capacity, preserved unconsumed output/storage and invalid atomicity.',
                'No concurrent host thread/IRQ or native timing proof; native live-loader proof and source-state tests are separate.'])
    (ROOT/'analysis/psg_queue_bulk_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)


if __name__=='__main__':main()
