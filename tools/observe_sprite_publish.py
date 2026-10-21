"""Observe sprite VRAM writes around the rejected PAL frame."""
import contextlib,ctypes as c,io,json,struct,sys
from game_sprite_frame_fixture import ROOT
from validate_actor_tick import PRESSES
from run_core import run
from validate_sprite_scene_timed import sha

def main():
 region='auto' if '--ntsc' in sys.argv else 'pal';suffix='_ntsc' if region=='auto' else '';folder=ROOT/('validation/md-sprite-publish'+suffix);folder.mkdir(exist_ok=True);core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_sprite_publish_libretro.dll';dll=c.CDLL(str(core));dll.gaw_sprite_reset.argtypes=[c.c_uint];dll.gaw_sprite_size.restype=dll.gaw_sprite_error.restype=c.c_uint;dll.gaw_sprite_data.restype=c.c_void_p;results=[]
 for label,path in [('v0210','versions/v0210-4678a4f4/gaw-megadrive-v0210.bin'),('v0214','versions/v0214-b224e777/gaw-megadrive-v0214.bin'),('v0215','versions/v0215-ba2279cd/gaw-megadrive-v0215.bin'),('v0216','versions/v0216-5c4a7b35/gaw-megadrive-v0216.bin'),('v0217','versions/v0217-d2b31074/gaw-megadrive-v0217.bin'),('v0218','versions/v0218-399be6a3/gaw-megadrive-v0218.bin')]:
  dll.gaw_sprite_reset(0);events=[]
  def ram(frame,data):
   assert not dll.gaw_sprite_error();raw=c.string_at(dll.gaw_sprite_data(),dll.gaw_sprite_size()*32)
   events.extend([[frame,*struct.unpack_from('<8I',raw,p)] for p in range(0,len(raw),32)]);dll.gaw_sprite_reset(int(3117<=frame<3122))
  rom=ROOT/path
  with contextlib.redirect_stdout(io.StringIO()):run(rom,3123,folder/label,{3120},PRESSES,ram_observer=ram,core=core,core_options={'genesis_plus_gx_region_detect':region})
  (folder/(label+'-events.json')).write_text(json.dumps(events)+'\n');groups=[]
  for frame,cycles,address,value,pc,line,code,reg,offset in events:
   if value&0x80000000:
    groups.append(dict(frame=frame,kind='sat-dma',first_address=address,last_address=address+(value&65535)*2-2,first_cycles=cycles,last_cycles=offset,first_line=line,last_line=reg,words=value&65535,pc=pc));continue
   kind='sat' if 0xf400<=address<0xf600 else 'clone' if 0x8000<=address<0x9900 else 'other'
   if not groups or groups[-1]['frame']!=frame or groups[-1]['kind']!=kind or address!=groups[-1]['last_address']+2:
    groups.append(dict(frame=frame,kind=kind,first_address=address,last_address=address,first_cycles=cycles,last_cycles=cycles,first_line=line,last_line=line,words=0,pc=pc))
   g=groups[-1];g.update(last_address=address,last_cycles=cycles,last_line=line,words=g['words']+1)
  interesting=[g for g in groups if g['kind']!='other'];
  if label in ['v0216','v0217','v0218']:assert all(g['kind']=='sat-dma' and g['first_line']>=224 and g['last_line']>=224 for g in interesting if g['kind'].startswith('sat')) and any(g['kind']=='sat-dma' for g in interesting)
  if label=='v0218':assert (folder/label/'frame_03120.png').read_bytes()==(ROOT/('validation/world-frame-coherence-v0218/'+region+'/frame_03120.png')).read_bytes(),('observer parity',region)
  results.append(dict(label=label,rom_sha256=sha(rom.read_bytes()),groups=interesting));print(label,json.dumps([g for g in interesting if g['frame']==3120]),flush=True)
 (ROOT/('analysis/sprite_publish_timing'+suffix+'_report.json')).write_text(json.dumps(dict(core_sha256=sha(core.read_bytes()),results=results,limits=['Read-only VRAM writes at native FIFO admission/completion after CPU stall; no DMA-source tracing. Physical raster/PC/address/data observed around PAL3120.']),indent=2)+'\n')
if __name__=='__main__':main()
