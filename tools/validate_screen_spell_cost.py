"""Check instruction counts against live unchanged SMS routines, excluding IRQs."""
import ctypes as c,gzip,json,os,random,subprocess
from run_core import ROOT
from archive_lossless_evidence import sha
from screen_spell_cost import level1_cost,level2_cost,advance1,advance2
class Work(c.Structure):_fields_=[('tstates',c.c_uint32),('fetches',c.c_uint32)]
class Output(c.Structure):_fields_=[('count',c.c_uint16),('y_end',c.c_uint16),('xy_end',c.c_uint16),('rotating',c.c_uint8),('bank',c.c_uint8)]
def read(path):
    if path.exists():return path.read_bytes()
    archive=ROOT/'analysis/screen-spell-clock-v0251';manifest=json.loads((archive/'manifest.json').read_bytes());item=manifest['compressed'][path.relative_to(ROOT).as_posix()];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'];return raw

def main():
    folder=ROOT/'validation/screen-spell-cost-host';folder.mkdir(exist_ok=True)
    (folder/'types.h').write_bytes(b'#include <stdint.h>\ntypedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef int16_t s16;typedef uint32_t u32;typedef int32_t s32;\n')
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];dllpath=folder/'scene_cost.dll'
    subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-shared','-I'+str(folder),'-I'+str(ROOT/'megadrive/src'),str(ROOT/'megadrive/src/source_sprite_scene_cost.c'),str(ROOT/'megadrive/src/source_sprite_scene_tstates.c'),str(ROOT/'megadrive/src/source_irq.c'),'-o',str(dllpath)],env=env,check=True,capture_output=True)
    lib=c.CDLL(str(dllpath));lib.source_sprite_scene_cost.restype=c.c_uint8
    rom=(ROOT/'input/original.sms').read_bytes();bank=(c.c_ubyte*16384).from_buffer_copy(rom[0x30000:0x34000]);low=(c.c_ubyte*32768).from_buffer_copy(rom[:32768]);cases=[]
    for tag in ['level1','level1-pal','level2','level2-pal']:
        one=tag.startswith('level1');path=ROOT/f'validation/screen-spell-cost2-{tag}-sms';events=json.loads(read(path/'cycle-events.json'));snapshots=read(path/'scenes.bin');work=bytearray(1024)
        for n in range(22 if one else 4):work[n*32]=22 if one else 4;work[n*32+1]=255-n if one else n*16
        pending=None;body=[];scenes=[];scene=None
        for e in events:
            if e[1]==(0x6b33 if one else 0x6c65):pending=e
            elif e[1]==(0x6b94 if one else 0x6cd2) and pending:
                value=((e[2]-pending[2])-(e[3]-pending[3]))//15;expected=level1_cost(work) if one else level2_cost(work,rom[0x6cf0:0x6d2c]);assert value==expected,(tag,len(body),expected,value);body.append(value);(advance1 if one else advance2)(work);pending=None
            if e[1]==0x0938:scene=e
            elif e[1]==(0x6b9e if one else 0x6cd5) and scene:
                scenes.append(((e[2]-scene[2])-(e[3]-scene[3]))//15);scene=None
        assert len(scenes)==len(body)==len(snapshots)//8192==(88 if one else 28)
        for n,expected in enumerate(scenes):
            ram_fast=(c.c_ubyte*8192).from_buffer_copy(snapshots[n*8192:(n+1)*8192]);fast_t=c.c_uint32();fast_out=Output();assert lib.source_sprite_scene_tstates(ram_fast,bank,low,c.byref(fast_t),c.byref(fast_out));assert fast_t.value==expected,(tag,n,'fast',fast_t.value,expected)
            ram=(c.c_ubyte*8192).from_buffer_copy(snapshots[n*8192:(n+1)*8192]);cost=Work();out=Output();assert lib.source_sprite_scene_cost(ram,bank,low,c.byref(cost),c.byref(out));assert cost.tstates==expected,(tag,n,cost.tstates,expected);assert bytes(ram)==bytes(ram_fast),(tag,n,'RAM mutation');assert bytes(out)==bytes(fast_out)
        cases.append(dict(case=tag,map_body_cases=len(body),sprite_scene_cases=len(scenes),input_scene_sha256=sha(snapshots)))
    rng=random.Random(0x6e3f0938);equivalence=0
    seed=read(ROOT/'validation/screen-spell-cost2-level1-sms/scenes.bin')[:8192]
    for case in range(512):
        state=bytearray(seed);state[0x47]=[0,1,7,8,12,32][case%6];state[0x1b]=0x80+(64 if case&1 else 0);state[0x2f]=case&255
        for slot in range(32):
            off=0x300+slot*48
            if slot==0:state[off+0x11]=rng.randrange(256);state[off+0x13]=rng.randrange(256);continue
            if slot>=16:
                state[off:off+48]=bytes(48);state[off]=0x26;state[off+8:off+10]=b'\xcc\x90'
            state[off+3]=1 if rng.randrange(3) else 0;state[off+0x11]=rng.randrange(256);state[off+0x13]=rng.randrange(256)
        a=(c.c_ubyte*8192).from_buffer_copy(state);b=(c.c_ubyte*8192).from_buffer_copy(state);wa=Work();wb=c.c_uint32();oa=Output();ob=Output()
        accepted=lib.source_sprite_scene_cost(a,bank,low,c.byref(wa),c.byref(oa));fast=lib.source_sprite_scene_tstates(b,bank,low,c.byref(wb),c.byref(ob));assert accepted==fast
        if accepted:
            assert wa.tstates==wb.value and bytes(a)==bytes(b) and bytes(oa)==bytes(ob),(case,wa.tstates,wb.value,[(i,x,y) for i,(x,y) in enumerate(zip(bytes(a),bytes(b))) if x!=y][:8],bytes(oa).hex(),bytes(ob).hex())
            equivalence+=1
    class IrqInput(c.Structure):_fields_=[('raster',c.c_uint32),('lines',c.c_uint16),('tile_count',c.c_uint16),('joy',c.c_uint8),('reset_mask',c.c_uint8),('compensation',c.c_uint8)]
    class IrqOutput(c.Structure):_fields_=[('stages',Work*9),('whole',Work),('palette_taken',c.c_uint16),('reset_requested',c.c_uint8)]
    fixed=json.loads((ROOT/'analysis/screen_spell_assets.json').read_bytes())['irq_empty_fixed_tstates'];irq_cases=[]
    for index,(lines,comp) in enumerate([(262,0),(262,128),(313,0),(313,128)]):
        state=(c.c_ubyte*336)();state[0x2e]=1;state[0x35]=0xdd;input_irq=IrqInput(193*3420+72*15,lines,0,0,16,comp);output_irq=IrqOutput();reader=Work()
        assert lib.source_irq(state,c.byref(input_irq),c.byref(reader),c.byref(output_irq));assert output_irq.whole.tstates==fixed[index]
        irq_cases.append(dict(lines=lines,compensation=comp,tstates=fixed[index]))
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),passed=True,cases=cases,map_body_cases=sum(r['map_body_cases'] for r in cases),sprite_scene_cases=sum(r['sprite_scene_cases'] for r in cases),fast_randomized_total_cases=512,fast_randomized_accepted_cases=equivalence,fast_randomized_rejection_agreements=512-equivalence,empty_irq_wrapper_cases=irq_cases,foreground_cost_verified=True,physical_scheduler_verified=False,full_game_verified=False,limits=['Controlled original spell cases; exact foreground T-state counts only. Interrupt, wait, initial raster and native scheduling are separate work.','Cost-only sprite helper supports low ROM descriptors and mutates private shadow RAM; the existing timed API remains unchanged.'])
    (ROOT/'analysis/screen_spell_cost_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report)
if __name__=='__main__':main()
