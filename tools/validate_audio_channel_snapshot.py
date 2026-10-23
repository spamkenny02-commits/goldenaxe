"""Check smaller audio channel snapshots against v0264, including rejection."""
import ctypes as c,hashlib,json,os,random,struct,subprocess
from pathlib import Path
from validate_native_audio_reader import MODULES,Output
from validate_native_audio_prefix import Work
ROOT=Path(__file__).resolve().parents[1]
BASELINE='b7696b3'
class Status(c.Structure):_fields_=[('count',c.c_uint16),('error',c.c_uint16),('track',c.c_uint8)]
SINK=c.CFUNCTYPE(None,c.c_void_p,c.POINTER(c.c_uint8),c.c_uint16)

def main():
 folder=ROOT/'validation/audio-channel-snapshot';folder.mkdir(exist_ok=True);sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];libs=[]
 baseline_files=set(subprocess.check_output(['git','ls-tree','--name-only',BASELINE+':megadrive/src'],cwd=ROOT).decode().splitlines())
 for tag in ['baseline','current']:
  src=folder/tag;src.mkdir(exist_ok=True)
  for p in list((ROOT/'megadrive/src').glob('*.h'))+[(ROOT/'megadrive/src'/f'{n}.c') for n in MODULES]:
   if tag=='baseline' and p.name not in baseline_files:continue
   raw=subprocess.check_output(['git','show',BASELINE+':megadrive/src/'+p.name],cwd=ROOT) if tag=='baseline' else p.read_bytes();(src/p.name).write_bytes(raw)
  subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I',str(sdk/'inc'),'-I',str(src),*[str(src/f'{n}.c') for n in MODULES if (src/f'{n}.c').exists() and (tag!='baseline' or n+'.c' in baseline_files)],'-o',str(src/'reader.dll')],env=env,check=True)
  dll=c.CDLL(str(src/'reader.dll'));args=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work)]
  dll.reader=getattr(dll,'source_audio_reader');dll.stream=getattr(dll,'source_audio_reader_stream')
  dll.reader.argtypes=args+[c.POINTER(Output)];dll.reader.restype=c.c_uint8
  dll.stream.argtypes=args+[c.POINTER(Status),SINK,c.c_void_p];dll.stream.restype=c.c_uint8;libs.append(dll)
 bank=(c.c_uint8*16384).from_buffer_copy((ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]);digest=hashlib.sha256();valid=0;rejected=0;streamed=0
 def call(dll,low,before,de_in,stream):
  state=(c.c_uint8*400).from_buffer_copy(before);de=c.c_uint16(de_in);work=Work();writes=[]
  if stream:
   status=Status()
   @SINK
   def sink(context,p,n):writes.extend(p[i] for i in range(n))
   ok=dll.stream(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(status),sink,None);count,error,track=status.count,status.error,status.track
  else:
   out=Output();ok=dll.reader(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(out));count,error,track=out.count,out.error,out.track;writes=list(out.writes[:count])
  return ok,bytes(state),de.value,work.tstates,work.fetches,count,error,track,bytes(writes)
 def check(low,before,de_in,label):
  nonlocal valid,rejected,streamed
  a,b=[call(dll,low,before,de_in,False) for dll in libs];assert a==b,(label,'transactional state/work/DE/PSG/error')
  x,y=[call(dll,low,before,de_in,True) for dll in libs];assert x==y,(label,'stream failed-channel rollback/work/DE/PSG/status')
  if a[0]:
   valid+=1;x,y=[call(dll,low,before,de_in,True) for dll in libs];assert x==y and y==a,(label,'streamed state/work/DE/PSG');streamed+=1
  else:
   rejected+=1;assert a[1]==before and a[2]==de_in,(label,'outer rollback')
  digest.update(a[1]);digest.update(struct.pack('<6I',a[2],a[3],a[4],a[5],a[6],a[7]));digest.update(a[8])
 suites=json.loads((ROOT/'validation/native-audio-reader/cases.json').read_text())+json.loads((ROOT/'validation/native-audio-reader/extension-cases.json').read_text())
 for number,suite in enumerate(suites):
  image=(ROOT/suite['fixture']).read_bytes();assert hashlib.sha256(image).hexdigest()==suite['fixture_sha256'];low=(c.c_uint8*32768).from_buffer_copy(image[:32768])
  for n,row in enumerate(suite['cases']):check(low,bytes(row['before']),row['de_in'],(number,n))
 low=(c.c_uint8*32768).from_buffer_copy((ROOT/'input/original.sms').read_bytes()[:32768]);rng=random.Random(0x800084c7);seed=bytes(suites[-1]['cases'][0]['before'])
 for n in range(6000):
  state=bytearray(seed)
  for k in range(1+n%19):state[rng.randrange(400)]=rng.randrange(256)
  state[10]=0;check(low,bytes(state),rng.randrange(65536),('mutated',n))
 # Exercise the public channel APIs at every accepted offset, including
 # overlapping prefix records and boundaries, for both snapshot branches.
 from validate_native_audio_sequence import Output as SequenceOutput
 direct=0;direct_rejected=0
 for name in ['source_audio_tone','source_audio_noise']:
  for dll in libs:
   fn=getattr(dll,name);fn.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(SequenceOutput)];fn.restype=c.c_uint8
  for offset in list(range(353))+[353,65535]:
   for tick in [0,1,2,255]:
    before=bytearray(rng.randbytes(400))
    if offset<=352:before[offset+10]=tick
    de_in=rng.randrange(65536);outcomes=[]
    for dll in libs:
     state=(c.c_uint8*400).from_buffer_copy(before);de=c.c_uint16(de_in);work=Work();out=SequenceOutput()
     ok=getattr(dll,name)(state,offset,low,32768,bank,c.byref(de),c.byref(work),c.byref(out))
     outcomes.append((ok,bytes(state),de.value,work.tstates,work.fetches,out.de,out.count,out.error,out.unwind,bytes(out.writes[:out.count])))
    assert outcomes[0]==outcomes[1],(name,offset,tick,'direct API')
    direct+=1;direct_rejected+=not outcomes[0][0]
 assert valid and rejected and streamed and direct_rejected
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),baseline_commit=BASELINE,source_vector_cases=sum(len(s['cases']) for s in suites),mutated_cases=6000,direct_channel_cases=direct,direct_channel_rejected=direct_rejected,accepted=valid,rejected=rejected,streamed_successes=streamed,all_400_bytes_work_DE_PSG_status_exact=True,transactional_rejection_restores_state_and_DE=True,result_digest=digest.hexdigest(),module_sha256={n:hashlib.sha256((ROOT/'megadrive/src'/f'{n}.c').read_bytes()).hexdigest() for n in MODULES},limits=['Host differential test. Valid states additionally have retained source and compiled68000 checks. All streamed rejections additionally match baseline state, DE, cost, status and previously emitted PSG bytes. The public transactional reader retains full rollback. No analogue waveform or full-game claim.'])
 report['production_channel_snapshot_optimized']=True
 report['production_fast_audio_wired']='source_audio_reader_stream_fast(' in (ROOT/'megadrive/src/sound.inc').read_text()
 (ROOT/'analysis/audio_channel_snapshot_equivalence_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='module_sha256'},indent=2))

if __name__=='__main__':main()
