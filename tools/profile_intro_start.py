"""Read-only source bootstrap / first-scene cycle and reveal profile."""
import contextlib,ctypes as c,hashlib,io,json,sys
from run_core import ROOT,run

def main():
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_intro_libretro.dll';dll=c.CDLL(str(core));dll.gaw_timing_reset();dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
 suffix='-pal' if '--pal' in sys.argv else '';options={'genesis_plus_gx_region_detect':'pal' if suffix else 'auto'};events=[];previous=0
 pcs={0xc98,0xb56,0xc9b,0xcaa,0xcbd,0xcc9,0xcd5,0xcdd,0xce0,0xcfc,0xcff,0xe4a,0xe54,0xe57,0xe5d,0xe60,0xe66,0xe72,0xe83,0xea0,0xea4,0x32a,0xbd3,0xbfe}
 def observe(frame,ram):
  nonlocal previous
  count=dll.gaw_timing_count();p=dll.gaw_timing_events()
  for n in range(previous,count):
   pc,cycles,irq,room,clock,hl,de,bc=[p[n*8+k] for k in range(8)]
   if pc in pcs:events.append(dict(frame=frame,pc=hex(pc),master_cycles=cycles,irq_master_cycles=irq,hl=hl,de=de,bc=bc))
  previous=count
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',160,ROOT/f'validation/sms-intro-start-profile{suffix}',set(),[],core=core,ram_observer=observe,skip_intro=False,core_options=options)
 report=dict(source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),region='pal' if suffix else 'auto',events=events)
 (ROOT/f'analysis/intro_start_profile{suffix}.json').write_text(json.dumps(report,indent=2)+'\n')
 print([(e['frame'],e['pc']) for e in events])
 starts=[e for e in events if e['pc']=='0xe83'];ends=[e for e in events if e['pc']=='0xea0']
 print('Reveal passes',[(a['frame'],b['frame'],((b['master_cycles']-a['master_cycles'])-(b['irq_master_cycles']-a['irq_master_cycles']))//15) for a,b in zip(starts,ends)])
if __name__=='__main__':main()
