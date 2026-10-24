"""Original0ACE fade against native palette/wait/IRQ clock, no average timing."""
import ctypes as c,itertools,json,os,struct,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_history_timed import fixture
from validate_native_hero_initialize import WRAPPER as HERO_WRAPPER
from validate_native_room_reveal import MODULES
WRAPPER=HERO_WRAPPER.replace('source_hero_initialize.h','source_room_reveal.h').replace('hero_case(','fade_case(').replace('source_hero_initialize(&k,&ctx,rom,0,0)','source_room_reveal_fade(&k,&ctx,rom,0,0)')

WRAPPER=WRAPPER.replace('if(!source_room_reveal_fade(&k,&ctx,rom,0,0))return 0;', 'if(!source_room_reveal_fade(&k,&ctx,rom,0,0)){out[0]=k.elapsed;out[1]=ctx.error;out[2]=k.irq_count;out[3]=ctx.last_irq.whole.tstates;return 0;}')

def main():
 folder=ROOT/'validation/native-room-fade';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'fade.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 original=(ROOT/'input/original.sms').read_bytes();rom=fixture(original,True);rom[0x3000:0x3100]=bytes(rom[0x3000:0x3100]).replace(bytes.fromhex('3a00ddb7'),bytes.fromhex('3af0ddb7'));rom[0x1706:0x1720]=bytes(rom[0x1706:0x1720]).replace(bytes.fromhex('3200ddc3'),bytes.fromhex('32f0ddc3'));rom[0x16d0:0x16d7]=bytes.fromhex('210617e5c3ce0a');assert rom[0xace:0xb12]==original[0xace:0xb12] and rom[0xb92:0xbc6]==original[0xb92:0xbc6] and rom[0x137:0x226]==original[0x137:0x226] and rom[0x10000:0x1c000]==original[0x10000:0x1c000]
 cart=folder/'fixture.sms';cart.write_bytes(rom);lib=c.CDLL(str(folder/'fade.dll'));u8=c.POINTER(c.c_uint8);lib.fade_case.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,u8,u8,c.POINTER(c.c_uint32),u8];lib.fade_case.restype=c.c_uint8;source_rom=(c.c_uint8*len(original)).from_buffer_copy(original)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loadertailrefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_foreground_phase_samples.restype=c.c_uint;engine.gaw_loader_entry_samples.restype=c.c_uint
 for n in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_loader_entry_events']:getattr(engine,n).restype=u8
 cases=list(itertools.product(range(6),[0,1],[0,1],[0,1800]));results=[];vectors=[]
 for region in ['auto','pal']:
  engine.gaw_timing_reset();pending=[];checked=[0];digest=bytearray()
  def prepare(i,f):
   style,skip,comp,delay=cases[i]
   a=bytes((0 if style in [0,1] else 63 if style==2 else n*7 if style==3 else n*13 if style==4 else 255)&255 for n in range(32));b=bytes((0 if style==0 else 63 if style==1 else 0 if style==2 else 255-n*3 if style==3 else n*13 if style==4 else n)&255 for n in range(32))
   pending[:]=[(f,0x34,bytes.fromhex('00dd')),(f,0x1ca0,a),(f,0x1cc0,b),(f,0x33,bytes([skip])),(f,0x1e03,bytes([comp])),(f,0x30,bytes([255])),(f,0x80,bytes([i&255,0])+delay.to_bytes(2,'little')),(f,0x1df0,bytes([1]))]
  def observe(f,r):
   count=engine.gaw_foreground_phase_samples();raw=c.string_at(engine.gaw_foreground_phase_events(),count*800);meta=c.string_at(engine.gaw_foreground_m1_events(),count*16);positions=[n for n in range(count) if struct.unpack_from('<Q',raw,n*800)[0] in [0xace,0x1706]]
   if not positions or struct.unpack_from('<Q',raw,positions[-1]*800)[0]!=0x1706:return
   assert len(positions)==2;ai,bi=positions;i=checked[0];phase=struct.unpack_from('<12I',raw,ai*800+16);ta=struct.unpack_from('<Q',raw,ai*800+8)[0];tb=struct.unpack_from('<Q',raw,bi*800+8)[0];fa,refresh,_=struct.unpack_from('<Q2I',meta,ai*16);fb,end_r,_=struct.unpack_from('<Q2I',meta,bi*16)
   entries=c.string_at(engine.gaw_loader_entry_events(),engine.gaw_loader_entry_samples()*8200);before=next(entries[n+8:n+8200] for n in range(0,len(entries),8200) if struct.unpack_from('<Q',entries,n)[0]==ta)
   body=(c.c_uint8*8192).from_buffer_copy(before);out=(c.c_uint32*9)();after=(c.c_uint8*8192)();assert lib.fade_case((c.c_uint32*12)(*phase),refresh,source_rom,body,out,after),(region,i,cases[i],'rejected',list(out),phase, list(before[0x34:0x36]),list(before[0x1d00:0x1d08]))
   assert out[0]==tb-ta and out[2]+out[4]==fb-fa and out[7]==end_r and out[8]==1,(region,i,cases[i],'time/M1/R',out[:],tb-ta,fb-fa,end_r)
   expected=raw[bi*800+64:bi*800+400];audio=raw[bi*800+400:bi*800+800];compact=bytes(after[:80])+bytes(after[0x1d00:0x1e00]);assert all(compact[j]==expected[j] for j in range(336) if j not in [0x1b,0x20,0x21,0x22,0x23]),(region,i,'RAM');assert bytes(after[0x1e00:0x1f90])==audio,(region,i,'audio')
   assert bytes(after[0x1ca0:0x1ce0])==bytes(r[0x1ca0:0x1ce0]) and all((after[0x1ca0+j]&63)==(before[0x1cc0+j]&63) for j in range(32)),(region,i,'palette')
   digest.extend(bytes(out));digest.extend(bytes(after[0x1ca0:0x1ce0]));vectors.append(dict(region=region,phase=list(phase),refresh=refresh,body=list(before),expected=list(out),after=list(after)));checked[0]+=1;engine.gaw_timing_reset()
   if checked[0]<len(cases):prepare(checked[0],f+1)
  prepare(0,10);run(cart,len(cases)*35+20,folder/region,set(),[],core=core,skip_intro=False,ram_writes=pending,ram_observer=observe,stop_when=lambda:checked[0]==len(cases),core_options={'genesis_plus_gx_region_detect':region});assert checked[0]==len(cases),(region,checked[0]);results.append(dict(region=region,cases=checked[0],output_sha256=sha(digest)));print(results[-1],flush=True)
 (folder/'cases.json').write_bytes((json.dumps(vectors,separators=(',',':'))+'\n').encode())
 report=dict(passed=True,cases=sum(r['cases'] for r in results),rows=results,source_sha256=sha(original),fixture_sha256=sha(rom),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},headers_sha256={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_room_reveal.h','source_room_ready.h','source_wait.h','source_wait_restore.h','source_irq_context.h']},production_clock_wired=False,limits=['Original0ACE..0B11 and waits unchanged; controlled caller returns directly to1706 rather than1FB6, with the same prefetched return boundary. Source IRQ/audio live. Six palette styles, equal/ascending/descending/mixed/high bits, palette skip, compensation and entry delay in both regions.','64 palette bytes,331 compact RAM bytes,400 audio bytes and total time/M1/R checked. IRQ video publication, physical MD cadence and complete chain through fade remain separate.'])
 (ROOT/'analysis/native_room_fade_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
if __name__=='__main__':main()
