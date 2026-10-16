"""Execute original84C7 against native composition in all six tonal slots."""
import contextlib
import ctypes as c
import hashlib
import io
import itertools
import json
import struct
from actor_reference import ROOT
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from validate_native_audio_tone import compile_helper
from validate_native_audio_sequence import Output
from validate_native_audio_prefix import Work
from run_core import run


def definitions():
    streams = [[0x81,7],[0x91,7],[0x34,0x12,7],[0x80,7],[0xf1],[0xf2],
               [0xf3,1,0x91,7],[0xf3,128,0x91,7],[0xea,255,3,0x91,7],
               [0xf6,0,0x3e],[0xf7,0,2,0,0x3e,0x81,7],
               [0xf8,0x10,0x3e,0x81,7],[0xe7,0x81,7]]
    for slot in [0x40,0x70,0xa0,0x100,0x130,0x160]:
        rows = []
        for index,flags,mode,env,transpose in itertools.product(
                range(len(streams)),[0,2,4,32,34,64,66,128], [0,1,128],[0,128],[0,128]):
            pointer = 0x3c00+index*16
            rows.append((pointer&255,pointer>>8,flags,0xe0 if slot==0xa0 else 0x80,
                         1,1,mode,env,transpose,0,0x30,0,0,0,0,0))
        offsets = [slot+3,slot+4,slot,slot+1,slot+2,slot+10,slot+6,slot+7,
                   slot+37,slot+29,slot+25,14,15,0x1a,0x1b,slot+38]
        # DE can safely be zero for these notes; explicit value is retained in records.
        yield f'notes-{slot:03x}',slot,rows,offsets,streams
    rows = []
    for flags,mode,env,release,transpose,de in itertools.product(
            [0,2,4,16,32,64,128],range(9),[0,1,16,128],[0,1,2],[0,255],[0x8a0b,0xff80]):
        rows.append((flags,mode,env,release,transpose,2,0,0,1,1,1,0,0,de&255,de>>8,0))
    yield 'held',0x40,rows,[0x40,0x46,0x47,0x4e,0x65,0x4a,0x55,0x5f,0x54,0x56,0x57,0x5d,0x48,0x1a,0x1b,0x181],None


def main():
    folder,dll_native,function = compile_helper()
    suites=[];summary=[]
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll'
    dll=c.CDLL(str(core))
    for name in ['gaw_prefix_samples','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:
        getattr(dll,name).restype=c.c_uint
    for name in ['gaw_prefix_tstates','gaw_prefix_m1_fetches']:getattr(dll,name).restype=c.c_uint64
    for name in ['gaw_prefix_entry','gaw_prefix_return']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    for kind,slot,records,offsets,streams in definitions():
        rom,base=generate(kind,records,offsets,0x84c7,'audio-tone-extensions',0xde00+slot,True,0xde1a)
        image=bytearray(rom.read_bytes())
        # Valid modulation data, frequency and table-envelope index for each slot.
        for offset,value in [(slot+9,0x30),(slot+16,0x0b),(slot+17,0x8a),(slot+11,0x80),
                             (slot+12,0xff),(slot+21,0),(slot+31,0),(0x181,0)]:
            image[0x3430+offset]=value
        if streams:
            for index,program in enumerate(streams):
                image[0x3c00+index*16:0x3c00+index*16+len(program)]=bytes(program)
            for address,program in [(0x3e00,[0x91,7]),(0x3e10,[0xf8,0x20,0x3e,0x81,7]),(0x3e20,[0x83,7])]:
                image[address:address+len(program)]=bytes(program)
        assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
        rom.write_bytes(image)
        seed=image[0x3430:0x3430+400]
        low=(c.c_uint8*32768).from_buffer_copy(image[:32768])
        bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);canonical=[]
        for region in ['auto','pal']:
            dll.gaw_timing_reset();previous=[0];done=[];raw=[];checked={}
            def observe(frame,ram):
                if ram[4]:done.append(frame)
                count=dll.gaw_prefix_samples()
                if count==previous[0]:return
                assert count==previous[0]+1
                case=int.from_bytes(ram[:2],'little')
                before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
                inputs=image[0x80000+case*16:0x80000+(case+1)*16];initial=bytearray(seed)
                for offset,value in zip(offsets,inputs):initial[offset]=value
                assert before==initial,(kind,case,'caller state')
                cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches()
                de_after=dll.gaw_envelope_return_de();unwind=bool(dll.gaw_envelope_did_unwind())
                entry=dll.gaw_prefix_refresh_before();exit=dll.gaw_prefix_refresh_after()
                assert exit==advance_refresh(entry,fetches+1)
                state=(c.c_uint8*400).from_buffer_copy(before);work=Work();output=Output()
                de=c.c_uint16(int.from_bytes(before[26:28],'little'))
                assert function(state,slot,low,32768,bank,c.byref(de),c.byref(work),c.byref(output)) and not output.error,(kind,region,case,'rejected',output.error)
                assert (bytes(state),work.tstates,work.fetches,de.value,output.unwind)==(after,cost,fetches,de_after,unwind),(
                    kind,region,case,'source/native',work.tstates,cost,work.fetches,fetches,de.value,de_after,output.unwind,unwind,
                    [(i,a,b) for i,(a,b) in enumerate(zip(state,after)) if a!=b][:10])
                row=dict(input=list(inputs),patches=[(i,v) for i,v in enumerate(after) if before[i]!=v],
                         tstates=cost,fetches=fetches,de_in=int.from_bytes(before[26:28],'little'),de=de_after,unwind=0)
                if region=='auto':canonical.append(row)
                else:assert row==canonical[case]
                checked[case]=row;raw.append(struct.pack('<6I',cost,fetches,entry,exit,de_after,unwind)+before+after)
                previous[0]=count
            with contextlib.redirect_stdout(io.StringIO()):
                run(rom,len(records)*4+100,base/region,set(),[],core=core,skip_intro=False,ram_observer=observe,
                    core_options={'genesis_plus_gx_region_detect':region})
            assert done and len(checked)==len(records),(kind,region,len(checked),len(records))
            data=b''.join(raw);(base/f'{region}-records.bin').write_bytes(data)
            summary.append(dict(kind=kind,region=region,cases=len(checked),raw_sha256=hashlib.sha256(data).hexdigest()))
            print(kind,region,len(checked),'source/native400 bytes,T/M1,DE/returns exact',flush=True)
        suites.append(dict(kind=kind,fixture=str(rom.relative_to(ROOT)),fixture_sha256=hashlib.sha256(image).hexdigest(),
                           seed=list(seed),offsets=offsets,offset=slot,cases=canonical))
    (folder/'extension-cases.json').write_text(json.dumps(suites,separators=(',',':'))+'\n')
    report=dict(rows=summary,source_sha256=hashlib.sha256(SOURCE).hexdigest(),
                tone_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_tone.c').read_bytes()).hexdigest(),
                limits=['Original84C7/bank6 unchanged; custom DI callers, all six tone slots plus held-envelope/pitch cases.',
                        'All400 bytes,T/M1,DE/returns compared directly, sourceR delta checked.',
                        'Synthetic context boundaries; PSG waveform, complete IRQ clock and natural progression remain open.'])
    (ROOT/'analysis/source_native_tone_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
