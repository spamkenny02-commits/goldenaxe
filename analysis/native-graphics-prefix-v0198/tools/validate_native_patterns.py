"""Native032A bytes and foreground T/M1 against the instruction timing model."""
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
from actor_reference import ROOT
from graphics_prefix_phase import pattern_rle
from graphics_prefix_refresh import audited_fetches

class Trace:
    def __init__(self,rom):
        self.rom=rom;self.ram=bytearray(65536)
        self.foreground_tstates=0;self.fetches=0
    def execute(self,t,effect=None):
        self.foreground_tstates+=t
        self.fetches+=audited_fetches(t,effect)

class Work(c.Structure):
    _fields_=[('tstates',c.c_uint32),('fetches',c.c_uint32)]

def vectors():
    rng=random.Random(0x032a)
    # Include real shared outdoor patterns and explicit B=0 literal runs.
    rom=(ROOT/'input/original.sms').read_bytes()
    trace=Trace(rom);end=pattern_rle(trace,0x3c010,0x4000)
    yield rom[0x3c010:end],0x4000
    yield bytes([0x80])+bytes(range(256))+bytes([0,0,0,0]),0x40fc
    yield bytes([0,0,0,0]),0xfffc
    for case in range(512):
        stream=bytearray()
        for plane in range(4):
            for run in range(rng.randrange(1,9)):
                literal=rng.randrange(2);count=rng.randrange(1,128)
                if literal and case%13==0:count=256
                stream.append((128 if literal else 0)|(count&127))
                stream.extend(rng.randbytes(count if literal else 1))
            stream.append(0)
        yield bytes(stream),rng.randrange(65533)

def decode(stream):
    output=bytearray([0xa7])*16384;source=0
    for plane in range(4):
        dst=plane
        while stream[source]:
            command=stream[source];source+=1
            for n in range((command&127) or 256):
                output[dst]=stream[source];dst+=4
                if command&128:source+=1
            if not command&128:source+=1
        source+=1
    return bytes(output),source

def main():
    folder=ROOT/'validation/native-patterns';folder.mkdir(exist_ok=True)
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',
        '-I',str(sdk/'inc'),str(ROOT/'megadrive/src/source_pattern.c'),'-o',str(folder/'patterns.dll')],
        env=env,capture_output=True,text=True)
    assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'patterns.dll'));fn=dll.source_pattern_decode
    fn.argtypes=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(Work)]
    fn.restype=c.c_void_p;cases=[]
    for stream,address in vectors():
        trace=Trace(stream);end=pattern_rle(trace,0,address)
        expected,used=decode(stream);assert end==used==len(stream)
        packed=(c.c_uint8*len(stream)).from_buffer_copy(stream)
        for measured in [False,True]:
            output=(c.c_uint8*len(expected))(*([0xa7]*len(expected)));work=Work()
            actual=fn(packed,output,address,c.byref(work) if measured else None)
            assert actual-c.addressof(packed)==used
            assert bytes(output)==expected
            if measured:assert (work.tstates,work.fetches)==(trace.foreground_tstates,trace.fetches)
        cases.append(dict(address=address,packed=len(stream),tstates=trace.foreground_tstates,
                          fetches=trace.fetches,output_sha256=hashlib.sha256(expected).hexdigest()))
    report=dict(cases=len(cases),measured_and_unmeasured_equal=True,
                module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_pattern.c').read_bytes()).hexdigest(),
                limits=['Host native C against existing instruction model; no independent new source capture.',
                        'Foreground totals only; live IRQ/clock integration remains pending.'])
    (folder/'vectors.json').write_text(json.dumps(cases,indent=2)+'\n')
    (ROOT/'analysis/native_patterns_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)

if __name__=='__main__':main()
