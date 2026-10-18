"""Observe actual SMS PSG calls and isolated original8000 calls, read-only."""
import subprocess
import sys
from actor_reference import ROOT

DECLARATION=r'''
/* GAW research: read-only original reader and PSG port timestamps. */
struct gaw_port_call { unsigned long long begin,end;unsigned de_before,de_after;unsigned char before[400],after[400]; };
struct gaw_port_write { unsigned long long master;unsigned call,value; };
static struct gaw_port_call gaw_port_calls[2048];
static struct gaw_port_write gaw_port_writes[32768];
static unsigned gaw_port_count,gaw_port_write_count,gaw_port_active,gaw_port_instruction_start;
__declspec(dllexport) unsigned gaw_port_samples(void) {return gaw_port_count;}
__declspec(dllexport) unsigned gaw_port_write_samples(void) {return gaw_port_write_count;}
__declspec(dllexport) const unsigned char *gaw_port_call_data(void) {return (const unsigned char *)gaw_port_calls;}
__declspec(dllexport) const unsigned char *gaw_port_write_data(void) {return (const unsigned char *)gaw_port_writes;}
void gaw_port_observe(unsigned cycles,unsigned value)
{
 struct gaw_port_write *e;
 if(!gaw_port_active || gaw_port_write_count>=32768) return;
 e=&gaw_port_writes[gaw_port_write_count++];
 e->master=gaw_elapsed+(unsigned)(cycles-gaw_port_instruction_start);
 e->call=gaw_port_active-1;e->value=value;
}
static void gaw_port_instruction(unsigned pc)
{
 struct gaw_port_call *e;
 gaw_port_instruction_start=Z80.cycles;
 if(pc==0x8000 && gaw_port_count<2048 && !gaw_port_active)
 {
  gaw_port_active=gaw_port_count+1;e=&gaw_port_calls[gaw_port_count];
  e->begin=gaw_elapsed;e->de_before=DED;memcpy(e->before,work_ram+0x1e00,400);
 }
 if(pc==0x3003 && gaw_port_active)
 {
  e=&gaw_port_calls[gaw_port_count++];e->end=gaw_elapsed;e->de_after=DED;
  memcpy(e->after,work_ram+0x1e00,400);gaw_port_active=0;
 }
}
'''

def main():
    folder=ROOT/'validation/loading-psg-deadlines';folder.mkdir(exist_ok=True)
    engine=ROOT.parents[1]/'work/genesis-plus-gx'
    paths=[engine/'core/z80/z80.c',engine/'core/memz80.c']
    original=[p.read_bytes() for p in paths]
    z80=original[0].decode()
    anchor='__declspec(dllexport) void gaw_timing_reset(void)'
    assert z80.count(anchor)==1
    z80=z80.replace(anchor,DECLARATION+'\n'+anchor)
    z80=z80.replace('gaw_elapsed=gaw_irq_elapsed=0;','gaw_port_count=gaw_port_write_count=gaw_port_active=0;gaw_elapsed=gaw_irq_elapsed=0;')
    anchor='gaw_timing_observe(pc);EXEC_INLINE(op,ROP());'
    assert z80.count(anchor)==1
    z80=z80.replace(anchor,'gaw_port_instruction(pc);'+anchor)
    mem=original[1].decode();anchor='psg_write(Z80.cycles, data);'
    assert mem.count(anchor)==5
    mem=mem.replace(anchor,'gaw_port_observe(Z80.cycles, data);'+anchor)
    mem='void gaw_port_observe(unsigned cycles,unsigned value);\n'+mem
    modified=[z80.encode(),mem.encode()]
    for name,body in zip(['z80-observer.txt','memz80-observer.txt'],modified):
        (folder/name).write_bytes(body)
    try:
        for path,body in zip(paths,modified):path.write_bytes(body)
        result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_audioports_libretro.dll'],capture_output=True,text=True,cwd=ROOT)
        (folder/'core-build.log').write_text(result.stdout+result.stderr)
        assert result.returncode==0,result.stdout+result.stderr
    finally:
        for path,body in zip(paths,original):path.write_bytes(body)
    assert all(p.read_bytes()==body for p,body in zip(paths,original))
    print('PSG port observer built; emulator sources restored.')

if __name__=='__main__':main()
