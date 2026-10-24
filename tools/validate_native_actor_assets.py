"""Original1853 graphics for every type in512 room lists, plus reuse/partial masks."""
import ctypes as c,json,os,struct,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_history_timed import fixture
from validate_native_actor_graphics import MODULES,WRAPPER

def main():
 folder=ROOT/'validation/native-actor-assets';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'assets.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 original=(ROOT/'input/original.sms').read_bytes();rom=fixture(original,True);rom[0x16d7:0x16da]=bytes.fromhex('c35318');assert rom[0x1853:0x18e2]==original[0x1853:0x18e2]
 cart=folder/'fixture.sms';cart.write_bytes(rom);rows=[original[0x3234e+n*8:0x32356+n*8] for n in range(512)];types=sorted({t for row in rows for t in row if t>=32});cases=[]
 for t in types:
  room=next(n for n,row in enumerate(rows) if t in row);slot=rows[room].index(t);cases.append((room,128>>slot,'single'))
  duplicate=next((n for n,row in enumerate(rows) if row.count(t)>1),None)
  if duplicate is not None:
   slots=[n for n,v in enumerate(rows[duplicate]) if v==t];cases.append((duplicate,(128>>slots[0])|(128>>slots[-1]),'reuse'))
 for room in [0x1a,0x3c,0x36,0x87,0x6d,0x96]:
  for mask in [0x55,0xaa]:cases.append((room,mask,'mixed'))
 lib=c.CDLL(str(folder/'assets.dll'));u8=c.POINTER(c.c_uint8);u32=c.POINTER(c.c_uint32);lib.actor_graphics_case.argtypes=[u32,c.c_uint8,*([u8]*7),u32,u32,u32,u8];lib.actor_graphics_case.restype=c.c_uint8;arr=lambda b:(c.c_uint8*len(b)).from_buffer_copy(b);source_rom=arr(original)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_actorgraphicsrefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_foreground_phase_samples.restype=c.c_uint;engine.gaw_actor_graphics_samples.restype=c.c_uint
 for n in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_actor_graphics_events']:getattr(engine,n).restype=u8
 pending=[];current={};checked=[0];results=[];digest=bytearray()
 def prepare(i,f):
  room,mask,kind=cases[i];actors=bytearray(768)
  for n,t in enumerate(rows[room]):
   if mask&(128>>n):
    actors[n*48]=t
    if t>=32:stats=original[0x320ea+(t-32)*4:0x320ee+(t-32)*4];actors[n*48+24:n*48+27]=stats[:3];actors[n*48+3]=stats[3]
  pending[:]=[(f,0x600,bytes(actors)),(f,0x1100,bytes([0xa7])*1024),(f,0xb9,room.to_bytes(2,'little')),(f,0x80,bytes([i&255,0,0,0])),(f,0x1d00,b'\1')];current.update(index=i,actors=bytes(actors),prepared=True)
 def observe(f,r):
  if f<10 or not current.get('prepared') or r[0x1d00]:return
  i=current['index'];room,mask,kind=cases[i];count=engine.gaw_foreground_phase_samples();raw=c.string_at(engine.gaw_foreground_phase_events(),count*800);m1=c.string_at(engine.gaw_foreground_m1_events(),count*16);records=[]
  for n in range(count):
   pc,t=struct.unpack_from('<2Q',raw,n*800);fetch,refresh,_=struct.unpack_from('<Q2I',m1,n*16);records.append(dict(pc=pc,time=t,phase=struct.unpack_from('<12I',raw,n*800+16),ram=raw[n*800+64:n*800+400],audio=raw[n*800+400:n*800+800],m1=fetch,refresh=refresh))
  entry=next(e for e in records if e['pc']==0x1853);observed=[e for e in records if e['pc'] in [0x18ac,0x18af,0x18b7,0x18e1] and e['time']>entry['time']];end_index=next(n for n,e in enumerate(observed) if e['pc']==0x18e1);observed=observed[:end_index+1]
  ram=arr(entry['ram']);audio=arr(entry['audio']);actors=arr(current['actors']);patterns=arr(bytes([0xa7])*16384);terrain=arr(bytes([0xa7])*1024);allocated=(c.c_uint8*1)();out=(c.c_uint32*15)();events=(c.c_uint32*384)();points=(c.c_uint32*150)();states=(c.c_uint8*7360)()
  assert lib.actor_graphics_case((c.c_uint32*12)(*entry['phase']),entry['refresh'],ram,audio,source_rom,actors,patterns,terrain,allocated,out,events,points,states),(i,cases[i],'rejected')
  assert out[14]==len(observed)
  for n,end in enumerate(observed):
   p=list(points[n*15:(n+1)*15]);state=bytes(states[n*736:(n+1)*736]);phase=end['phase'];delta=((phase[0]-phase[2]+0x80000000)&0xffffffff)-0x80000000
   assert p[14]==end['pc'] and p[0]==(phase[1]*3420+delta)%(phase[3]*3420) and p[2]==end['time']-entry['time'],(i,cases[i],hex(end['pc']),'phase/time')
   assert p[8]==end['refresh'] and p[4]+p[6]==end['m1']-entry['m1'],(i,cases[i],hex(end['pc']),'M1/R')
   assert state[336:]==end['audio'] and all(state[j]==end['ram'][j] for j in range(336) if j not in [0x1b,0x20,0x21,0x22,0x23]),(i,cases[i],hex(end['pc']),'RAM/audio')
  gcount=engine.gaw_actor_graphics_samples();assert gcount==1;g=c.string_at(engine.gaw_actor_graphics_events(),8208);assert struct.unpack_from('<Q',g)[0]==observed[-1]['time'];tiles=struct.unpack_from('<I',g,8)[0]
  assert allocated[0]==tiles and bytes(patterns[0x2000:0x2000+tiles*32])==g[16:16+tiles*32],(i,cases[i],'patterns/allocation')
  assert bytes(actors)==r[0x600:0x900] and bytes(terrain)==r[0x1100:0x1500],(i,cases[i],'actors/scratch')
  used=sorted({a for n,a in enumerate(rows[room]) if a>=32 and mask&(128>>n)});results.append(dict(room=room,mask=mask,kind=kind,types=used,pattern_bytes=tiles*32,checkpoints=out[14],irqs=out[7]));digest.extend(bytes(actors));digest.extend(bytes(terrain));digest.extend(bytes(patterns[0x2000:0x2000+tiles*32]));checked[0]+=1;engine.gaw_timing_reset()
  if checked[0]%20==0:print('checked',checked[0],len(cases),flush=True)
  if i+1<len(cases):prepare(i+1,f+1)
  else:current['prepared']=False
 engine.gaw_timing_reset();prepare(0,10);run(cart,40000,folder/'source',set(),[],core=core,skip_intro=False,ram_writes=pending,ram_observer=observe,stop_when=lambda:checked[0]==len(cases))
 assert checked[0]==len(cases) and {t for r in results for t in r['types']}==set(types)
 report=dict(passed=True,cases=checked[0],loaded_types=len(types),types=types,reuse_cases=sum(r['kind']=='reuse' for r in results),mixed_mask_cases=12,rows=results,source_sha256=sha(original),fixture_sha256=sha(rom),core_sha256=sha(core.read_bytes()),output_sha256=sha(digest),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},limits=['Original1853..18E1 and resource ROM unchanged. Every type present in512 lists is selected once; available duplicate types and12 mixed partial masks also exercised. Controlled actor records/entryR and paused audio, live source IRQs enabled.','Entry1853 observed once; native clock/IRQ/audio thereafter. Checkpoint331RAM/400audio/phase/time/M1/R, final actors/allocation/patterns and1024 scratch bytes compare. Not all512 full lists/masks or full gameplay.','Native68000 live-music/full-chain proof is the separate24-path matrix; individual boss resources and remap10 here are host C/source comparisons.'])
 (ROOT/'analysis/native_actor_assets_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(dict(passed=True,cases=checked[0],loaded_types=len(types)),flush=True)

if __name__=='__main__':main()
