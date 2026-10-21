"""Recover IRQ-driven physical MD sprite planes and linked assets losslessly."""
import gzip,json,re
from pathlib import Path
from verify_game_sprite_frame_assets import read as parent_read,records
from validate_md_game_sprite_frame import physical_plane
from md_sms_sprite8_fixture import inputs
from md_z80_source_video_fixture import convert_sms_patterns
from validate_sms_sprite8 import source_plane
from game_sprite_frame_fixture import ROOT
from validate_sprite_scene_timed import sha

def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/md-game-sprite-frame-v0203';manifest=archive/'manifest.json';name=path.relative_to(ROOT).as_posix()
 if manifest.exists():
  m=json.loads(manifest.read_bytes())
  if name in m['files']:
   b=(archive/name).read_bytes();assert sha(b)==m['files'][name];return b
  if name in m['compressed']:
   item=m['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes'];return raw
 return parent_read(path)

def main():
 folder=ROOT/'validation/md-game-sprite-frame';report=json.loads(read(ROOT/'analysis/md_game_sprite_frame_report.json'));assert sha(read(ROOT/'analysis/game_sprite_frame_report.json'))==report['source_report_sha256']
 kernel=read(folder/'out/release/rom.bin');assert sha(kernel)==report['kernel_sha256'];symbols={m[2]:int(m[1],16) for line in read(folder/'out/release/symbol.txt').decode().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))}
 for name in ['inputs','low','bank6','bank12','ntsc','pal']:
  raw=parent_read(ROOT/('validation/game-sprite-frame-68k/src/'+name+'.bin'));address=symbols['frame_'+name];assert kernel[address:address+len(raw)]==raw==read(folder/('src/'+name+'.bin'))
 _,patterns,regs=inputs();packed=convert_sms_patterns(patterns);address=symbols['frame_patterns'];assert kernel[address:address+len(packed)]==packed==read(folder/'src/patterns.bin');results=[]
 for r in report['results']:
  region=r['region'];ports=records(parent_read(ROOT/('validation/game-sprite-frame/'+region+'-ports.bin')));assert len(r['cases'])==len(ports)==133 and r['video_contracts']==5
  for row,port in zip(r['cases'],ports):
   import struct
   index=row['case'];sat=bytes(struct.unpack_from('<I',port,n+8)[0] for n in range(0,len(port),20) if struct.unpack_from('<I',port,n)[0]==2);vram=read(folder/(region+'-'+str(index)+'-vram.bin'));actual,raw=physical_plane(vram,r['sat_base']);wanted,_,_=source_plane(sat,patterns,regs[0],regs[2]);assert actual==wanted and sha(actual)==row['plane_sha256'] and sha(sat)==row['sat_sha256'];count=row['sprites'];assert raw[count*8:]==bytes((64-count)*8)
  results.append(dict(region=region,cases=133,pixels_compared=133*49152,physical_words_read_back=r['video_words'],dma_jobs=r['video_jobs'],kernel_sha256=sha(kernel)));print(region,'133 IRQ-produced physical sprite planes recovered exactly')
 (ROOT/'analysis/md_game_sprite_frame_recovery_report.json').write_text(json.dumps(dict(results=results,limits=['Original source SAT/planar patterns compare to actual captured MD VRAM. Linked native ROM inputs match the independently verified parent frame assets. Source entry/status and pattern shadow are supplied. No deadline, display reveal or hardware PSG delivery proof.']),indent=2)+'\n')
if __name__=='__main__':main()
