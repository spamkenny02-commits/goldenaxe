"""Native instruction clock vs independently verified Python phase/R scheduler."""
import ctypes as c,hashlib,itertools,json,os,subprocess
from actor_reference import ROOT
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from audio_reader_refresh import reader_refresh
from audio_irq_wrapper_refresh import audio_irq_wrapper_refresh
from source_rng_refresh import advance_refresh

PLANS=[[(4,1,0),(4,1,0)],[(11,1,3),(4,1,2),(4,1,0),(16,2,0)],[(4,1,1),(21,2,0),(4,1,2),(4,1,0),(20,2,0)],[(4,1,2),(4,1,1),(4,1,0),(4,1,2),(4,1,0),(11,1,3)],[(16,1,0),(16,2,0),(8,2,0),(8,1,0),(15,2,0),(19,2,0)]]
PLANS.extend([[(21,2,0)]*8000,[(4,1,1)]+[(21,2,0)]*8000+[(11,1,3),(4,1,2),(4,1,0)]+[(21,2,0)]*2000])
WRAPPER='''#include "source_clock.h"
typedef struct { u32 tstates,fetches,elapsed_sum,raster_sum,refresh_sum; } TestInterrupt;
static u8 test_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work)
{ TestInterrupt *p=context;p->elapsed_sum+=entry->entry_elapsed;p->raster_sum+=entry->entry_raster;p->refresh_sum+=entry->entry_refresh;work->tstates=p->tstates;work->fetches=p->fetches;return 1; }
u8 clock_case(const u32 *input,const u16 *plan,u16 length,u32 *out)
{
 SourceClock clock;TestInterrupt context={0};u16 i;
 context.tstates=input[6];context.fetches=input[7];
 if(!source_clock_init(&clock,input[0],input[1],input[2],input[3],input[4],input[5])) return 0;
 for(i=0;i<length;i++) if(!source_clock_execute(&clock,plan[i*3],plan[i*3+1],plan[i*3+2],test_interrupt,&context)) return 0;
 if(!source_clock_checkpoint(&clock,test_interrupt,&context)) return 0;
 out[0]=clock.raster;out[1]=clock.until_vint;out[2]=clock.elapsed;
 out[3]=clock.foreground_tstates;out[4]=clock.foreground_m1;out[5]=clock.irq_tstates;out[6]=clock.irq_m1;
 out[7]=clock.refresh;out[8]=clock.iff;out[9]=clock.blocked;out[10]=clock.pending;out[11]=clock.first;
 out[12]=clock.status_suppressions;out[13]=clock.vector_coalescences;out[14]=clock.irq_count;
 out[15]=context.elapsed_sum;out[16]=context.raster_sum;out[17]=context.refresh_sum;return 1;
}
'''

