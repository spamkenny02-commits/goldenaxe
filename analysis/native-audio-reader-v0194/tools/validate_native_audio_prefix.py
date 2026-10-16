"""Native pause/arbitration/tempo/stop/fade state and original work comparisons."""
import ctypes as c,hashlib,itertools,json,os,subprocess
from actor_reference import ROOT
from audio_prefix_refresh import arbitration_refresh,tempo_refresh,stop_refresh,fade_refresh
from audio_reader_refresh import reader_refresh

FIELDS=[1,2,5,6,7,8,10,11,12,13,17,24,72,74,120,122,168,170,218]

def make_cases():
 source=(ROOT/'input/original.sms').read_bytes();rows=[]
 def add(kind,updates,salt):
  initial=bytearray((i*37+salt)&255 for i in range(400))
  for offset,value in updates.items():initial[offset]=value
  if kind==0:expected=tempo_refresh(initial)
  elif kind==1:expected=stop_refresh(initial)
  elif kind==2:expected=fade_refresh(initial)
  elif kind==3:expected=arbitration_refresh(source,initial)
  else:expected=reader_refresh(source,initial) if initial[10] else dict(state=bytes(initial),tstates=33,m1_fetches=4)
  state=expected['state'];cleared=all(state[i]==(128 if i==5 else 0) for i in range(5,400));reconstructed=bytearray(initial)
  if cleared:reconstructed[5:]=bytes(395);reconstructed[5]=128
  for offset in FIELDS:reconstructed[offset]=state[offset]
  assert reconstructed==state,'Sparse fixture representation lost a mutation'
  rows.append(dict(kind=kind,salt=salt,cleared=int(cleared),gate=int(bool(initial[10])) if kind==4 else 0,input=[initial[i] for i in FIELDS],expected=[state[i] for i in FIELDS],tstates=expected['tstates'],fetches=expected['m1_fetches']))
 for counter,reload,phase in itertools.product(range(256),[0,1,128,255],[0,1,127,255]):add(0,{1:counter,2:reload,**{0x4a+n*0x30:(phase+n)&255 for n in range(4)}},(counter*19+phase)&255)
 for salt in range(64):add(1,{},salt)
 for steps,counter,reload,volume in itertools.product(range(256),[0,1,2,255],[0,1,128,255],[0,10,11,12,127,255]):add(2,{11:steps,12:counter,13:reload,72:volume,120:(volume+1)&255,168:(volume+2)&255,24:(volume+3)&255},(steps*19+counter)&255)
 for requests,priority,command in itertools.product(itertools.product([0,128,129,144,172,176,180,255,127],repeat=3),[0,1,127,128,255],[0,128,255]):add(3,{6:requests[0],7:requests[1],8:requests[2],17:priority,5:command},(priority+command)&255)
 for pause,command,salt in itertools.product(range(256),[0,128,255],[0,1,127,255]):add(4,{10:pause,5:command},salt)
 return rows

class Work(c.Structure):_fields_=[('tstates',c.c_uint32),('fetches',c.c_uint32)]

def main():
 folder=ROOT/'validation/native-audio-prefix';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(ROOT/'megadrive/src/source_audio_prefix.c'),'-o',str(folder/'source_audio_prefix.dll')]
 result=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
 dll=c.CDLL(str(folder/'source_audio_prefix.dll'));functions=[dll.source_audio_tempo,dll.source_audio_stop,dll.source_audio_fade,dll.source_audio_arbitrate,dll.source_audio_gate];bank=(c.c_uint8*16384).from_buffer_copy((ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]);rows=make_cases();counts=[0]*5
 for kind,function in enumerate(functions):function.argtypes=[c.POINTER(c.c_uint8)]+([c.POINTER(c.c_uint8)] if kind==3 else [])+[c.POINTER(Work)];function.restype=c.c_uint8 if kind==4 else None
 for n,row in enumerate(rows):
  initial=bytearray((i*37+row['salt'])&255 for i in range(400))
  for offset,value in zip(FIELDS,row['input']):initial[offset]=value
  expected=bytearray(initial)
  if row['cleared']:expected[5:]=bytes(395);expected[5]=128
  for offset,value in zip(FIELDS,row['expected']):expected[offset]=value
  state=(c.c_uint8*400).from_buffer_copy(initial);work=Work();kind=row['kind'];gate=functions[kind](state,*([bank] if kind==3 else []),c.byref(work))
  assert bytes(state)==expected and (work.tstates,work.fetches)==(row['tstates'],row['fetches']),(n,kind,work.tstates,work.fetches)
  if kind==4:assert gate==row['gate']
  counts[kind]+=1
 (folder/'cases.json').write_text(json.dumps(dict(fields=FIELDS,cases=rows),separators=(',',':'))+'\n')
 report=dict(cases=len(rows),kinds=dict(zip(['tempo','stop','fade','arbitration','gate'],counts)),source_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_prefix.c').read_bytes()).hexdigest(),compared_RAM_bytes=400,production_ROM_changed=False,production_audio_replaced=False,limits=['Native prefix state/work only; no PSG writes. Dispatch,priority effects,channels,fullIRQ andgame wiring remain. Cases vary independent dimensions,not fullCartesian state space.'])
 (ROOT/'analysis/native_audio_prefix_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(rows),'native audio prefix cases exact:',counts,flush=True)
if __name__=='__main__':main()
