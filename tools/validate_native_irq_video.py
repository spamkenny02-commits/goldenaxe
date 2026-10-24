"""Unchanged full IRQ vs native VRAM/CRAM/register delivery."""
import ctypes as c,itertools,json,os,struct,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_history_timed import fixture
WRAPPER=r'''#include "source_irq_video.h"
u8 video_case(const u8 *rom,const u8 *sram,u8 *body,u8 *vram,u8 *cram,u8 *regs,u32 *out)
{
 SourceIrqContext ctx={0};SourceIrqVideo v={0};SourceClockIrq e={0};u8 ram[336];u16 n,count;
 for(n=0;n<80;n++){ram[n]=body[n];}for(n=0;n<256;n++){ram[80+n]=body[0x1d00+n];}
 ctx.ram=ram;ctx.audio=body+0x1e00;ctx.full_ram=body;v.rom=rom;v.sram=sram;v.vram=vram;v.cram=cram;v.registers=regs;
 if(!source_irq_video_publish(&v,&ctx,&e,&count)){out[0]=v.error;return 0;}
 out[0]=v.bytes;out[1]=count;return 1;
}
'''
def main():
 folder=ROOT/'validation/native-irq-video';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 args=['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),str(ROOT/'megadrive/src/source_irq_video.c'),str(folder/'wrapper.c'),'-o',str(folder/'video.dll')]
 built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr
 original=(ROOT/'input/original.sms').read_bytes();image=fixture(original,False);image[0x3000:0x3100]=bytes(image[0x3000:0x3100]).replace(bytes.fromhex('3ea0d3bf'),bytes.fromhex('3e80d3bf')).replace(bytes.fromhex('3a00ddb7'),bytes.fromhex('3af0ddb7'));image[0x1706:0x1720]=bytes(image[0x1706:0x1720]).replace(bytes.fromhex('3200ddc3'),bytes.fromhex('32f0ddc3'));image[0x16d0:0x16d4]=bytes.fromhex('f5c33701');cart=folder/'fixture.sms';cart.write_bytes(image)
 for a,b in [(0x137,0x327),(0x3b07,0x3b67),(0x1f54,0x1f78),(0x10000,0x1c000)]:assert image[a:b]==original[a:b]
 lib=c.CDLL(str(folder/'video.dll'));u8=c.POINTER(c.c_uint8);lib.video_case.argtypes=[u8]*6+[c.POINTER(c.c_uint32)];lib.video_case.restype=c.c_uint8;rom=(c.c_uint8*len(original)).from_buffer_copy(original)
 sram_bytes=bytes((n*29+7)&255 for n in range(16384));(folder/'sram.bin').write_bytes(sram_bytes);sram=(c.c_uint8*16384).from_buffer_copy(sram_bytes)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loadertailrefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_foreground_phase_samples.restype=c.c_uint;engine.gaw_loader_entry_samples.restype=c.c_uint
 for n in ['gaw_foreground_phase_events','gaw_loader_entry_events']:getattr(engine,n).restype=u8
 cases=list(itertools.product([(0,0),(4,0x81c3),(5,0x9e38)],range(4),range(6),[0,1]));results=[];vectors=[]
 for region in ['auto','pal']:
  engine.gaw_timing_reset();pending=[];checked=[0];initial=[None];digest=bytearray()
  def prepare(i,f):
   (bank,pointer),hud,q,skip=cases[i];descriptors=[b'',bytes.fromhex('01020081007802'),bytes.fromhex('01800081006001'),bytes.fromhex('02020300d1'),bytes.fromhex('0102008100780202020300d1'),bytes.fromhex('02020700dd')][q];end=0xdd00+len(descriptors);queue=descriptors+b'\0';sat=bytes((n*17+i)&255 for n in range(192));palette=bytes((n*11+i)&255 for n in range(32));data=bytes((n*19+i)&255 for n in range(256))
   pending[:]=[(f,0x18,bytes([i&255,(i*7)&255,0xff])),(f,0x2e,b'\1'),(f,0x33,bytes([skip])),(f,0x34,end.to_bytes(2,'little')),(f,0x42,bytes([bank])+pointer.to_bytes(2,'little')+bytes([hud])),(f,0x1d00,queue),(f,0x1d40,sat),(f,0x1ca0,palette),(f,0x1b00,data),(f,0x1100,data),(f,0x1e05,b'\x80'),(f,0x1e0a,b'\1'),(f,0x1df0,b'\1')]
  def video(f,vram):
   state=c.create_string_buffer(engine.retro_serialize_size());assert engine.retro_serialize(state,len(state));base=16+8192+16+1024;raw=state.raw;cram=bytes(raw[base+65536+n*2]&63 for n in range(32));regs=raw[base+0x10100:base+0x10110];snapshot=(vram[:16384],cram,regs)
   count=engine.gaw_foreground_phase_samples();events=c.string_at(engine.gaw_foreground_phase_events(),count*800);done=any(struct.unpack_from('<Q',events,n*800)[0]==0x1706 for n in range(count))
   if done:
    i=checked[0];assert initial[0] is not None;before=c.string_at(engine.gaw_loader_entry_events(),8200)[8:];body=(c.c_uint8*8192).from_buffer_copy(before);pv=(c.c_uint8*16384).from_buffer_copy(initial[0][0]);pc=(c.c_uint8*32).from_buffer_copy(initial[0][1]);pr=(c.c_uint8*16).from_buffer_copy(initial[0][2]);out=(c.c_uint32*2)();assert lib.video_case(rom,sram,body,pv,pc,pr,out),(region,i,cases[i],list(out))
    assert bytes(pv)==snapshot[0],(region,i,cases[i],'VRAM',[(hex(n),a,b) for n,(a,b) in enumerate(zip(pv,snapshot[0])) if a!=b][:12]);assert bytes(pc)==cram,(region,i,'CRAM',list(pc),list(cram));assert bytes(pr[8:11])==regs[8:11],(region,i,'registers')
    assert bytes(body)==before,'video must not mutate IRQ RAM';digest.extend(bytes(pv));digest.extend(bytes(pc));digest.extend(bytes(pr[8:11]));vectors.append(dict(before=list(before),vram=list(initial[0][0]),cram=list(initial[0][1]),registers=list(initial[0][2]),after_vram=list(pv),after_cram=list(pc),after_registers=list(pr),output=list(out)));checked[0]+=1;engine.gaw_timing_reset()
    if checked[0]<len(cases):prepare(checked[0],f+1)
   initial[0]=snapshot
  prepare(0,10);run(cart,len(cases)*6+20,folder/region,set(),[],core=core,skip_intro=False,ram_writes=pending,vram_observer=video,sram_in=folder/'sram.bin',stop_when=lambda:checked[0]==len(cases),core_options={'genesis_plus_gx_region_detect':region});assert checked[0]==len(cases),(region,checked[0]);results.append(dict(region=region,cases=checked[0],output_sha256=sha(digest)));print(results[-1],flush=True)
 (folder/'cases.json').write_bytes((json.dumps(vectors,separators=(',',':'))+'\n').encode());report=dict(passed=True,cases=sum(r['cases'] for r in results),rows=results,source_sha256=sha(original),fixture_sha256=sha(image),module_sha256={'source_irq_video.c':sha((ROOT/'megadrive/src/source_irq_video.c').read_bytes())},production_clock_wired=False,limits=['Unchanged original full IRQ/banks4/6 under a controlled caller; hardware IRQ generation disabled. Bitmap absent/bank4/bank5, all HUD selections, palette skip, ROM/SRAM/row/mixed/self-reading queues in both regions. Entire16KiB VRAM,32 effective6bit CRAM and scrolling/line registers compared.','Physical MD scheduling, nested IRQs, exact byte deadlines, full game and all malformed/zero-count descriptors remain unverified.'])
 (ROOT/'analysis/native_irq_video_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
if __name__=='__main__':main()
