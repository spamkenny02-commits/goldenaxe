"""Check whole-channel rollback when a later tone component rejects its input."""
import ctypes as c
import hashlib
import json
from actor_reference import ROOT
from validate_native_audio_tone import compile_helper
from validate_native_audio_sequence import Output
from validate_native_audio_prefix import Work


def main():
    folder,dll,function=compile_helper()
    image=bytearray((ROOT/'input/original.sms').read_bytes())
    image[0x3c00:0x3c07]=bytes([0xea,128,3,0xe3,0x91,7,0x81])
    image[0x3c10:0x3c12]=bytes([0x91,7])
    low=(c.c_uint8*32768).from_buffer_copy(image[:32768])
    bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    rows=[]
    for slot in [0x40,0x70,0xa0,0x100,0x130,0x160]:
        for kind,pointer,mode,table in [('stream',0xc000,0,0),
                                         ('command-after-mutation',0x3c00,0,0),
                                         ('vibrato-after-note',0x3c10,128,0xc000)]:
            initial=bytearray(400);initial[slot]=128;initial[slot+1]=128
            initial[slot+2]=1;initial[slot+3:slot+5]=pointer.to_bytes(2,'little')
            initial[slot+6]=mode;initial[slot+9]=0x30;initial[slot+10]=1
            initial[slot+16:slot+18]=table.to_bytes(2,'little')
            state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(0x8a0b)
            work=Work();output=Output()
            accepted=function(state,slot,low,32768,bank,c.byref(de),c.byref(work),c.byref(output))
            assert not accepted and output.error,(slot,kind,'accepted')
            assert bytes(state)==initial and de.value==output.de==0x8a0b,(slot,kind,'partial state')
            assert work.tstates==work.fetches==output.count==output.unwind==0,(slot,kind,'partial output')
            rows.append(dict(slot=slot,kind=kind,error=output.error))
    report=dict(cases=rows,tone_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_tone.c').read_bytes()).hexdigest(),
                limits=['Host C only; verifies rollback contract, not source semantics for uncaptured RAM/unsupported commands.'])
    (ROOT/'analysis/native_audio_tone_rejection_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'whole-tone rejection/rollback cases passed')


if __name__=='__main__':main()
