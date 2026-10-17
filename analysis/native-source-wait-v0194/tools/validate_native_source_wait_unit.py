"""Direct source wait replays for DI/EI/latched IRQ boundaries against native C."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import struct
from actor_reference import ROOT
from run_core import run
from validate_native_source_wait import compile_helper,MODULES


def main():
    folder,dll_native,function=compile_helper();cases=[];summary=[]
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_waitrefresh_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_wait_events']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    for name in ['gaw_foreground_phase_samples','gaw_wait_samples','gaw_audio_irq_count']:getattr(dll,name).restype=c.c_uint
    dll.gaw_audio_irq_events.restype=c.POINTER(c.c_uint64)
    for variant,report_name in [('wait-raster-unit','wait_raster_unit_report.json'),('wait-raster-unit-pal','wait_raster_pal_latched_unit_report.json')]:
        old=json.loads((ROOT/'analysis'/report_name).read_text());fixture=ROOT/f'validation/{variant}/wait/source.sms';image=fixture.read_bytes()
        assert hashlib.sha256(image).hexdigest()==old['fixture_sha256']
        low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
        for row in old['rows']:
            region=row['region'];dll.gaw_timing_reset();previous=[0];done=[];raw_pairs=[];raw_meta=[];raw_waits=[];source_events=[]
            def observe(frame,ram):
                if ram[4]:done.append(frame)
                count=dll.gaw_wait_samples()
                if count==previous[0]:return
                assert count==previous[0]+1
                wraw=c.string_at(c.addressof(dll.gaw_wait_events().contents)+(count-1)*112,112);w=struct.unpack('<14Q',wraw)
                fore=dll.gaw_foreground_phase_samples();base=c.addressof(dll.gaw_foreground_phase_events().contents)
                mbase=c.addressof(dll.gaw_foreground_m1_events().contents);found={}
                for i in range(max(0,fore-16),fore):
                    raw=c.string_at(base+i*800,800);pc,time=struct.unpack_from('<2Q',raw)
                    if (pc,time) in [(0xb95,w[0]),(0xbb3,w[2])]:found[pc]=(raw,c.string_at(mbase+i*16,16))
                initial,fmeta=found[0xb95];end,lmeta=found[0xbb3]
                first_meta=struct.unpack('<Q2I',fmeta);end_meta=struct.unpack('<Q2I',lmeta)
                phase=struct.unpack_from('<12I',initial,16);end_phase=struct.unpack_from('<12I',end,16)
                before=initial[64:400];sound=initial[400:800]
                state=(c.c_uint8*336).from_buffer_copy(before);audio=(c.c_uint8*400).from_buffer_copy(sound)
                output=(c.c_uint32*18)();trace=(c.c_uint32*96)()
                assert function((c.c_uint32*12)(*phase),first_meta[1],state,audio,low,bank,0,output,trace),(variant,region,count,'rejected')
                assert bytes(audio)==end[400:800] and all(state[i]==end[64+i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(variant,region,count,'RAM/audio')
                delta=((end_phase[0]-end_phase[2]+0x80000000)&0xffffffff)-0x80000000
                assert output[0]==(end_phase[1]*3420+delta)%(phase[3]*3420) and output[2]==w[2]-w[0],(variant,region,count,'phase/time')
                assert output[5]*15==w[3]-w[1] and output[15]==w[4],(variant,region,count,'IRQ/polling')
                assert output[10]==end_meta[1] and output[4]+output[6]==end_meta[0]-first_meta[0],(variant,region,count,'M1/R')
                assert (output[11],output[13],output[14])==(end_phase[8],end_phase[10],1) and not output[12] and not output[16]
                events=dll.gaw_audio_irq_events();actual=[]
                for i in range(dll.gaw_audio_irq_count()-1,-1,-1):
                    time=events[i*14+1]
                    if time<=w[0]:break
                    if time<w[2] and events[i*14]==0x137:actual.append((time-w[0],bool(events[i*14+4])))
                actual.reverse();predicted=[(trace[n*6],bool(trace[n*6+5])) for n in range(output[7])]
                assert predicted==actual,(variant,region,count,'IRQ acceptance',predicted,actual)
                cases.append(dict(kind=variant,phase=list(phase),refresh=first_meta[1],ram=list(before),audio=list(sound),
                                  tile_count=0,expected_ram=list(state),expected_audio=list(audio),expected=list(output),events=list(trace[:output[7]*6]),
                                  fixture=str(fixture.relative_to(ROOT)),fixture_sha256=old['fixture_sha256']))
                raw_pairs.append(initial+end);raw_meta.append(fmeta+lmeta);raw_waits.append(wraw);source_events.append(actual)
                previous[0]=count
            base=ROOT/f'validation/native-source-wait-unit/{variant}-{region}'
            with contextlib.redirect_stdout(io.StringIO()):
                run(fixture,row['cases']*10+100,base,set(),[],core=core,skip_intro=False,ram_observer=observe,
                    core_options={'genesis_plus_gx_region_detect':region})
            assert done and previous[0]==row['cases'] and hashlib.sha256(b''.join(raw_waits)).hexdigest()==row['wait_sha256']
            hashes={}
            for name,data in [('pairs',b''.join(raw_pairs)),('m1',b''.join(raw_meta)),('waits',b''.join(raw_waits))]:
                (base/f'{name}.bin').write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
            (base/'irq-offsets.json').write_text(json.dumps(source_events,separators=(',',':'))+'\n')
            summary.append(dict(variant=variant,region=region,cases=row['cases'],sha256=hashes))
            print(variant,region,row['cases'],'source/native wait, dynamicIRQ,DI/EI/latched contexts exact',flush=True)
    (folder/'extension-cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(cases=len(cases),rows=summary,
                helper_sha256={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                limits=['Retained original fixtures reexecuted read-only; entry/return states and M1/R/cost/IRQ offsets compared directly to native clock/wait/dynamicIRQ.',
                        '331 IRQ RAM bytes and400 audio; input/status five bytes excluded. Sound80/inactive channels, empty queues in these latch fixtures.',
                        'No nested IRQs, physical acknowledgement, production wiring, waveform/hardware/full progression proof.'])
    (ROOT/'analysis/native_source_wait_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
