"""Timed04E1 and direct R reads against ROM-derived plans and Python clock oracle."""
import ctypes as c,json,os,subprocess
from pathlib import Path
from run_core import ROOT
from archive_lossless_evidence import sha
from source_rng_reference import source_rng
from source_rng_refresh import advance_refresh
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from audio_reader_refresh import reader_refresh
from audio_irq_wrapper_refresh import audio_irq_wrapper_refresh
class Clock(c.Structure):
 _fields_=[(n,c.c_uint32) for n in ['period','raster','until_vint','elapsed','foreground_tstates','foreground_m1','irq_tstates','irq_m1','irq_count','status_suppressions','vector_coalescences']]+[(n,c.c_uint8) for n in ['refresh','iff','blocked','pending','first']]
class Out(c.Structure):_fields_=[('seed',c.c_uint16),('value',c.c_uint8),('sampled_refresh',c.c_uint8),('zero_replaced',c.c_uint8)]
class Entry(c.Structure):_fields_=[('raster',c.c_uint32),('elapsed',c.c_uint32),('refresh',c.c_uint8)]
class Work(c.Structure):_fields_=[('tstates',c.c_uint32),('fetches',c.c_uint32)]
IRQ=c.CFUNCTYPE(c.c_uint8,c.c_void_p,c.POINTER(Entry),c.POINTER(Work))
# Individual original opcodes at04E1..04FD; conditional zero fallback explicit.
PLAN=[(0x4e1,16,1),(0x4e4,4,1),(0x4e5,4,1),(0x4e6,4,1),(0x4e7,4,1),(0x4e8,4,1),(0x4e9,4,1),(0x4ea,4,1),(0x4eb,4,1),(0x4ec,4,1),(0x4ed,4,1),(0x4ee,4,1),(0x4ef,4,1),(0x4f0,15,2)]
def compile():
 folder=ROOT/'validation/rng-timed-host';folder.mkdir(exist_ok=True);(folder/'types.h').write_bytes(b'#include <stdint.h>\ntypedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;\n');env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];path=folder/'rng.dll'
 subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(folder),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/n) for n in ['source_clock.c','source_rng.c','source_rng_timed.c']],'-o',str(path)],env=env,check=True);lib=c.CDLL(str(path));lib.source_clock_init.argtypes=[c.POINTER(Clock),c.c_uint16,c.c_uint32,c.c_uint8,c.c_uint8,c.c_uint8,c.c_uint8];lib.source_clock_init.restype=c.c_uint8;lib.source_rng_timed.argtypes=[c.POINTER(Clock),c.POINTER(c.c_uint8),c.POINTER(Out),IRQ,c.c_void_p];lib.source_rng_timed.restype=c.c_uint8;lib.source_rng_read_refresh.argtypes=[c.POINTER(Clock),c.POINTER(c.c_uint8),IRQ,c.c_void_p];lib.source_rng_read_refresh.restype=c.c_uint8;return lib

