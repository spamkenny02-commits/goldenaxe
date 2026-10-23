"""Read-only unchanged SMS overview instruction intervals and room snapshots."""
import argparse,contextlib,ctypes as c,io,json
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from archive_lossless_evidence import sha

def main():
 p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--pal',action='store_true');p.add_argument('--edited',action='store_true');p.add_argument('--all-flags',action='store_true');p.add_argument('--ice',action='store_true');a=p.parse_args();core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_overview_libretro.dll';dll=c.CDLL(str(core));dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_screen_scene_size.restype=c.c_uint;dll.gaw_screen_scene_data.restype=c.POINTER(c.c_uint8);events=[];previous=0;states=[]
 writes=[(2810,0xdf,b'\13'),(2810,0xeb,b'\1'),(2810,0xf5,b'\0'),(2810,0x600,bytes(768))]
 if a.all_flags:writes.append((2810,0x110,bytes([1])*240))
 if a.ice:writes.append((2810,0xac,b'\1'))
 if a.edited:writes.append((2810,0x111,b'\1'))
 def observe(f,r):
  nonlocal previous
  if f<2858:dll.gaw_timing_reset();previous=0;return
  count=dll.gaw_timing_count();ptr=dll.gaw_timing_events();assert previous<=count<32768
  for n in range(previous,count):events.append([f]+[int(ptr[n*8+j]) for j in range(8)])
  previous=count;states.append(dict(frame=f,clock=r[0x2f],room=int.from_bytes(r[0xb9:0xbb],'little')))
 folder=ROOT/f'validation/overview-source-{a.tag}';assert not folder.exists()
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3450,folder,{2859,2868,3200,3356,3400},[(200,220,0)]+PRESSES[:8]+[(2860,2861,8)],core=core,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
 size=dll.gaw_screen_scene_size();assert size==225,size;raw=c.string_at(dll.gaw_screen_scene_data(),size*8192);(folder/'scenes.bin').write_bytes(raw);(folder/'events.json').write_bytes(json.dumps(events).encode());(folder/'states.json').write_bytes(json.dumps(states).encode());print(a.tag,'events',len(events),'rooms',size,'clocks',states[:3],states[-1])
if __name__=='__main__':main()
