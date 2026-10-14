"""Measure emulated frames, never host execution time, against the source ROM."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 region='pal' if '--pal' in sys.argv else 'auto'
 suffix='-pal' if region=='pal' else ''
 options={'genesis_plus_gx_region_detect':region}
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 fields=[('game_state',0x1d,1),('room_id',0xb9,2),('hero_y',0x310,2),('hero_x',0x312,2),('hero_direction',0x30a,1),('hero_animation',0x30b,1),('hero_counter',0x304,1)]
 results=[]
 base=PRESSES[:8]
 for name,inputs,last,start in [('hero',base+[(2600,2620,7),(2650,2690,4),(2720,2760,6),(2790,2830,5),(2855,2940,4),(2950,2970,5)],2970,2600),('horizontal',base+[(2600,2649,6),(2700,2714,4),(2750,2900,6),(3000,3100,7)],3130,2765),('vertical',PRESSES,3160,3000)]:
  records={};cadence={}
  for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
   samples={}
   def observe(f,d):
    if f<start:return
    samples[f]=[int.from_bytes(d[o:o+n],'little') if tag=='sms' else int.from_bytes(d[sy[k]:sy[k]+2],'little') for k,o,n in fields]
   folder=ROOT/f'validation/timing-{name}-{tag}{suffix}'
   with contextlib.redirect_stdout(io.StringIO()):run(rom,last,folder,set(),([(200,220,0)] if tag=='sms' else [])+inputs,ram_observer=observe,core_options=options)
   records[tag]=samples;cadence[tag]=json.loads((folder/'capture.json').read_text())['fps']
  differences=[dict(frame=f,sms=a,md=records['md'][f]) for f,a in records['sms'].items() if a!=records['md'][f]]
  intervals={}
  for tag,rec in records.items():
   spans=[];begin=None
   for f,a in rec.items():
    if a[0]==10 and begin is None:begin=f
    elif a[0]!=10 and begin is not None:spans.append([begin,f-1,f-begin]);begin=None
   if begin is not None:spans.append([begin,last,last-begin+1])
   intervals[tag]=spans
  motion={}
  for tag,rec in records.items():
   changes=[f for f in range(start+1,last+1) if rec[f][2:4]!=rec[f-1][2:4]]
   deltas=[(rec[f][3]-rec[f-1][3])/256 for f in changes if rec[f][2]==rec[f-1][2] and rec[f][1]==rec[f-1][1] and rec[f][0]==rec[f-1][0]==12]
   motion[tag]=dict(position_change_frames=len(changes),horizontal_nonzero_steps_px=sorted(set(deltas)))
  results.append(dict(sequence=name,first_frame=start,last_frame=last,frames_compared=len(records['sms']),cadence_hz=cadence,differing_state_frames=len(differences),examples=differences[:12],transition_intervals=intervals,motion=motion))
 # One enemy with a long deterministic movement counter; no ongoing state injections.
 initial=bytearray((ROOT/'validation/sms-vertical-check/ram_03101.bin').read_bytes()[0x600:0x630])
 initial[4]=120;initial[5]=initial[6]=0;initial[0x14:0x18]=bytes.fromhex('40000000')
 initial[0x10:0x14]=bytes.fromhex('00500078')
 velocities=[64,128,256,384,-64,-128,-256,-384];actors=bytearray(768)
 for slot,speed in enumerate(velocities):
  e=bytearray(initial);e[0x10:0x12]=((32 if speed>0 else 140)<<8).to_bytes(2,'little');e[0x12:0x14]=(160<<8).to_bytes(2,'little');e[0x14:0x16]=speed.to_bytes(2,'little',signed=True);actors[slot*48:(slot+1)*48]=e
 data=bytes(actors)
 enemy={}
 for tag,rom,off in [('sms',ROOT/'input/original.sms',0x600),('md',ROOT/'gaw-megadrive.bin',sy['world_actor_state'])]:
  samples={}
  def observe(f,d):
   if 3102<=f<=3148:
    rows=[]
    for slot in range(8):
     o=off+slot*48;e=bytearray(d[o:o+48])
     if tag=='md':e[::2]=d[o+1:o+48:2];e[1::2]=d[o:o+48:2]
     rows.append(list(e[4:8])+list(e[0x10:0x18]))
    samples[f]=rows
  folder=ROOT/f'validation/timing-enemy-{tag}{suffix}'
  with contextlib.redirect_stdout(io.StringIO()):run(rom,3148,folder,set(),([(200,220,0)] if tag=='sms' else [])+PRESSES,ram_writes=[(3102,off,data)],ram_observer=observe,core_options=options)
  enemy[tag]=samples
 differences=[dict(frame=f,sms=a,md=enemy['md'][f]) for f,a in enemy['sms'].items() if a!=enemy['md'][f]]
 report=dict(region=region,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),basis='One retro_run is one emulated video frame; actual core FPS is recorded, host speed is irrelevant',fields=[x[0] for x in fields],natural_input_sequences=results,enemy=dict(frames_compared=47,initial_record_injected_once=True,controlled_enemies=8,velocity_y_px_per_tick=[v/256 for v in velocities],first_and_last_samples={k:[v[3102],v[3148]] for k,v in enemy.items()},differing_motion_counter_frames=len(differences),examples=differences[:12]),scope='Normal movement and three exterior scroll directions; eight deterministic enemy movements. Not all enemy AI, RNG or hardware workloads.')
 (ROOT/f'validation/timing{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 assert not differences
 assert all(x['differing_state_frames']==0 for x in results )
if __name__=='__main__':main()
