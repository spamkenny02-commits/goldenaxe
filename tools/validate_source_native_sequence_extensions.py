"""Original8357 direct evidence for nonzero8211 restoration and mirrored streams."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct
from actor_reference import ROOT
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from validate_native_audio_sequence import compile_helper,Output
from validate_native_audio_prefix import Work
from run_core import run

def main():
    folder,dll_native,function=compile_helper();suites=[];summary=[]
    records=[(a&255,a>>8,flags,tone,command,latch,noise,borrowed) for a,flags,tone,command,latch,noise,borrowed in
             itertools.product([0x3c00,0x3c08],[128,132,192],[128,160,192,224],[0x90,0x91,0xac],[0,1,128,255],[0,128,192],[0,128])]
    definitions=[('restore',records,[0x43,0x44,0x40,0x41,14,15,0x160,0x130],None)]
    for target,addresses in [(0x80,[0xde80,0xfe80]),(0x180,[0xdf80,0xff80])]:
        rows=[(a&255,a>>8,flags,scale,0,0,0xea,value,3,0x81,7) for a,flags,scale,value in
              itertools.product(addresses,[0,4,8,128],[0,1,2,255],[0,127,128,255])]
        definitions.append((f'mirror-{target:03x}',rows,[0x43,0x44,0x40,0x42,0x47,14]+list(range(target,target+5)),target))
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_prefix_samples','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_prefix_tstates','gaw_prefix_m1_fetches']:getattr(dll,name).restype=c.c_uint64
    for name in ['gaw_prefix_entry','gaw_prefix_return']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    for kind,records,offsets,target in definitions:
        rom,base=generate(kind,records,offsets,0x8357,'audio-sequence-extensions',0xde40,True)
        image=bytearray(rom.read_bytes())
        if target is None:image[0x3c00]=0xf1;image[0x3c08]=0xf2
        assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000];rom.write_bytes(image)
        low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);canonical=[]
        for region in ['auto','pal']:
            dll.gaw_timing_reset();previous=[0];done=[];checked={};raw=[]
            def observe(frame,ram):
                if ram[4]:done.append(frame)
                count=dll.gaw_prefix_samples()
                if count==previous[0]:return
                assert count==previous[0]+1
                case=int.from_bytes(ram[:2],'little');before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
                inputs=image[0x80000+case*16:0x80000+(case+1)*16];initial=bytearray(image[0x3430:0x3430+400])
                for offset,value in zip(offsets,inputs):initial[offset]=value
                assert before==initial
                cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();de=dll.gaw_envelope_return_de();unwind=dll.gaw_envelope_did_unwind()
                entry=dll.gaw_prefix_refresh_before();exit=dll.gaw_prefix_refresh_after();assert exit==advance_refresh(entry,fetches+1)
                state=(c.c_uint8*400).from_buffer_copy(before);work=Work();output=Output()
                assert function(state,0x40,low,32768,bank,c.byref(work),c.byref(output)) and not output.error
                assert (bytes(state),work.tstates,work.fetches,output.de,output.unwind)==(after,cost,fetches,de,unwind),(kind,region,case,'native/source',work.tstates,cost,work.fetches,fetches,output.de,de)
                row=dict(input=list(inputs),patches=[(i,v) for i,v in enumerate(after) if before[i]!=v],tstates=cost,fetches=fetches,de=de,unwind=unwind)
                if region=='auto':canonical.append(row)
                else:assert row==canonical[case]
                checked[case]=row;raw.append(struct.pack('<6I',cost,fetches,entry,exit,de,unwind)+before+after);previous[0]=count
            with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,base/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            assert done and len(checked)==len(records),(kind,region,len(checked),len(records))
            data=b''.join(raw);(base/f'{region}-records.bin').write_bytes(data)
            summary.append(dict(kind=kind,region=region,cases=len(checked),raw_sha256=hashlib.sha256(data).hexdigest()));print(kind,region,len(checked),'source/native400 bytes,T/M1,DE/unwind; sourceR exact',flush=True)
        suites.append(dict(kind=kind,fixture=str(rom.relative_to(ROOT)),fixture_sha256=hashlib.sha256(image).hexdigest(),offsets=offsets,cases=canonical))
    (folder/'extension-cases.json').write_text(json.dumps(suites,separators=(',',':'))+'\n')
    report=dict(rows=summary,source_sha256=hashlib.sha256(SOURCE).hexdigest(),
                native_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_sequence.c').read_bytes()).hexdigest(),
                limits=['Original8357/bank6 unchanged; custom DI two-level callers. Direct native-vs-source state,T/M1,DE/unwind; Rdelta observed.',
                        'Includes F1/F2 with active8211 restoration and EA enable/disable in DE/FE/DF/FF streams.',
                        'Controlled fixtures; PSG bytes/waveforms andfull game clock not established by this check.'])
    (ROOT/'analysis/source_native_sequence_extensions_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
