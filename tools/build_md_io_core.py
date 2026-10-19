"""Read-only HV/PSG/BUSREQ observer. Restore upstream files exactly."""
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
    native_hv='--native-hv' in sys.argv
    z80_psg='--z80-psg' in sys.argv
    native_hv=native_hv or z80_psg
    folder=ROOT/('validation/md-z80-psg-io-core' if z80_psg else 'validation/md-service-io-core' if native_hv else 'validation/md-io-clock');folder.mkdir(exist_ok=True)
    core=ROOT.parents[1]/'work/genesis-plus-gx/core'
    paths=[core/'vdp_ctrl.c',core/'mem68k.c']
    if z80_psg:paths.append(core/'membnk.c')
    originals={p:p.read_bytes() for p in paths}
    vdp=originals[paths[0]].decode()
    anchor='unsigned int vdp_hvc_r(unsigned int cycles)'
    assert vdp.count(anchor)==1
    vdp=vdp.replace(anchor,OBSERVER+'\n'+anchor)
    if z80_psg:
        extra='void gaw_z80_io_observe(unsigned kind,unsigned cycles,unsigned value,unsigned pc) {unsigned before=gaw_io_count;gaw_io_observe(kind,cycles,value);if(gaw_io_count!=before) gaw_io_events[before][3]=pc;}\n__declspec(dllexport) const unsigned char *gaw_z80_ram(void) {return zram;}\n__declspec(dllexport) unsigned gaw_z80_pc(void) {return Z80.pc.w.l;}\n__declspec(dllexport) unsigned gaw_z80_bank(void) {return zbank;}\n__declspec(dllexport) unsigned gaw_z80_ix(void) {return Z80.ix.w.l;}\n'
        vdp=vdp.replace(anchor,extra+anchor)
    start=vdp.index(anchor);end=vdp.index('void vdp_test_w',start)
    section=vdp[start:end]
    assert section.count('return (data);')==1
    section=section.replace('return (data);','gaw_io_observe(1,cycles,data);\n  return (data);')
    vdp=vdp[:start]+section+vdp[end:]
    mem=originals[paths[1]].decode()
    if native_hv:
        assert mem.count('vdp_hvc_r(m68k.cycles)')==3
        mem=mem.replace('vdp_hvc_r(m68k.cycles)','gaw_native_hvc(m68k.cycles)')
        anchor='unsigned int vdp_read_byte(unsigned int address)';assert mem.count(anchor)==1
        helper='static unsigned gaw_native_hvc(unsigned cycles) {unsigned value=vdp_hvc_r(cycles);gaw_io_observe(4,cycles,value);return value;}\n\n'
        mem=mem.replace(anchor,helper+anchor)
    for call,kind in [('psg_write(m68k.cycles, data);',2),('psg_write(m68k.cycles, data & 0xFF);',3)]:
        assert mem.count(call)==1
        mem=mem.replace(call,f'gaw_io_observe({kind},m68k.cycles,data & 0xff);\n      '+call)
    mem='extern void gaw_io_observe(unsigned,unsigned,unsigned);\n'+mem
    if z80_psg:
        for call,value in [('gen_zbusreq_w(data & 1, m68k.cycles);','data & 1'),('gen_zbusreq_w((data >> 8) & 1, m68k.cycles);','(data >> 8) & 1')]:
            assert mem.count(call)==1;mem=mem.replace(call,'gaw_io_observe(7,m68k.cycles,'+value+');\n        '+call)
    modified={paths[0]:vdp.encode(),paths[1]:mem.encode()}
    if z80_psg:
        bank=originals[paths[2]].decode();anchor='psg_write(Z80.cycles, data);';assert bank.count(anchor)==1
        bank=bank.replace(anchor,'gaw_z80_io_observe(5,Z80.cycles,data,Z80.pc.w.l);\n        '+anchor)
        assert bank.count('vdp_hvc_r(Z80.cycles)')==2
        bank=bank.replace('vdp_hvc_r(Z80.cycles)','gaw_z80_hvc()')
        anchor='unsigned int zbank_read_vdp(unsigned int address)';assert bank.count(anchor)==1
        helper='static unsigned gaw_z80_hvc(void) {unsigned value=vdp_hvc_r(Z80.cycles);gaw_z80_io_observe(6,Z80.cycles,value,Z80.pc.w.l);return value;}\n'
        bank=bank.replace(anchor,helper+anchor)
        bank='extern void gaw_z80_io_observe(unsigned,unsigned,unsigned,unsigned);\n'+bank
        modified[paths[2]]=bank.encode()
    try:
        for path,raw in modified.items():
            (folder/(path.name+'-observer.txt')).write_bytes(raw);path.write_bytes(raw)
        target='genesis_plus_gx_z80_psg_io_libretro.dll' if z80_psg else 'genesis_plus_gx_service_io_libretro.dll' if native_hv else 'genesis_plus_gx_io_libretro.dll'
        result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target',target],cwd=ROOT,capture_output=True,text=True)
        (folder/'core-build.log').write_text(result.stdout+result.stderr)
        assert not result.returncode,result.stdout+result.stderr
    finally:
        for path,raw in originals.items():path.write_bytes(raw)
    for path,raw in originals.items():
        assert path.read_bytes()==raw
        (folder/(path.name+'-original.sha256')).write_text(hashlib.sha256(raw).hexdigest()+'\n')
    print('Read-only HV/PSG IO core built; all original files restored.')


if __name__=='__main__':main()
