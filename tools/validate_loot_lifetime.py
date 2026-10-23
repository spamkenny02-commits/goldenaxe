"""Observe full loot lifetime from controlled states on SMS and production MD."""
import argparse,contextlib,io,json
from pathlib import Path
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
 p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--diagnostic',action='store_true');p.add_argument('--type',type=int,default=8);p.add_argument('--pal',action='store_true');a=p.parse_args();sy=symbols(ROOT/'megadrive/out/release/symbol.txt');clock=0;traces={};folders={};ends={};states={}
 loot=bytearray(336)
 for slot in range(7):loot[slot*48]=a.type;loot[slot*48+0x11]=32+slot*16;loot[slot*48+0x13]=32+slot*28
 captures={2999,3000,3001,3002,3003,3004,3239,3240,3241,3242,3243,3244,3245,3246,3247,3248,3249,3250,3251,3252,3253,3254,3255,3256,3257,3258,3259,3260,3358,3359,3360,3361,3362,3363,3364,3365,3366,3370,3399}
 for tag in ['sms','md']:
  source=tag=='sms';folder=ROOT/f'validation/loot-lifetime-{a.tag}-{tag}';assert not folder.exists();folders[tag]=folder;rows={};st={}
  writes=[(3000,0x4b0,bytes(loot)),(3000,0x600,bytes(768)),(3000,0x330,bytes(384)),(3000,0x310,b'\0\x70\0\x88')] if source else [(3000,sy['world_loot_state'],bytes(loot)),(3000,sy['world_actor_state'],bytes(768)),(3000,sy['world_spell_state'],bytes(48)),(3000,sy['hero_x'],b'\x88\0'),(3000,sy['hero_y'],b'\x70\0'),(2980,sy['vtimer'],clock.to_bytes(4,'big')),(2980,sy['world_clock_shift'],bytes(4))]
  def observe(f,r):
   nonlocal clock
   if source and f==2979:clock=r[0x2f]
   if f<2999:return
   data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k));word=lambda n:int.from_bytes(data(n,2),'big')
   rows[f]=bytes(r[0x4b0:0x600]) if source else data('world_loot_state',336)
   st[f]=dict(clock=r[0x2f] if source else (int.from_bytes(data('vtimer',4),'big')-int.from_bytes(data('world_clock_shift',4),'big'))&255,room=int.from_bytes(r[0xb9:0xbb],'little') if source else word('room_id'),x=r[0x313] if source else word('hero_x')>>8,y=r[0x311] if source else word('hero_y')>>8)
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),3400,folder,captures,([(200,220,0)] if source else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if a.pal else 'auto'})
  traces[tag]=rows;states[tag]=st;ends[tag]=next((f for f,row in rows.items() if f>3000 and not any(row)),None)
 rows_equal=all(traces['sms'][f]==traces['md'][f] for f in range(3000,3401));stats_equal=states['sms']==states['md'];images=[]
 for f in sorted(captures-{2999,3000,3001}):
  x=Image.open(folders['sms']/f'frame_{f:05d}.png').convert('RGB');y=Image.open(folders['md']/f'frame_{f:05d}.png').convert('RGB').crop((0,16,256,208));colors=set(x.getdata());conv={v:min(colors,key=lambda c:sum((a-b)**2 for a,b in zip(v,c))) for v in set(y.getdata())};diff=sum(a!=conv[b] for a,b in zip(x.getdata(),y.getdata()));images.append(dict(frame=f,pixels=diff))
 result=dict(passed=rows_equal and stats_equal and not any(x['pixels'] for x in images),record_frames_compared=401,md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),type=a.type,region='pal' if a.pal else 'auto',records_equal=rows_equal,states_equal=stats_equal,expiry_frame=ends,images=images,all_pixels_equal=not any(x['pixels'] for x in images),full_game_verified=False)
 (ROOT/f'analysis/loot_lifetime_{a.tag}_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
 for tag in ['sms','md']:(folders[tag]/'loot-records.json').write_bytes(json.dumps({str(f):r.hex() for f,r in traces[tag].items()}).encode())
 assert result['passed'] or a.diagnostic
if __name__=='__main__':main()