def main():
 lib=compile();rom=(ROOT/'input/original.sms').read_bytes();sound=bytearray(400);sound[10]=1;driver=reader_refresh(rom,sound);wrapper=audio_irq_wrapper_refresh(False);workT=wrapper['interrupt_accept_and_vector']+wrapper['to_return_excluding_reader']+driver['tstates']+wrapper['return_instruction'];workM=wrapper['whole_IRQ_excluding_reader_M1']+driver['m1_fetches'];calls=[0]
 @IRQ
 def irq(ctx,entry,work):calls[0]+=1;work[0].tstates=workT;work[0].fetches=workM;return 1
 exhaustive=0
 for seed in range(65536):
  for refresh in [0,127,255]:
   for first in [0,1]:
    clock=Clock();initial=refresh if first else (refresh&128)|((refresh-1)&127);assert lib.source_clock_init(c.byref(clock),262,0,initial,1,0,0);clock.first=first;state=(c.c_uint8*2)(seed&255,seed>>8);out=Out();assert lib.source_rng_timed(c.byref(clock),state,c.byref(out),irq,None)
    model=source_rng(seed,advance_refresh(refresh,17+(seed==0)));assert (out.seed,out.value,out.sampled_refresh,out.zero_replaced,bytes(state))==(model['seed'],model['value'],advance_refresh(refresh,17+(seed==0)),seed==0,model['seed'].to_bytes(2,'little'))
    assert clock.foreground_tstates==model['foreground_tstates'] and clock.foreground_m1==21+(seed==0) and clock.refresh==advance_refresh(out.sampled_refresh,3) and not clock.irq_count;exhaustive+=1
 cases=[];interrupts=0
 for lines in [262,313]:
  for delta in range(-2100,31,15):
   raster=193*3420+delta
   for seed in [0,0x8000,0x733c,0xffff]:
    for refresh in [0,127,128,255]:
     class Model(GraphicsPrefixRefreshPhase):entry_refresh=refresh
     phase=[raster%3420,raster//3420,0,lines,0xda if lines==262 else 0xf2,0,0xa0,0x20,1,0,0,0];model=Model(rom,phase,bytes(336),sound)
     for pc,t,m in PLAN:model.execute(t,'M1_2' if m==2 else 'M1_1')
     zero=seed==0;model.execute(7 if zero else 12,'M1_1')
     if zero:model.execute(10,'M1_1')
     model.execute(9,'M1_2');sample=model.refresh;model.execute(4,'M1_1');model.execute(16,'M1_1');model.execute(10,'M1_1')
     expected=source_rng(seed,sample);clock=Clock();assert lib.source_clock_init(c.byref(clock),lines,raster,refresh,1,0,0);state=(c.c_uint8*2)(seed&255,seed>>8);out=Out();assert lib.source_rng_timed(c.byref(clock),state,c.byref(out),irq,None)
     actual=[clock.raster,clock.until_vint,clock.elapsed,clock.foreground_tstates,clock.foreground_m1,clock.irq_tstates,clock.irq_m1,clock.refresh,clock.iff,clock.blocked,clock.pending,clock.first,clock.irq_count]
     deadline=model.deadline;pending=model.pending
     while model.time>=deadline:pending=True;deadline+=model.period
     want=[model.time%model.period,deadline-model.time,model.time-model.started,model.foreground_tstates,model.foreground_M1,model.IRQ_tstates,model.IRQ_M1,model.refresh,int(model.iff),int(model.blocked),int(pending),int(model.first),len(model.events)]
     assert actual==want and (out.seed,out.value,out.sampled_refresh)==(expected['seed'],expected['value'],sample),(lines,delta,seed,refresh,actual,want)
     interrupts+=bool(clock.irq_count);cases.append(dict(input=[lines,raster,refresh,seed],output=[out.seed,out.value,out.sampled_refresh,*actual]))
 direct=0
 for refresh in range(256):
  clock=Clock();assert lib.source_clock_init(c.byref(clock),262,0,refresh,1,0,0);out=c.c_uint8();assert lib.source_rng_read_refresh(c.byref(clock),c.byref(out),irq,None);assert out.value==advance_refresh(refresh,1) and clock.foreground_tstates==9 and clock.foreground_m1==2;direct+=1
 # IRQ before the initial load observes the changed RAM seed; IRQ before
 # RET must retain a mutation made after the original seed store.
 mutations=0
 for when in ['entry','return']:
  state=(c.c_uint8*2)(1,0);clock=Clock();out=Out();raster=0 if when=='entry' else 193*3420-120*15
  assert lib.source_clock_init(c.byref(clock),262,raster,0,1,0,when=='entry')
  if when=='entry':clock.first=0
  @IRQ
  def mutate(ctx,entry,work):state[0]=0xcd;state[1]=0xab;work[0].tstates=workT;work[0].fetches=workM;return 1
  assert lib.source_rng_timed(c.byref(clock),state,c.byref(out),mutate,None)
  expected_seed=source_rng(0xabcd if when=='entry' else 1,0)['seed']
  assert out.seed==expected_seed and bytes(state)==(expected_seed if when=='entry' else 0xabcd).to_bytes(2,'little');mutations+=1
 failures=0
 for when in ['entry','return']:
  state=(c.c_uint8*2)(1,0);clock=Clock();out=Out();raster=0 if when=='entry' else 193*3420-120*15
  assert lib.source_clock_init(c.byref(clock),262,raster,0,1,0,when=='entry')
  if when=='entry':clock.first=0
  @IRQ
  def fail(ctx,entry,work):return 0
  assert not lib.source_rng_timed(c.byref(clock),state,c.byref(out),fail,None)
  assert bytes(state)==(1 if when=='entry' else source_rng(1,0)['seed']).to_bytes(2,'little');failures+=1
 assert interrupts
 folder=ROOT/'validation/rng-timed-host';(folder/'boundary-cases.json').write_bytes(json.dumps(cases,separators=(',',':')).encode());r=dict(passed=True,exhaustive_seed_refresh_prefetch_cases=exhaustive,boundary_cases=len(cases),interrupted_cases=interrupts,direct_refresh_cases=direct,irq_seed_mutation_cases=mutations,callback_failure_cases=failures,irq_tstates=workT,irq_fetches=workM,module_sha256={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_clock.c','source_rng.c','source_rng_timed.c','source_rng_timed.h']},playable_rom_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),production_rng_integrated=False,limits=['ROM-derived04E1 instruction plan plus separately source-verified Python clock oracle and paused audio IRQ model. Boundary inputs are controlled, not natural gameplay entry clocks.','No whole-game clock propagation or native gameplay RNG replacement. Source direct-R reads and seeded calls are distinct APIs. Native68000 execution is checked separately.']);(ROOT/'analysis/rng_timed_host_report.json').write_bytes((json.dumps(r,indent=2)+'\n').encode());print(r)
if __name__=='__main__':main()