def cases():
 rom=(ROOT/'input/original.sms').read_bytes();sound=bytearray(400);sound[10]=1;ram=bytes(336);driver=reader_refresh(rom,sound);wrapper=audio_irq_wrapper_refresh(False)
 workT=wrapper['interrupt_accept_and_vector']+wrapper['to_return_excluding_reader']+driver['tstates']+wrapper['return_instruction'];workM=wrapper['whole_IRQ_excluding_reader_M1']+driver['m1_fetches'];result=[]
 for lines in [262,313]:
  period=lines*3420;edge=193*3420
  phases=sorted({0,period-1,*[edge+n for n in [-526,-525,-181,-180,-166,-165,-61,-60,-16,-15,-1,0,1,15,60,165,525]]})
  configurations=list(itertools.product(phases,itertools.product([0,1],repeat=3),[0,1,127,128,255],range(5)))
  configurations.extend((raster,(iff,0,pending),refresh,plan) for raster,iff,pending,refresh,plan in itertools.product([0,edge-1],[0,1],[0,1],[0,255],[5,6]))
  for raster,(iff,blocked,pending),refresh,plan_index in configurations:
   class Model(GraphicsPrefixRefreshPhase):
    entry_refresh=refresh
    def __init__(self,*args):super().__init__(*args);self.sums=[0,0,0]
    def boundary(self):
     oldR=self.refresh;old=len(self.events);super().boundary()
     for i,event in enumerate(self.events[old:]):
      offset=event['entry_offset_master'];values=[offset,(raster+offset)%period,advance_refresh(oldR,7+i*workM)]
      self.sums=[(a+b)&0xffffffff for a,b in zip(self.sums,values)]
   phase=[raster%3420,raster//3420,0,lines,0xda if lines==262 else 0xf2,0,0xa0,0x20,iff,blocked,pending,0]
   cpu=Model(rom,phase,ram,sound)
   for ticks,fetches,effect in PLANS[plan_index]:cpu.execute(ticks,{1:'DI',2:'EI',3:'status'}.get(effect,'M1_2' if fetches==2 else 'M1_1'))
   cpu.checkpoint()
   expected=[cpu.time%period,cpu.deadline-cpu.time,cpu.time-cpu.started,cpu.foreground_tstates,cpu.foreground_M1,cpu.IRQ_tstates,cpu.IRQ_M1,cpu.refresh,int(cpu.iff),int(cpu.blocked),int(cpu.pending),int(cpu.first),cpu.status_suppressions,cpu.vector_coalescences,len(cpu.events),*cpu.sums]
   result.append(dict(input=[lines,raster,refresh,iff,blocked,pending,workT,workM],plan=plan_index,expected=expected))
 for invalid in [[261,0,0,0,0,0,workT,workM],[262,262*3420,0,0,0,0,workT,workM],[262,0,0,2,0,0,workT,workM],[262,0,0,1,0,1,0,workM],[262,0,0,1,0,1,workT,0]]:result.append(dict(input=invalid,plan=0,expected=[0]*18,accepted=0))
 return result

def main():
 folder=ROOT/'validation/native-source-clock';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve();(folder/'wrapper.c').write_text(WRAPPER);env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 command=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c'),str(ROOT/'megadrive/src/source_clock.c'),str(ROOT/'megadrive/src/source_rng.c'),'-o',str(folder/'source_clock.dll')]
 compiled=subprocess.run(command,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(compiled.stdout+compiled.stderr);assert compiled.returncode==0,compiled.stderr
 dll=c.CDLL(str(folder/'source_clock.dll'));dll.clock_case.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint16),c.c_uint16,c.POINTER(c.c_uint32)];dll.clock_case.restype=c.c_uint8;data=cases();plans=[(c.c_uint16*(len(p)*3))(*(v for row in p for v in row)) for p in PLANS]
 for n,row in enumerate(data):
  output=(c.c_uint32*18)();plan=row['plan'];assert dll.clock_case((c.c_uint32*8)(*row['input']),plans[plan],len(PLANS[plan]),output)==row.get('accepted',1)
  if row.get('accepted',1):assert list(output)==row['expected'],(n,row,list(output))
 (folder/'cases.json').write_text(json.dumps(dict(plans=PLANS,cases=data),separators=(',',':'))+'\n')
 report=dict(cases=len(data),rejected_cases=sum(not r.get('accepted',1) for r in data),source_sha256=hashlib.sha256((ROOT/'megadrive/src/source_clock.c').read_bytes()).hexdigest(),suppression_cases=sum(bool(r['expected'][12]) for r in data),coalescence_cases=sum(bool(r['expected'][13]) for r in data),IRQ_cases=sum(bool(r['expected'][14]) for r in data),production_ROM_changed=False,production_clock_integrated=False,limits=['Constant independently composed paused-reader audio IRQ callback; dynamic audio/fullIRQ cost production remains to port. Mode4/192,VINT-only andlocal GPG acknowledge convention. Native host code checked against Python scheduler; real hardware/full game not proved.'])
 (ROOT/'analysis/native_source_clock_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(data),'native clock cases exact including M1/R,DI/EI,status,VINT,IRQ entry R/phase andbudgets',flush=True)
if __name__=='__main__':main()
