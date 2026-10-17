"""Read-only source wait entry/restore/caller snapshots with logicalM1/R."""
import subprocess
import sys
from actor_reference import ROOT

OBSERVER='''
struct gaw_wait_return_record {
 struct gaw_fore_phase first,restore,last;
 struct gaw_fore_M1 mfirst,mrestore,mlast;
 unsigned return_pc,bank_saved,bank_final;
};
static struct gaw_wait_return_record gaw_wait_returns[8192];
static unsigned gaw_wait_return_count,gaw_wait_return_active,gaw_wait_return_pc;
__declspec(dllexport) unsigned gaw_wait_return_samples(void) { return gaw_wait_return_count; }
__declspec(dllexport) unsigned gaw_wait_return_stride(void) { return sizeof(struct gaw_wait_return_record); }
__declspec(dllexport) const unsigned char *gaw_wait_return_events(void) { return (const unsigned char *)gaw_wait_returns; }
static void gaw_wait_return_snapshot(struct gaw_fore_phase *e,struct gaw_fore_M1 *m,unsigned pc)
{
 e->pc=pc;e->master=gaw_elapsed;
 e->phase[0]=Z80.cycles;e->phase[1]=v_counter;e->phase[2]=mcycles_vdp;
 e->phase[3]=lines_per_frame;e->phase[4]=vc_max;e->phase[5]=interlaced;
 e->phase[6]=reg[1];e->phase[7]=system_hw;e->phase[8]=IFF1;
 e->phase[9]=Z80.after_ei;e->phase[10]=Z80.irq_state;e->phase[11]=reg[0];
 memcpy(e->ram,work_ram,80);memcpy(e->ram+80,work_ram+0x1d00,256);
 memcpy(e->sound,work_ram+0x1e00,400);
 m->fetches=gaw_M1_fetches;m->refresh=(R&127)|R2;m->pad=0;
}
static void gaw_wait_return_observe(unsigned pc)
{
 struct gaw_wait_return_record *e;
 if(gaw_wait_return_count>=8192) return;
 e=gaw_wait_returns+gaw_wait_return_count;
 /* Finalize before a possible next wait at the same return PC0B95. */
 if(gaw_wait_return_active && pc==gaw_wait_return_pc)
 {
  gaw_wait_return_snapshot(&e->last,&e->mlast,pc);e->return_pc=pc;
  e->bank_final=work_ram[0x1fff];gaw_wait_return_count++;gaw_wait_return_active=0;
  if(gaw_wait_return_count>=8192) return;
  e=gaw_wait_returns+gaw_wait_return_count;
 }
 if(pc==0x0b95)
 {
  memset(e,0,sizeof(*e));gaw_wait_return_snapshot(&e->first,&e->mfirst,pc);
  e->bank_saved=work_ram[0x1fff];gaw_wait_return_active=1;gaw_wait_return_pc=0x10000;
 }
 if(pc==0x0bb3 && !gaw_wait_return_active)
 {
  memset(e,0,sizeof(*e));gaw_wait_return_snapshot(&e->first,&e->mfirst,pc);
  e->bank_saved=work_ram[(SP+1)&0x1fff];gaw_wait_return_active=1;gaw_wait_return_pc=0x10000;
 }
 if(!gaw_wait_return_active) return;
 if(pc==0x0bb3) gaw_wait_return_snapshot(&e->restore,&e->mrestore,pc);
 if(pc==0x0bc5 && SP>=0xc000)
  gaw_wait_return_pc=work_ram[SP&0x1fff]|(work_ram[(SP+1)&0x1fff]<<8);
}
'''


def main():
    folder=ROOT/'analysis/wait-return-observer-v0194';folder.mkdir(exist_ok=True)
    path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
    source=(ROOT/'analysis/wait-refresh-v0183/z80-wait-refresh.txt').read_text()
    anchor='__declspec(dllexport) void gaw_timing_reset(void)'
    assert source.count(anchor)==1;source=source.replace(anchor,OBSERVER+'\n'+anchor)
    anchor='gaw_fore_phase_count=0; }';assert source.count(anchor)==1
    source=source.replace(anchor,'gaw_fore_phase_count=gaw_wait_return_count=gaw_wait_return_active=0;gaw_wait_return_pc=0x10000; }')
    anchor=' gaw_fore_phase_observe(pc);';assert source.count(anchor)==1
    source=source.replace(anchor,' gaw_wait_return_observe(pc);\n'+anchor)
    data=source.encode();target=folder/'z80-wait-return-v2.txt'
    if target.exists():assert target.read_bytes()==data
    else:target.write_bytes(data)
    try:
        path.write_bytes(data)
        result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_waitcomplete_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
        (ROOT/'validation/wait-return-core-build.log').write_text(result.stdout+result.stderr)
        assert result.returncode==0,(result.stdout+result.stderr)[-4000:]
    finally:path.write_bytes(original)
    assert path.read_bytes()==original
    print('Read-only wait return observer built; emulator source restored.')


if __name__=='__main__':main()
