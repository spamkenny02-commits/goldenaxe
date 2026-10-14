"""Observe original SMS decoder/remap CPU cycles without changing emulated execution."""
import contextlib,ctypes as c,hashlib,io,json,sys
from actor_reference import ROOT,load_room_actors
from actor_loading_cost import resource_cost,remap_cost
from run_core import run
from validate_actor_tick import PRESSES

def main():
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_timing_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
 suffix='-pal' if '--pal' in sys.argv else '';options={'genesis_plus_gx_region_detect':'pal' if suffix else 'auto'}
 events=[];previous=0
 def observe(frame,ram):
  nonlocal previous
  count=dll.gaw_timing_count();p=dll.gaw_timing_events()
  for n in range(previous,count):
   pc,cycles,irq,room,clock,hl,de,bc=[p[n*8+k] for k in range(8)]
   if frame>=3000:events.append(dict(frame=frame,pc=hex(pc),master_cycles=cycles,irq_master_cycles=irq,room=room,clock=clock,hl=hl,de=de,bc=bc))
  previous=count
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3160,ROOT/f'validation/sms-actor-loading-profile{suffix}',set(),[(200,220,0)]+PRESSES,core=core,ram_observer=observe,core_options=options)
 events=[e for e in events if e['room']==0xa4]
 start=next(e for e in events if e['pc']=='0x1780');end=next(e for e in events if e['pc']=='0x18e1');done=next(e for e in events if e['pc']=='0x24ed')
 remaps=[e for e in events if e['pc']=='0x1d0d' and start['master_cycles']<=e['master_cycles']<=end['master_cycles']]
 resources=load_room_actors((ROOT/'input/original.sms').read_bytes(),0xa4)[4]
 models=[resource_cost((ROOT/'input/original.sms').read_bytes(),e) for e in resources]
 checks=[]
 for n,event in enumerate(events[:-1]):
  if event['pc']!='0x1d0d':continue
  following=events[n+1];assert following['pc']=='0x18b7'
  observed=((following['master_cycles']-event['master_cycles'])-(following['irq_master_cycles']-event['irq_master_cycles']))//15
  nominal=remap_cost(event['de']-event['hl'],event['hl'])
  core_model=remap_cost(event['de']-event['hl'],event['hl'],ini_tstates=20)
  assert observed==core_model,(observed,core_model)
  checks.append(dict(decoded_bytes=event['de']-event['hl'],nominal_z80_isa_tstates=nominal,reference_core_tstates=core_model,observed_tstates=observed,reference_core_ini_extra_tstates_per_instruction=4))
 report=dict(resource_cycle_models=models,remap_source_cycle_checks=checks,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),region='pal' if suffix else 'auto',cycles_per_tstate=15,room=0xa4,original_rle_and_remap_resources=resources,actor_loader_start_frame=start['frame'],actor_loader_end_frame=end['frame'],pre_gameplay_frame=done['frame'],actor_loader_tstates=(end['master_cycles']-start['master_cycles'])//15,interrupt_tstates_during_loader=(end['irq_master_cycles']-start['irq_master_cycles'])//15,foreground_tstates_during_loader=((end['master_cycles']-start['master_cycles'])-(end['irq_master_cycles']-start['irq_master_cycles']))//15,events=events,notes='Diagnostic hook only observes PCs, registers and cycle deltas; never substitutes source/native RAM or captured state into the cartridge.')
 (ROOT/f'analysis/actor_loading_profile{suffix}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['events','original_rle_and_remap_resources']},indent=2))
if __name__=='__main__':main()
