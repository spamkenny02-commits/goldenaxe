"""Recover source frame evidence and verify the assets linked into68000 ROM."""
import gzip,json,re,struct
from game_sprite_frame_fixture import ROOT,generate
from validate_sprite_scene_timed import sha

def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/game-sprite-frame-v0203';m=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix()
 if name in m['files']:
  raw=(archive/name).read_bytes();assert sha(raw)==m['files'][name];return raw
 item=m['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes'];return raw

def records(raw):
 p=0;rows=[]
 while p<len(raw):
  tag,size=struct.unpack_from('<II',raw,p);p+=8;assert tag==len(rows);rows.append(raw[p:p+size]);p+=size
 assert p==len(raw);return rows

def main():
 native=ROOT/'validation/game-sprite-frame-68k';source=ROOT/'validation/game-sprite-frame';report=json.loads(read(ROOT/'analysis/game_sprite_frame_68k_report.json'));parent=json.loads(read(ROOT/'analysis/game_sprite_frame_report.json'))
 kernel=read(native/'out/release/rom.bin');assert sha(kernel)==report['kernel_sha256'];assert sha(read(ROOT/'analysis/game_sprite_frame_report.json'))==report['source_report_sha256']
 symbols={m[2]:int(m[1],16) for line in read(native/'out/release/symbol.txt').decode().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))}
 image,rows,_=generate();assert sha(image)==parent['fixture_sha256'];inputs=b''.join(b for _,b in rows)
 for name,raw in [('inputs',inputs),('low',image[:32768]),('bank6',image[0x18000:0x1c000]),('bank12',image[0x30000:0x34000])]:
  address=symbols['frame_'+name];assert read(native/('src/'+name+'.bin'))==raw==kernel[address:address+len(raw)]
 h=read(native/'src/offsets.h').decode().split('={',1)[1];numbers=list(map(int,re.findall(r'\d+',h)));assert len(numbers)==2*len(rows)*8;results=[]
 for region_index,region in enumerate(['ntsc','pal']):
  packed=read(native/('src/'+region+'.bin'));address=symbols['frame_'+region];assert kernel[address:address+len(packed)]==packed
  rawpoints=read(source/(region+'-points.bin'));rawports=read(source/(region+'-ports.bin'));r=next(r for r in parent['results'] if r['region']==region);assert sha(rawpoints)==r['points_sha256'] and sha(rawports)==r['ports_sha256']
  points=records(rawpoints);ports=records(rawports);assert len(points)==len(ports)==len(rows);cursor=checkpoint_count=irq_count=port_count=0
  for index,(point,port) in enumerate(zip(points,ports)):
   streams=[b''.join(point[k:k+960] for k in range(0,len(point),960) if struct.unpack_from('<I',point,k)[0]!=0x137)]
   streams.extend(b''.join(port[k:k+20] for k in range(0,len(port),20) if struct.unpack_from('<I',port,k)[0]==kind) for kind in [1,2])
   streams.append(b''.join(point[k:k+960] for k in range(0,len(point),960) if struct.unpack_from('<I',point,k)[0]==0x137))
   base=(region_index*len(rows)+index)*8
   for j,(stream,size) in enumerate(zip(streams,[960,20,20,960])):
    offset,count=numbers[base+2*j:base+2*j+2];assert offset==cursor and len(stream)==count*size and packed[offset:offset+len(stream)]==stream;cursor+=len(stream)
   checkpoint_count+=len(streams[0])//960;irq_count+=len(streams[3])//960;port_count+=(len(streams[1])+len(streams[2]))//20
  assert cursor==len(packed);results.append(dict(region=region,cases=len(rows),checkpoints=checkpoint_count,irq_inputs=irq_count,port_values_dates=port_count,packed_sha256=sha(packed),kernel_sha256=sha(kernel)))
  print(region,'original frame records and actual68000 ROM assets verified')
 (ROOT/'analysis/game_sprite_frame_assets_report.json').write_text(json.dumps(dict(results=results,limits=['Exact byte recovery and ROM linkage for source checkpoints, explicit IRQ status inputs, SAT/PSG values/dates, original ROM banks and input RAM. Hardware status is supplied evidence, not predicted. No whole-game or renderer deadline claim.']),indent=2)+'\n')
if __name__=='__main__':main()
