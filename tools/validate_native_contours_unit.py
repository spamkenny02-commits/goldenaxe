"""Original16-contour routine: independent map patterns, full VRAM and clock."""
import ctypes as c,itertools,json,os,struct,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_history_timed import fixture
from validate_native_hero_initialize import WRAPPER as HERO
from validate_native_room_contours import MODULES
WRAPPER=HERO.replace('source_hero_initialize.h','source_room_contours.h"\n#include "source_irq_video.h').replace('hero_case(','contours_case(')
WRAPPER=WRAPPER.replace('u32 *out,u8 *after)','u32 *out,u8 *after,u8 *vram)')
WRAPPER=WRAPPER.replace('SourceClock k;SourceIrqContext ctx={0};','SourceClock k;SourceIrqContext ctx={0};SourceIrqVideo video={0};u8 cram[32]={0},regs[16]={0};')
WRAPPER=WRAPPER.replace(' if(!source_clock_init(', ' video.rom=rom;video.vram=vram;video.cram=cram;video.registers=regs;ctx.video=source_irq_video_publish;ctx.video_context=&video;\n if(!source_clock_init(')
WRAPPER=WRAPPER.replace('source_hero_initialize(&k,&ctx,rom,0,0)', 'source_clock_plain(&k,10,1,source_irq_interrupt,&ctx) || !source_clock_checkpoint(&k,source_irq_interrupt,&ctx) || !source_room_contours(&k,&ctx,rom,vram,0,0) || !source_clock_plain(&k,10,1,source_irq_interrupt,&ctx) || !source_clock_plain(&k,10,1,source_irq_interrupt,&ctx) || !source_clock_checkpoint(&k,source_irq_interrupt,&ctx)')
def main():
 folder=ROOT/'validation/native-contours-unit';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'contours.dll')],env=env,capture_output=True,text=True);(folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 original=(ROOT/'input/original.sms').read_bytes();image=fixture(original,False);image[0x3000:0x3100]=bytes(image[0x3000:0x3100]).replace(bytes.fromhex('3a00ddb7'),bytes.fromhex('3af0ddb7'));image[0x1706:0x1720]=bytes(image[0x1706:0x1720]).replace(bytes.fromhex('3200ddc3'),bytes.fromhex('32f0ddc3'));image[0x16d0:0x16d3]=bytes.fromhex('c3b61f');cart=folder/'fixture.sms';cart.write_bytes(image)
 for a,b in [(0x137,0x327),(0x1fb6,0x2051),(0xb92,0xbc6),(0x10000,0x1c000)]:assert image[a:b]==original[a:b]
 u8=c.POINTER(c.c_uint8);lib=c.CDLL(str(folder/'contours.dll'));lib.contours_case.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,u8,u8,c.POINTER(c.c_uint32),u8,u8];lib.contours_case.restype=c.c_uint8;rom=(c.c_uint8*len(original)).from_buffer_copy(original)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loadertailrefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_foreground_phase_samples.restype=c.c_uint;engine.gaw_loader_entry_samples.restype=c.c_uint
 for n in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_loader_entry_events']:getattr(engine,n).restype=u8
 cases=list(itertools.product(range(4),range(4),[0,1]));results=[]
 for region in ['auto','pal']:
  engine.gaw_timing_reset();pending=[];checked=[0];initial=[None];digest=bytearray();ram_now=[None]
  def prepare(i,f):
   pattern,hud,skip=cases[i];tilemap=bytes((0 if pattern==0 else 255 if pattern==1 else n*17 if pattern==2 else (n//2)*37+(n&1)*8)&255 for n in range(1536))
   pending[:]=[(f,0x1600,tilemap),(f,0x34,bytes.fromhex('00dd')),(f,0x33,bytes([skip])),(f,0x42,bytes([0,0,0,hud])),(f,0x65,b'\4'),(f,0x1d00,b'\0'),(f,0x1e05,b'\x80'),(f,0x1e0a,b'\1'),(f,0x1df0,b'\1')]
  def observe(f,r):ram_now[0]=r
  def video(f,vram):
   count=engine.gaw_foreground_phase_samples();raw=c.string_at(engine.gaw_foreground_phase_events(),count*800);meta=c.string_at(engine.gaw_foreground_m1_events(),count*16);ends=[n for n in range(count) if struct.unpack_from('<Q',raw,n*800)[0]==0x1706]
   if ends:
    i=checked[0];a=next(n for n in range(count) if struct.unpack_from('<Q',raw,n*800)[0]==0x16d0);b=ends[0];phase=struct.unpack_from('<12I',raw,a*800+16);ta=struct.unpack_from('<Q',raw,a*800+8)[0];tb=struct.unpack_from('<Q',raw,b*800+8)[0];fa,refresh,_=struct.unpack_from('<Q2I',meta,a*16);fb,end_r,_=struct.unpack_from('<Q2I',meta,b*16);before=c.string_at(engine.gaw_loader_entry_events(),8200)[8:];body=(c.c_uint8*8192).from_buffer_copy(before);after=(c.c_uint8*8192)();pv=(c.c_uint8*16384).from_buffer_copy(initial[0]);out=(c.c_uint32*9)()
    assert lib.contours_case((c.c_uint32*12)(*phase),refresh,rom,body,out,after,pv),(region,i,'rejected')
    assert out[0]==tb-ta and out[2]+out[4]==fb-fa and out[7]==end_r,(region,i,'time/M1/R',list(out),tb-ta,fb-fa,end_r)
    assert bytes(pv)==vram[:16384],(region,i,'VRAM',[(hex(j),a,b) for j,(a,b) in enumerate(zip(pv,vram)) if a!=b][:8]);assert bytes(pv[0x3800:0x3e00])==before[0x1600:0x1c00]
    compact=bytes(after[:80])+bytes(after[0x1d00:0x1e00]);expected=raw[b*800+64:b*800+400];assert all(compact[j]==expected[j] for j in range(336) if j not in [0x1b,0x20,0x21,0x22,0x23]);assert bytes(after[0x1e00:0x1f90])==raw[b*800+400:b*800+800]
    digest.extend(bytes(pv));digest.extend(bytes(out));checked[0]+=1;engine.gaw_timing_reset()
    if checked[0]<len(cases):prepare(checked[0],f+1)
   initial[0]=vram[:16384]
  prepare(0,10);run(cart,len(cases)*40+20,folder/region,set(),[],core=core,skip_intro=False,ram_writes=pending,ram_observer=observe,vram_observer=video,stop_when=lambda:checked[0]==len(cases),core_options={'genesis_plus_gx_region_detect':region});assert checked[0]==len(cases);results.append(dict(region=region,cases=checked[0],output_sha256=sha(digest)));print(results[-1],flush=True)
 report=dict(passed=True,cases=sum(r['cases'] for r in results),rows=results,source_sha256=sha(original),fixture_sha256=sha(image),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},production_clock_wired=False,limits=['Original1FB6..2050, IRQ, waits and banks4/6 unchanged. Test caller JP from16D0 and return/JP to1706 are explicitly included in native timing. Four full tilemap patterns, all HUD flags and palette skips, both regions. Entire16KiB VRAM,331 RAM/400 audio,time/M1/R checked.','Controlled caller and inactive audio. No physical MD pacing/byte deadlines or full game proof.'])
 (ROOT/'analysis/native_contours_unit_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
if __name__=='__main__':main()
