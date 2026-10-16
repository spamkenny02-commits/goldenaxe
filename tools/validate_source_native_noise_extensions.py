"""Original864F direct oracle for shared controls, reader exits and table ends."""
import argparse,contextlib,ctypes as c,hashlib,io,itertools,json,struct
from actor_reference import ROOT
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from validate_audio_note_commands_cost import COMMANDS
from validate_native_audio_noise import compile_helper
from validate_native_audio_sequence import Output
from validate_native_audio_prefix import Work
from run_core import run

def definitions():
    streams=[]
    for command,value in itertools.product(COMMANDS,[0,1,7,127,128,255]):
        operands=bytes([value,7,2,255,128]);size=5 if command in [0xe0,0xe9] else 4 if command==0xf0 else 2 if command in [0xea,0xf6] else 1
        if command==0xf6:operands=bytes([0,0x3e])
        streams.append(bytes([command])+operands[:size]+bytes([0x91,7,0x81,7]))
    # E2 targets GG stereo port06; on SMS that port mirrors cartridge control.
    # Zero routing inputs keep the custom SMS caller executable, as in the
    # retained tonal command fixture. This does not test GG hardware routing.
    rows=[((0x3600+i*12)&255,(0x3600+i*12)>>8,flags,0xe0,scale,1,0,0,0x30,fade,0,0x0b,0x8a,0,0)
          for i,flags,scale,fade in itertools.product(range(len(streams)),[0,2,4,16,64,128],[0,1,2,255],[0,1])]
    yield 'commands',rows,[0xd3,0xd4,0xd0,0xd1,0xd2,0xda,0xd7,0xef,0xd9,11,14,0x1a,0x1b,0x12,0xf6],streams
    rows=[(a&255,a>>8,flags,tone,1,pending,latch,noise,borrowed,11,138) for a,flags,tone,pending,latch,noise,borrowed in
          itertools.product([0x3c00,0x3c08],[0,4,64,128],[128,160,192,224],[0,0x90,0x91,0xac],[0,1,128,255],[0,128,192],[0,128])]
    yield 'termination',rows,[0xd3,0xd4,0xd0,0xd1,0xda,14,15,0x160,0x130,0x1a,0x1b],None
    rows=[((0x3c00+i*8)&255,(0x3c00+i*8)>>8,flags,1,latch,borrowed,0xe0,0,11,138) for i,flags,latch,borrowed in
          itertools.product(range(8),[0,4,64,68,128,255],[0,1,127,128,255],[0,128])]
    yield 'ownership',rows,[0xd3,0xd4,0xd0,0xda,15,0x130,0xd1,14,0x1a,0x1b],None
    rows=[]
    for index,flags,scale,counter in itertools.product(range(6),[0,2,4,64,128],[0,1,255],[0,1,255]):
        address=0x3c00+index*16;rows.append((address&255,address>>8,flags,0xe0,scale,1,0,0x2e if index==3 else 0x30,counter,0x5f,0x3e,0,11,138))
    yield 'flow',rows,[0xd3,0xd4,0xd0,0xd1,0xd2,0xda,0xd7,0xd9,0xf7,0xfe,0xff,0x100,0x1a,0x1b],None
    bank=SOURCE[0x18000:0x1c000];read=lambda a:bank[a-0x8000]
    pointers=[read(0x897f+n*2)|read(0x8980+n*2)<<8 for n in range(16)]+[0x8a52];rows=[]
    for mode in range(1,17):
        for index,flags,de in itertools.product([0,pointers[mode]-pointers[mode-1]-1,pointers[mode]-pointers[mode-1]-2],[0,4,16,20,128,255],[0x8a0b,0x899e,0x89a1,0xff80]):
            rows.append((flags,0xe0,2,mode,index,de&255,de>>8,0))
    yield 'held',rows,[0xd0,0xd1,0xda,0xd7,0xef,0x1a,0x1b,0x181],None
    for target,addresses in [(0x80,[0xde80,0xfe80]),(0x180,[0xdf80,0xff80])]:
        rows=[(a&255,a>>8,flags,0xe0,scale,1,0,0,11,138,0xea,value,3,0x81,7) for a,flags,scale,value in
              itertools.product(addresses,[0,4,8,128],[0,1,2,255],[0,127,128,255])]
        yield f'mirror-{target:03x}',rows,[0xd3,0xd4,0xd0,0xd1,0xd2,0xda,14,0xd7,0x1a,0x1b]+list(range(target,target+5)),None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind');args=parser.parse_args()
    folder,dll_native,function,_=compile_helper();suites=[];summary=[]
    if args.kind:
        old=json.loads((ROOT/'analysis/source_native_noise_extensions_report.json').read_text())
        assert old['noise_helper_sha256']==hashlib.sha256((ROOT/'megadrive/src/source_audio_noise.c').read_bytes()).hexdigest()
        assert old['sequence_helper_sha256']==hashlib.sha256((ROOT/'megadrive/src/source_audio_sequence.c').read_bytes()).hexdigest()
        suites=[s for s in json.loads((folder/'extension-cases.json').read_text()) if s['kind']!=args.kind]
        summary=[s for s in old['rows'] if s['kind']!=args.kind]
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_prefix_samples','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_prefix_tstates','gaw_prefix_m1_fetches']:getattr(dll,name).restype=c.c_uint64
    for name in ['gaw_prefix_entry','gaw_prefix_return']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    for kind,records,offsets,streams in definitions():
        if args.kind and kind!=args.kind:continue
        rom,base=generate(kind,records,offsets,0x864f,'audio-noise-extensions',0xded0,True,0xde1a)
        image=bytearray(rom.read_bytes());image[0x3430+0xd1]=0xe0
        if streams:
            image[0x3600:0x3600+len(streams)*12]=b''.join(s.ljust(12,b'\x81') for s in streams);image[0x3e00:0x3e04]=bytes([0x91,7,0x81,7])
        if kind=='termination':image[0x3c00]=0xf1;image[0x3c08]=0xf2
        if kind=='ownership':
            for i,value in enumerate([0,1,2,3,127,128,254,255]):image[0x3c00+i*8:0x3c08+i*8]=bytes([0xf3,value,0x91,7,0x81,7,0x81,7])
        if kind=='flow':
            programs=[[0xe7,0x81,7],[0xf7,9,1,0,0x3e,0x81,7],[0xf8,0x10,0x3e,0x81,7],[0xf9],[0xf7,0,2,0,0x3e,0x81,7],[0xf8,0x30,0x3e,0x81,7]]
            for index,program in enumerate(programs):image[0x3c00+index*16:0x3c00+index*16+len(program)]=bytes(program)
            for address,program in [(0x3e00,[0x91,7]),(0x3e10,[0xf8,0x20,0x3e,0x81,7]),(0x3e20,[0x83,7]),(0x3e30,[0xf9]),(0x3e60,[0x83,7])]:image[address:address+len(program)]=bytes(program)
        assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000];rom.write_bytes(image)
        seed=image[0x3430:0x3430+400];low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);canonical=[]
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
                cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();de_after=dll.gaw_envelope_return_de();unwind=bool(dll.gaw_envelope_did_unwind())
                entry=dll.gaw_prefix_refresh_before();exit=dll.gaw_prefix_refresh_after();assert exit==advance_refresh(entry,fetches+1)
                state=(c.c_uint8*400).from_buffer_copy(before);work=Work();output=Output();de=c.c_uint16(int.from_bytes(before[26:28],'little'))
                assert function(state,0xd0,low,32768,bank,c.byref(de),c.byref(work),c.byref(output)) and not output.error,(kind,region,case,'rejected')
                assert (bytes(state),work.tstates,work.fetches,de.value,output.unwind==2)==(after,cost,fetches,de_after,unwind),(kind,region,case,'source/native',work.tstates,cost,work.fetches,fetches,de.value,de_after,output.unwind,unwind)
                row=dict(input=list(inputs),patches=[(i,v) for i,v in enumerate(after) if before[i]!=v],tstates=cost,fetches=fetches,de_in=int.from_bytes(before[26:28],'little'),de=de_after,unwind=2 if unwind else 0)
                if region=='auto':canonical.append(row)
                else:assert row==canonical[case]
                checked[case]=row;raw.append(struct.pack('<6I',cost,fetches,entry,exit,de_after,unwind)+before+after);previous[0]=count
            with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,base/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            assert done and len(checked)==len(records),(kind,region,len(checked),len(records));data=b''.join(raw);(base/f'{region}-records.bin').write_bytes(data)
            summary.append(dict(kind=kind,region=region,cases=len(checked),raw_sha256=hashlib.sha256(data).hexdigest()));print(kind,region,len(checked),'source/native400 bytes,T/M1,DE/reader-exit exact',flush=True)
        suites.append(dict(kind=kind,api=0,fixture=str(rom.relative_to(ROOT)),fixture_sha256=hashlib.sha256(image).hexdigest(),seed=list(seed),offsets=offsets,cases=canonical))
    (folder/'extension-cases.json').write_text(json.dumps(suites,separators=(',',':'))+'\n')
    report=dict(rows=summary,source_sha256=hashlib.sha256(SOURCE).hexdigest(),
                noise_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_noise.c').read_bytes()).hexdigest(),
                sequence_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_sequence.c').read_bytes()).hexdigest(),
                limits=['Original864F/8679/sharedcommand handlers/bank6 unchanged; custom DI callers, explicitDE.',
                        'All400 bytes,T/M1,DE andwhole-reader exits directly compared; sourceRdelta checked.',
                        'Controlled/synthetic boundaries; native full IRQ clock andwaveforms remain unproven.'])
    (ROOT/'analysis/source_native_noise_extensions_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
