"""Compare standalone8211 to original SMS instructions; helper/bank6 unchanged."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct
from actor_reference import ROOT
from audio_restore_effect_refresh import restore_effect_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
    records=[(command,latch,tone,noise,de&255,de>>8) for command,latch,tone,noise,de in
             itertools.product(range(0x90,0xad),[0,1,127,128,255],[0,128,192],[0,128,192],[0,0x9123,0xde0a,65535])]
    rom,folder=generate('restore',records,[14,15,0x130,0x160,0x1a,0x1b],0x8211,'audio-restore-effect-refresh',de_address=0xde1a)
    image=bytearray(rom.read_bytes());anchor=bytes.fromhex('3e0632ffffcd0030')
    assert image.count(anchor)==1;position=image.index(anchor);image[position:position+len(anchor)]=bytes.fromhex('3e0632ffffcd5030')
    # Supply A before the instrumented3000 call; retain DE in ordinary caller RAM.
    image[0x3050:0x305b]=bytes.fromhex('3a0edecd0030ed530cc0c9')
    assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000];rom.write_bytes(image)
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefixrefresh_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_prefix_samples','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_prefix_tstates','gaw_prefix_m1_fetches']:getattr(dll,name).restype=c.c_uint64
    for name in ['gaw_prefix_entry','gaw_prefix_return']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    rows=[]
    for region in ['auto','pal']:
        dll.gaw_timing_reset();previous=[0];checked={};done=[];pending=[None]
        def observe(frame,ram):
            if ram[4]:done.append(frame)
            if pending[0] is not None and frame>pending[0][0]:
                _,case,de=pending[0]
                assert int.from_bytes(ram[:2],'little')==case
                assert int.from_bytes(ram[12:14],'little')==de,(region,case,'DE',ram[12:14],de)
                pending[0]=None
            n=dll.gaw_prefix_samples()
            if n==previous[0]:return
            assert n==previous[0]+1
            before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
            case=int.from_bytes(ram[:2],'little');de=int.from_bytes(before[0x1a:0x1c],'little')
            predicted=restore_effect_refresh(SOURCE,before,before[14],de)
            cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches()
            entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after()
            assert (cost,fetches,after)==(predicted['tstates'],predicted['m1_fetches'],predicted['state']),(region,case,records[case],cost,fetches,predicted['tstates'],predicted['m1_fetches'])
            assert exitR==advance_refresh(entryR,fetches+1),(region,case,'R')
            checked[case]=struct.pack('<5I',cost,fetches,entryR,exitR,predicted['de'])+hashlib.sha256(after).digest()
            pending[0]=(frame,case,predicted['de']);previous[0]=n
        with contextlib.redirect_stdout(io.StringIO()):
            run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region})
        assert done and len(checked)==len(records) and pending[0] is None,(region,len(checked),len(records))
        data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
        rows.append(dict(region=region,cases=len(checked),raw_sha256=hashlib.sha256(data).hexdigest()))
        print(region,len(checked),'original8211 T/M1/R/DE/all400 bytes exact',flush=True)
    report=dict(source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),rows=rows,
                limits=['Original8211 andbank6 unmodified; custom DI caller loads A/currentcommand andDE.',
                        '29 effect IDs, ownership and active/bit6 flags, four DE values; synthetic state combinations.',
                        'Does not prove PSG waveform or full reader integration.'])
    (ROOT/'analysis/audio_restore_effect_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
