"""Natural New Game/Continue music hook; no RAM or ROM injections."""
import contextlib,ctypes as c,hashlib,io,json,re
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
def main():
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_menu_libretro.dll';dll=c.CDLL(str(core));dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};cases=[]
 source=(ROOT/'input/original.sms').read_bytes();assert source[0x14f3:0x14f8]==bytes.fromhex('3e89cdf81c')
 for region in ['auto','pal']:
  result={}
  for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
   tracks={};audio={};active={};events=[];previous=[0]
   def observe(f,r):
    if tag=='sms':
     count=dll.gaw_timing_count();p=dll.gaw_timing_events()
     for n in range(previous[0],count):
      if p[n*8]==0x14f3:events.append(f)
     previous[0]=count;record=r[0x1e00:0x1f90]
    else:
     def data(n,l):return bytes(r[(sy[n]+i)^1] for i in range(l))
     tracks[f]=int.from_bytes(data('sound_current_track',2),'big');record=data('sound_ram',0x190)
     assert not int.from_bytes(data('sound_unhandled_command',2),'big')
    if f>=1100:active[f]=sum(bool(record[0x40+n*48]&128) for n in range(4))
   with contextlib.redirect_stdout(io.StringIO()):run(rom,1600,ROOT/f'validation/start-menu-audio-{tag}-{region}',{1200},[(200,220,0),(920,935,0)],skip_intro=False,ram_observer=observe,core=core,psg_observer=lambda f,p:audio.update({f:p}),core_options={'genesis_plus_gx_region_detect':region})
   assert all(active.values()),(region,tag,'no music channels')
   audible=[f for f,p in audio.items() if f>=1100 and any(p[n]<15 for n in [1,3,5,7])]
   assert len(audible)>400,(region,tag,len(audible))
   if tag=='sms':assert events
   else:assert all(tracks[f]==0x89 for f in range(1100,1601)),set(tracks.values())
   result[tag]=dict(track_89_source_call_frames=events,active_music_frames=len(active),audible_frames=len(audible))
  cases.append(dict(region=region,results=result))
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,natural_controller_input=True,ram_injections=False,full_game_ported=False,limits=['Natural source14F3 hook and native89 selection, active channels and audible PSG checked.','Exact sequence/pitch/envelopes validated separately by validate_music; natural track start frame and audio waveforms are not claimed equal.'])
 (ROOT/'validation/start_menu_audio_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Natural start menu: track89 active and audible, PAL and NTSC.')
if __name__=='__main__':main()
