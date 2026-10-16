"""Verify captured rollback and explicit streaming partial-publication contracts."""
import ctypes as c
import hashlib
import json
from actor_reference import ROOT
from validate_native_audio_reader import compile_helper,Output
from validate_native_audio_prefix import Work


class Status(c.Structure):
    _fields_=[('count',c.c_uint16),('error',c.c_uint16),('track',c.c_uint8)]


Sink=c.CFUNCTYPE(None,c.c_void_p,c.POINTER(c.c_uint8),c.c_uint16)


def main():
    folder,dll,capture=compile_helper();stream=dll.source_audio_reader_stream
    stream.argtypes=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),
                     c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Status),Sink,c.c_void_p]
    stream.restype=c.c_uint8
    image=bytearray((ROOT/'input/original.sms').read_bytes())
    image[0x3c00:0x3c02]=bytes([0x91,7]);image[0x3c10]=0xe3
    low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    cases=[]
    for kind in ['dispatch','priority','later-channel']:
        initial=bytearray(400);initial[5]=128;initial[6]=0
        if kind=='dispatch':initial[5]=0x8e
        if kind=='priority':initial[9]=1
        if kind=='later-channel':
            for slot,tone,address in [(0x40,0x80,0x3c00),(0xd0,0xe0,0x3c10)]:
                initial[slot]=128;initial[slot+1]=tone;initial[slot+2]=1
                initial[slot+3:slot+5]=address.to_bytes(2,'little');initial[slot+9]=0x30;initial[slot+10]=1
        state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(0x8a0b);work=Work();output=Output()
        assert not capture(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(output))
        assert bytes(state)==initial and de.value==0x8a0b and output.error and not output.count and not output.track
        assert work.tstates==work.fetches==0
        published=[]
        @Sink
        def sink(context,writes,count):published.extend(c.string_at(writes,count))
        state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(0x8a0b);status=Status()
        assert not stream(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(status),sink,None)
        assert status.error==output.error and status.count==len(published) and work.tstates==work.fetches==0
        if kind=='later-channel':assert published and state[0x4a]==7 and state[0xda]==1
        cases.append(dict(kind=kind,error=status.error,stream_writes_published=len(published),capture_rollback=True))
    report=dict(cases=cases,reader_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_reader.c').read_bytes()).hexdigest(),
                limits=['Host C rejection contracts only; unsupported source paths are not claimed emulated. Streaming keeps earlier successful effects.'])
    (ROOT/'analysis/native_audio_reader_rejection_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(cases),'reader capture/stream rejection contracts passed')


if __name__=='__main__':main()
