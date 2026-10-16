"""Direct original8000 oracle for prefixes, compensation and channel composition."""
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
from validate_native_audio_reader import compile_helper,Output
from validate_native_audio_prefix import Work
from run_core import run

SLOTS=[0x40,0x70,0xa0,0xd0,0x100,0x130,0x160]


def definitions():
    rows=[(phase,enabled,flags,1) for phase,enabled,flags in
          itertools.product(range(256),[0,1,128,255],[0,128])]
    yield 'compensation',rows,[4,3,0x40,0x4a]
    rows=[(command,enabled,phase) for command,enabled,phase in
          itertools.product([i for i in range(256) if i not in [0x8e,0x8f,0xad,0xae,0xaf,0xb4]],
                            [0,128],[0,5])]
    yield 'dispatch',rows,[5,3,4]
    rows=[(command,priority,pending,flags) for command,priority,pending,flags in
          itertools.product([0,128]+list(range(0x90,0xad)),[0,1,128,255],[0x90,0x91,0xac],[0,128,192])]
    yield 'priority',rows,[9,16,14,0x160]
    rows=[]
    for mask,count,phase,enabled in itertools.product(range(128),[0,1,2],[0,5],[0,128]):
        rows.append(tuple(128 if mask&(1<<n) else 0 for n in range(7))+(count,)*7+(phase,enabled))
    yield 'channels',rows,SLOTS+[slot+10 for slot in SLOTS]+[4,3]
    rows=[(address&255,address>>8,flags,command,latch) for address,flags,command,latch in
          itertools.product([0x3c00,0x3c10,0x3c20,0x3c30,0x3c40,0x3c50],
                            [128,132,192],[0,0x90,0x91,0xac],[0,128])]
    yield 'noise-exits',rows,[0xd3,0xd4,0xd0,14,15]


def main():
    folder,dll_native,function=compile_helper();suites=[];summary=[]
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_prefix_samples','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:
        getattr(dll,name).restype=c.c_uint
    for name in ['gaw_prefix_tstates','gaw_prefix_m1_fetches']:getattr(dll,name).restype=c.c_uint64
    for name in ['gaw_prefix_entry','gaw_prefix_return']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    for kind,records,offsets in definitions():
        rom,base=generate(kind,records,offsets,0x8000,'audio-reader-extensions',None,False,0xde1a)
        image=bytearray(rom.read_bytes());seed=bytearray(400);seed[5]=128;seed[26:28]=bytes([0x0b,0x8a])
        for slot,tone in zip(SLOTS,[0x80,0xa0,0xc0,0xe0,0xa0,0xc0,0xe0]):
            seed[slot+1]=tone;seed[slot+2]=1;seed[slot+3:slot+5]=bytes([0,0x3e])
            seed[slot+9]=0x30;seed[slot+10]=1
        if kind=='noise-exits':
            for slot in SLOTS:seed[slot]=128;seed[slot+10]=2
            seed[0xda]=1
        image[0x3430:0x3430+400]=seed
        image[0x3e00:0x3e04]=bytes([0x91,7,0x81,7])
        for address,program in [(0x3c00,[0xf1]),(0x3c10,[0xf2]),(0x3c20,[0xf3,0xe3,0x81,7]),
                                (0x3c30,[0xf3,0xe4,0x81,7]),(0x3c40,[0xf6,0,0x3e]),
                                (0x3c50,[0xea,255,3,0x81,7])]:
            image[address:address+len(program)]=bytes(program)
        assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000];rom.write_bytes(image)
        low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);canonical=[]
        for region in ['auto','pal']:
            dll.gaw_timing_reset();previous=[0];done=[];raw=[];checked={}
            def observe(frame,ram):
                if ram[4]:done.append(frame)
                count=dll.gaw_prefix_samples()
                if count==previous[0]:return
                assert count==previous[0]+1
                case=int.from_bytes(ram[:2],'little');before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
                inputs=image[0x80000+case*16:0x80000+(case+1)*16];initial=bytearray(seed)
                for offset,value in zip(offsets,inputs):initial[offset]=value
                assert before==initial
                cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();de_after=dll.gaw_envelope_return_de();unwind=dll.gaw_envelope_did_unwind()
                entry=dll.gaw_prefix_refresh_before();exit=dll.gaw_prefix_refresh_after();assert exit==advance_refresh(entry,fetches+1)
                state=(c.c_uint8*400).from_buffer_copy(before);work=Work();output=Output();de=c.c_uint16(int.from_bytes(before[26:28],'little'))
                assert function(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(output)) and not output.error,(kind,region,case,'rejected',output.error)
                assert not unwind and (bytes(state),work.tstates,work.fetches,de.value)==(after,cost,fetches,de_after),(
                    kind,region,case,'source/native',work.tstates,cost,work.fetches,fetches,de.value,de_after,
                    [(i,a,b) for i,(a,b) in enumerate(zip(state,after)) if a!=b][:10])
                row=dict(before=list(before),after=list(after),de_in=int.from_bytes(before[26:28],'little'),de=de_after,tstates=cost,fetches=fetches)
                if region=='auto':canonical.append(row)
                else:assert row==canonical[case]
                checked[case]=row;raw.append(struct.pack('<6I',cost,fetches,entry,exit,de_after,unwind)+before+after);previous[0]=count
            with contextlib.redirect_stdout(io.StringIO()):
                run(rom,len(records)*4+100,base/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            assert done and len(checked)==len(records),(kind,region,len(checked),len(records))
            data=b''.join(raw);(base/f'{region}-records.bin').write_bytes(data)
            summary.append(dict(kind=kind,region=region,cases=len(checked),raw_sha256=hashlib.sha256(data).hexdigest()))
            print(kind,region,len(checked),'source/native400 bytes,T/M1,DE exact',flush=True)
        suites.append(dict(kind=kind,fixture=str(rom.relative_to(ROOT)),fixture_sha256=hashlib.sha256(image).hexdigest(),cases=canonical))
    (folder/'extension-cases.json').write_text(json.dumps(suites,separators=(',',':'))+'\n')
    report=dict(rows=summary,source_sha256=hashlib.sha256(SOURCE).hexdigest(),
                reader_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_reader.c').read_bytes()).hexdigest(),
                limits=['Original8000/bank6 intact, custom DI caller. All256 compensation phases, supported dispatch, priorities, all128 active-slot masks andnoise reader exits.',
                        'All400 bytes,T/M1,DE directly compared; R delta checked. Synthetic states, not natural reachability.',
                        'PSG writes/full IRQ clock/waveform/hardware/full progression remain outside this component fixture.'])
    (ROOT/'analysis/source_native_reader_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
