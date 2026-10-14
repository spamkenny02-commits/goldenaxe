"""Read-only original title loader profile, checked against instruction-count models."""
import contextlib,ctypes as c,hashlib,io,json,sys
from actor_reference import ROOT
from run_core import run
from actor_loading_cost import rle_cost
from title_loading_cost import map_cost,title_cost

def main():
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_title_libretro.dll';dll=c.CDLL(str(core));dll.gaw_timing_reset()
 dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
 suffix='-pal' if '--pal' in sys.argv else '';options={'genesis_plus_gx_region_detect':'pal' if suffix else 'auto'};events=[];previous=0
 def observe(frame,ram):
  nonlocal previous
  count=dll.gaw_timing_count();p=dll.gaw_timing_events()
  for n in range(previous,count):
   pc,cycles,irq,room,clock,hl,de,bc=[p[n*8+k] for k in range(8)]
   if frame>=5900 and pc in [0xb56,0x1473,0x1487,0x148d,0x1493,0x1499,0x14cf,0x14d2,0x14d5,0x14da,0xbd3,0xbfe,0x32a]:events.append(dict(frame=frame,pc=hex(pc),master_cycles=cycles,irq_master_cycles=irq,hl=hl,de=de,bc=bc))
  previous=count
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',6100,ROOT/f'validation/sms-title-loading-profile{suffix}',set(),[],core=core,ram_observer=observe,skip_intro=False,core_options=options)
 def one(pc):return next(e for e in events if e['pc']==hex(pc))
 def foreground(a,b):return ((one(b)['master_cycles']-one(a)['master_cycles'])-(one(b)['irq_master_cycles']-one(a)['irq_master_cycles']))//15
 rom=(ROOT/'input/original.sms').read_bytes();models=[]
 r=rle_cost(rom,0x1c010,0x4000);models.append(dict(routine='032A',model=r,observed_tstates=foreground(0x32a,0x148d)))
 source=r['source_end']
 for start,end,dst in [(0xbd3,0x1493,0xd600),(0x1493,0x1499,0xc900)]:
  r=map_cost(rom,source,dst);models.append(dict(routine='0BD3',model=r,observed_tstates=foreground(start,end)-(27 if start==0x1493 else 0)));source=r['source_end']
 for m in models:assert m['model']['tstates']==m['observed_tstates'],m
 full=title_cost(rom)
 checks=[(full['clear_tstates'],foreground(0xb56,0x1473)),(full['setup_tstates'],foreground(0x1473,0x1487)),(full['assets_tstates'],foreground(0x1487,0x1499)),(full['tail_tstates'],foreground(0x1499,0x14cf)),(full['foreground_tstates'],foreground(0xb56,0x14cf))]
 assert all(a==b for a,b in checks),checks
 report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),models=models,full_model=full,foreground_components_exact=True,events=events,foreground_load_tstates=foreground(0xb56,0x14cf),foreground_asset_routines_tstates=foreground(0x1487,0x1499),region='pal' if suffix else 'auto')
 (ROOT/f'analysis/title_loading_profile{suffix}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(events,indent=2))
if __name__=='__main__':main()
