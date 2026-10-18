"""Read-only HV/68000 PSG bus observer. Restore both upstream files exactly."""
import hashlib
import subprocess
import sys
from actor_reference import ROOT

OBSERVER = r'''
/* Host-only bus observations. No emulated state/cycle changes. */
#define GAW_IO_CAPACITY 131072
static unsigned gaw_io_events[GAW_IO_CAPACITY][4];
static unsigned gaw_io_count,gaw_io_overflow,gaw_io_enabled;
__declspec(dllexport) void gaw_io_reset(unsigned enabled) {
 gaw_io_count=gaw_io_overflow=0;gaw_io_enabled=enabled;
}
__declspec(dllexport) unsigned gaw_io_size(void) {return gaw_io_count;}
__declspec(dllexport) unsigned gaw_io_errors(void) {return gaw_io_overflow;}
__declspec(dllexport) const unsigned *gaw_io_data(void) {return &gaw_io_events[0][0];}
void gaw_io_observe(unsigned kind,unsigned cycles,unsigned value) {
 unsigned *event;
 if(!gaw_io_enabled) return;
 if(gaw_io_count==GAW_IO_CAPACITY) {gaw_io_overflow++;return;}
 event=gaw_io_events[gaw_io_count++];
 event[0]=kind;event[1]=cycles;event[2]=value;
 event[3]=m68k_get_reg(M68K_REG_PC);
}
'''


def main():
    folder=ROOT/'validation/md-io-clock';folder.mkdir(exist_ok=True)
    core=ROOT.parents[1]/'work/genesis-plus-gx/core'
    paths=[core/'vdp_ctrl.c',core/'mem68k.c']
    originals={p:p.read_bytes() for p in paths}
    vdp=originals[paths[0]].decode()
    anchor='unsigned int vdp_hvc_r(unsigned int cycles)'
    assert vdp.count(anchor)==1
    vdp=vdp.replace(anchor,OBSERVER+'\n'+anchor)
    start=vdp.index(anchor);end=vdp.index('void vdp_test_w',start)
    section=vdp[start:end]
    assert section.count('return (data);')==1
    section=section.replace('return (data);','gaw_io_observe(1,cycles,data);\n  return (data);')
    vdp=vdp[:start]+section+vdp[end:]
    mem=originals[paths[1]].decode()
    for call,kind in [('psg_write(m68k.cycles, data);',2),('psg_write(m68k.cycles, data & 0xFF);',3)]:
        assert mem.count(call)==1
        mem=mem.replace(call,f'gaw_io_observe({kind},m68k.cycles,data & 0xff);\n      '+call)
    mem='extern void gaw_io_observe(unsigned,unsigned,unsigned);\n'+mem
    modified={paths[0]:vdp.encode(),paths[1]:mem.encode()}
    try:
        for path,raw in modified.items():
            (folder/(path.name+'-observer.txt')).write_bytes(raw);path.write_bytes(raw)
        result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_io_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
        (folder/'core-build.log').write_text(result.stdout+result.stderr)
        assert not result.returncode,result.stdout+result.stderr
    finally:
        for path,raw in originals.items():path.write_bytes(raw)
    for path,raw in originals.items():
        assert path.read_bytes()==raw
        (folder/(path.name+'-original.sha256')).write_text(hashlib.sha256(raw).hexdigest()+'\n')
    print('Read-only HV/PSG IO core built; both original files restored.')


if __name__=='__main__':main()
