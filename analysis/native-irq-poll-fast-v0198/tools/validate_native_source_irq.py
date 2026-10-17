"""Native IRQ RAM/work composition against immutable source stage captures."""
import ctypes as c
import hashlib
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from source_rng_refresh import advance_refresh
from validate_native_audio_reader import compile_helper as compile_reader,Output as ReaderOutput
from validate_native_audio_prefix import Work


class Input(c.Structure):
    _fields_=[('raster',c.c_uint32),('lines',c.c_uint16),('tile_count',c.c_uint16),
              ('joy',c.c_uint8),('reset_mask',c.c_uint8),('compensation',c.c_uint8)]


class Output(c.Structure):
    _fields_=[('stages',Work*9),('whole',Work),('palette_taken',c.c_uint16),('reset_requested',c.c_uint8)]


def compile_helper():
    folder=ROOT/'validation/native-source-irq';folder.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',
          '-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),
          str(ROOT/'megadrive/src/source_irq.c'),'-o',str(folder/'source_irq.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True)
    (folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_irq.dll'));function=dll.source_irq
    function.argtypes=[c.POINTER(c.c_uint8),c.POINTER(Input),c.POINTER(Work),c.POINTER(Output)]
    function.restype=c.c_uint8;return folder,dll,function


def main():
    folder,dll,function=compile_helper();_,reader_dll,reader_function=compile_reader()
    source=(ROOT/'input/original.sms').read_bytes()
    low=(c.c_uint8*32768).from_buffer_copy(source[:32768])
    bank=(c.c_uint8*16384).from_buffer_copy(source[0x18000:0x1c000])
    cases=[];summary=[]

    def audio(before,de_in,expected=None):
        state=(c.c_uint8*400).from_buffer_copy(before);de=c.c_uint16(de_in);work=Work();output=ReaderOutput()
        assert reader_function(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(output)) and not output.error
        if expected:assert (bytes(state),de.value,work.tstates)==expected
        return work,bytes(state)

    def check(raw,metadata,reader,label):
        before=raw[128:464];after=raw[464:800]
        points=struct.unpack_from('<12Q',raw);values=struct.unpack_from('<8I',raw,96)
        counts=struct.unpack_from('<10Q',metadata);refresh=struct.unpack_from('<10I',metadata,80)
        phase=struct.unpack_from('<8I',metadata,120)
        cpu,line,line_master,lines,overflow,interlaced,reg1,hardware=phase
        assert not interlaced and not reg1&4 and hardware in [0x20,0x21]
        assert (lines,overflow) in [(262,0xda),(313,0xf2)]
        delta=((cpu-line_master+0x80000000)&0xffffffff)-0x80000000
        raster=(line*3420+delta)%(lines*3420)
        tile_count=0
        if before[0x42]:
            pointer=int.from_bytes(before[0x43:0x45],'little');asset=pointer if pointer<0x8000 else before[0x42]*0x4000+(pointer&0x3fff)
            tile_count=source[asset] or 256
        entry=Input(raster,lines,tile_count,*values[2:5])
        state=(c.c_uint8*336).from_buffer_copy(before);output=Output()
        assert function(state,c.byref(entry),c.byref(reader),c.byref(output)),(label,'rejected')
        times=[points[0]]+list(points[2:11])
        expected_t=[(b-a)//15 for a,b in zip(times,times[1:])]
        expected_m=[b-a for a,b in zip(counts,counts[1:])]
        assert [s.tstates for s in output.stages]==expected_t,(label,'T',[s.tstates for s in output.stages],expected_t)
        assert [s.fetches for s in output.stages]==expected_m,(label,'M1',[s.fetches for s in output.stages],expected_m)
        assert list(refresh[1:])==[advance_refresh(r,n) for r,n in zip(refresh,expected_m)]
        assert bytes(state)==after and output.palette_taken==values[0] and not output.reset_requested,(label,'RAM/palette')
        assert (output.whole.tstates,output.whole.fetches)==(72+sum(expected_t)+10,7+sum(expected_m))
        cases.append(dict(kind=label[0],before=list(before),after=list(after),
                          input=[raster,lines,tile_count,*values[2:5]],reader=[reader.tstates,reader.fetches],
                          stages=[[s.tstates,s.fetches] for s in output.stages],
                          whole=[output.whole.tstates,output.whole.fetches],palette_taken=output.palette_taken))

    unit=json.loads((ROOT/'analysis/full_irq_refresh_unit_report.json').read_text())
    prior=json.loads((ROOT/'analysis/full_irq_unit_report.json').read_text())
    fixture=(ROOT/'validation/full-irq-unit/full-irq/source.sms').read_bytes()
    assert hashlib.sha256(fixture).hexdigest()==unit['fixture_sha256']
    for row,old in zip(unit['rows'],prior['rows']):
        region=row['region'];raw=(ROOT/f'validation/full-irq-refresh-unit/{region}-records.bin').read_bytes()
        metadata=(ROOT/f'validation/full-irq-refresh-unit/{region}-m1.bin').read_bytes()
        assert hashlib.sha256(raw).hexdigest()==old['raw_sha256']
        assert hashlib.sha256(metadata).hexdigest()==row['M1_sha256']
        for number in range(row['cases']):
            record=raw[number*800:(number+1)*800];values=struct.unpack_from('<8I',record,96)
            initial=bytearray(fixture[0x3430:0x3430+400])
            initial[0x20:0x27]=fixture[0x80000+number*16:0x80000+number*16+7]
            initial[5]=128;initial[3]=values[4]
            reader,_=audio(initial,0)
            check(record,metadata[number*152:(number+1)*152],reader,('full-unit',region,number))
        summary.append(dict(kind='full-unit',region=region,cases=row['cases']))
        print('full-unit',region,row['cases'],'native336/nine T/M1 stages/palette exact',flush=True)
    live=json.loads((ROOT/'analysis/live_full_irq_refresh_report.json').read_text())
    archive=ROOT/'analysis/full-irq-refresh-research-v0183'
    for row in live['rows']:
        relative=f"validation/full-irq-refresh-live/{row['town']:02x}-{row['mask']:02x}"
        base=ROOT/relative;region=row['region']
        raw=(base/f'{region}-full-irq-records.bin').read_bytes()
        metadata=(base/f'{region}-full-irq-m1-records.bin').read_bytes()
        readers=(base/f'{region}-live-envelope-records.bin').read_bytes()
        events=json.loads((base/f'{region}-audio-irq-events.json').read_text())
        for suffix,data in [('full-irq-records.bin',raw),('full-irq-m1-records.bin',metadata),('live-envelope-records.bin',readers)]:
            assert data==(archive/relative/f'{region}-{suffix}').read_bytes()
        assert hashlib.sha256(metadata).hexdigest()==row['M1_sha256']
        calls=[e for e in events if e[1] in [0x1a2,0x202]]
        lookup={e[2]:readers[n*824:(n+1)*824] for n,e in enumerate(calls)}
        for number in range(row['cases']):
            record=raw[number*800:(number+1)*800];points=struct.unpack_from('<12Q',record)
            captured=lookup[points[8]];_,de_in,de_after,_,cost,unwind=struct.unpack_from('<6I',captured)
            assert not unwind
            reader,_=audio(captured[24:424],de_in,(captured[424:824],de_after,cost))
            check(record,metadata[number*152:(number+1)*152],reader,('full-live',row['town'],row['mask'],region,number))
        summary.append(dict(kind='full-live',town=row['town'],mask=row['mask'],region=region,cases=row['cases']))
        print('full-live',row['town'],row['mask'],region,row['cases'],'native336/nine T/M1 stages/palette exact',flush=True)
    wrapper=json.loads((ROOT/'analysis/audio_irq_refresh_unit_report.json').read_text())
    fixture=(ROOT/'validation/audio-irq-refresh-unit/wrapper/source.sms').read_bytes()
    assert hashlib.sha256(fixture).hexdigest()==wrapper['fixture_sha256']
    for row in wrapper['rows']:
        raw=(ROOT/f"validation/audio-irq-refresh-unit/wrapper/{row['region']}-results.bin").read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['raw_sha256']
        for number in range(row['cases']):
            inputs=fixture[0x80000+number*16:0x80000+(number+1)*16]
            initial=bytearray(fixture[0x3430:0x3430+400])
            for offset,value in zip([0x20,10,3,4],inputs):initial[offset]=value
            reader,audio_after=audio(initial,0)
            cost,fetches,_,_,delay=struct.unpack_from('<5I',raw,number*52)
            assert hashlib.sha256(audio_after).digest()==raw[number*52+20:number*52+52]
            before=bytearray(336);before[0x30]=inputs[0];expected=bytearray(before);expected[0x30]=delay
            state=(c.c_uint8*336).from_buffer_copy(before);entry=Input(0,262 if row['region']=='auto' else 313,0,0,16,inputs[2]);output=Output()
            assert function(state,c.byref(entry),c.byref(reader),c.byref(output))
            # Isolated source caller47T/4M1 is replaced by real vector72T/6M1.
            assert bytes(state)==expected and (output.whole.tstates,output.whole.fetches)==(cost+25,fetches+2)
            cases.append(dict(kind='audio-unit',before=list(before),after=list(expected),
                              input=[entry.raster,entry.lines,0,0,16,entry.compensation],reader=[reader.tstates,reader.fetches],
                              stages=[[0,0]]*9,whole=[output.whole.tstates,output.whole.fetches],palette_taken=0))
        summary.append(dict(kind='audio-unit',region=row['region'],cases=row['cases']))
        print('audio-unit',row['region'],row['cases'],'native wrapper work/audio/timer exact',flush=True)
    (folder/'cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(cases=len(cases),rows=summary,irq_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_irq.c').read_bytes()).hexdigest(),
                reader_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_reader.c').read_bytes()).hexdigest(),
                production_md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                limits=['Retained hashed original-instruction stage captures; full336 state/T/M1 and palette waits predicted from entry raster.',
                        'Reader work comes from native8000 and is compared to source audio states, not a fixed budget.',
                        'Tile count decoded from original asset. Input R/raster/joy remain observed; reset requested path and other queues need further proof.',
                        'No production IRQ-clock wiring, hardware acknowledgement, video waveform or full natural progression claim.'])
    (ROOT/'analysis/native_source_irq_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(cases),'native IRQ vectors passed',flush=True)


if __name__=='__main__':main()
