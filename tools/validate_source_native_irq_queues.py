"""Fresh original-IRQ oracle for tile and queue byte-counter boundaries."""
import contextlib
import ctypes as c
import hashlib
import io
import itertools
import json
import struct
from actor_reference import ROOT
from run_core import run
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from validate_native_source_irq import compile_helper,Input,Output
from validate_native_audio_reader import compile_helper as compile_reader,Output as ReaderOutput
from validate_native_audio_prefix import Work


def main():
    folder,dll_native,function=compile_helper();_,dll_reader,reader_function=compile_reader()
    programs=[[]]
    programs += [[1,bank,0,0x3e,0,0x40,count] for bank,count in itertools.product([0,4,128,255],[0,1,2,255])]
    programs += [[2,height,width,0,0] for height,width in itertools.product([0,1,2,255],[0,1,127,128,255])]
    programs += [[1,4,0,0x3e,0,0x40,2,2,2,1,0,0],
                 [2,2,1,0,0,1,128,0,0x3e,0,0x40,1],
                 [1,4,0,0x3e,0,0x40,1,1,128,0,0x3e,0,0x40,1]]
    records=[]
    for index,skip,hud,comp in itertools.product(range(len(programs)),[0,1],[0,3],[0,128]):
        address=0x3600+index*16;records.append((skip,hud,0,0,0,1,255,1,address&255,address>>8,len(programs[index]),comp))
    for count_index,skip,hud,comp in itertools.product(range(4),[0,1],[0,3],[0,128]):
        records.append((skip,hud,4,count_index,255,255,0,255,0,0x36,0,comp))
    rom,base=generate('queues',records,list(range(0x20,0x2c)),0x3040,'source-irq-queues')
    image=bytearray(rom.read_bytes());image[0x3430:0x3430+400]=bytes(400)
    for index,program in enumerate(programs):
        image[0x3600+index*16:0x3610+index*16]=bytes(program).ljust(16,b'\0')
    assert 0x3600+len(programs)*16<=0x3900
    image[0x3900:0x3a40]=bytes(320);image[0x3e00:0x3e04]=bytes([0,1,2,255])
    # Keep the fixture's C000..C00F counter/pointer/done fields intact.
    stub=bytearray.fromhex('2100391110c0014000edb02140391100dd010001edb02a28de1100dd011000edb0')
    destinations={0:0xc033,1:0xc045,2:0xc042,3:0xc043,4:0xc01c,5:0xc030,6:0xc020,7:0xc022,10:0xc034,11:0xde03}
    for index,address in destinations.items():
        stub+=b'\x3a'+(0xde20+index).to_bytes(2,'little')+b'\x32'+address.to_bytes(2,'little')
    stub+=bytes.fromhex('3e3e3244c03edd3235c03e803205de3e01322ec0f5c33701')
    assert len(stub)<=0xc0
    image[0x3040:0x3040+len(stub)]=stub
    assert image[0x137:0x227]==SOURCE[0x137:0x227] and image[0x293:0x327]==SOURCE[0x293:0x327]
    assert image[0x3b07:0x3b80]==SOURCE[0x3b07:0x3b80]
    assert image[0x10000:0x14000]==SOURCE[0x10000:0x14000] and image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
    rom.write_bytes(image)
    low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_fullirqrefresh_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_full_irq_records','gaw_full_irq_m1_events','gaw_live_envelope_events']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    dll.gaw_full_irq_samples.restype=dll.gaw_live_envelope_samples.restype=c.c_uint
    cases=[];summary=[]
    for region in ['auto','pal']:
        dll.gaw_timing_reset();previous=[0];done=[];raws=[];metas=[];readers=[]
        def observe(frame,ram):
            if ram[4]:done.append(frame)
            count=dll.gaw_full_irq_samples()
            if count==previous[0]:return
            assert count==previous[0]+1 and dll.gaw_live_envelope_samples()==count
            raw=c.string_at(c.addressof(dll.gaw_full_irq_records().contents)+(count-1)*800,800)
            meta=c.string_at(c.addressof(dll.gaw_full_irq_m1_events().contents)+(count-1)*152,152)
            captured=c.string_at(c.addressof(dll.gaw_live_envelope_events().contents)+(count-1)*824,824)
            _,de_in,de_after,_,cost,unwind=struct.unpack_from('<6I',captured);assert not unwind
            audio_state=(c.c_uint8*400).from_buffer_copy(captured[24:424]);de=c.c_uint16(de_in);reader=Work();audio_output=ReaderOutput()
            assert reader_function(audio_state,low,32768,bank,c.byref(de),c.byref(reader),c.byref(audio_output))
            assert (bytes(audio_state),de.value,reader.tstates)==(captured[424:824],de_after,cost)
            before=raw[128:464];after=raw[464:800]
            points=struct.unpack_from('<12Q',raw);values=struct.unpack_from('<8I',raw,96)
            counts=struct.unpack_from('<10Q',meta);refresh=struct.unpack_from('<10I',meta,80);phase=struct.unpack_from('<8I',meta,120)
            cpu,line,line_master,lines,overflow,interlaced,reg1,hardware=phase
            assert not interlaced and not reg1&4 and hardware in [0x20,0x21]
            assert (lines,overflow) in [(262,0xda),(313,0xf2)]
            delta=((cpu-line_master+0x80000000)&0xffffffff)-0x80000000;raster=(line*3420+delta)%(lines*3420)
            tile_count=(image[int.from_bytes(before[0x43:0x45],'little')] or 256) if before[0x42] else 0
            entry=Input(raster,lines,tile_count,*values[2:5]);state=(c.c_uint8*336).from_buffer_copy(before);output=Output()
            assert function(state,c.byref(entry),c.byref(reader),c.byref(output)),(region,count,'rejected')
            times=[points[0]]+list(points[2:11]);expected_t=[(b-a)//15 for a,b in zip(times,times[1:])]
            expected_m=[b-a for a,b in zip(counts,counts[1:])]
            assert [s.tstates for s in output.stages]==expected_t,(region,count,'T',[s.tstates for s in output.stages],expected_t)
            assert [s.fetches for s in output.stages]==expected_m,(region,count,'M1',[s.fetches for s in output.stages],expected_m)
            assert list(refresh[1:])==[advance_refresh(r,n) for r,n in zip(refresh,expected_m)]
            assert bytes(state)==after and output.palette_taken==values[0] and not output.reset_requested,(region,count,'RAM/palette')
            assert (output.whole.tstates,output.whole.fetches)==(72+sum(expected_t)+10,7+sum(expected_m))
            cases.append(dict(kind='queue-source',before=list(before),after=list(after),input=[raster,lines,tile_count,*values[2:5]],
                              reader=[reader.tstates,reader.fetches],stages=[[s.tstates,s.fetches] for s in output.stages],
                              whole=[output.whole.tstates,output.whole.fetches],palette_taken=output.palette_taken))
            raws.append(raw);metas.append(meta);readers.append(captured);previous[0]=count
        with contextlib.redirect_stdout(io.StringIO()):
            run(rom,len(records)*40+100,base/region,set(),[],core=core,skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region})
        assert done and previous[0]==len(records),(region,previous[0],len(records))
        row=dict(region=region,cases=previous[0])
        for name,data in [('records',b''.join(raws)),('m1',b''.join(metas)),('reader',b''.join(readers))]:
            (base/f'{region}-{name}.bin').write_bytes(data);row[name+'_sha256']=hashlib.sha256(data).hexdigest()
        summary.append(row);print(region,len(records),'fresh source tile/queue boundaries, nine stages/state exact',flush=True)
    (folder/'extension-cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(cases=len(cases),rows=summary,fixture_sha256=hashlib.sha256(image).hexdigest(),
                irq_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_irq.c').read_bytes()).hexdigest(),
                limits=['Original IRQ/queue/tile/HUD/bank4/bank6 code intact; custom DI caller, queue metadata and fixed-ROM tile assets.',
                        'Tile counts0/1/2/255, linear queue count0/1/2/255 andbank0/4/128/255, rectangle height0/1/2/255 andwidth0/1/127/128/255, mixed queues.',
                        '336 bytes/nine T/M1 stages/palette waits/R deltas/source audio compare. VDP IRQs disabled, so long synthetic cases do not prove nested IRQ scheduling.',
                        'No pixel transfer-value, production IRQ integration, hardware or full progression claim.'])
    (ROOT/'analysis/source_native_irq_queues_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
