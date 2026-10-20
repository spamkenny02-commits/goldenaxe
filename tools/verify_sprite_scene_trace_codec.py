"""Verify lossless native ROM trace assets against original instruction records."""
import gzip,json,re,struct
from validate_sprite_scene_timed import ROOT,sha
def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/sprite-scene-timed-v0203';m=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix()
 if name in m['files']:
  b=(archive/name).read_bytes();assert sha(b)==m['files'][name];return b
 item=m['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==item['raw_sha256'] and len(b)==item['raw_bytes'];return b
def main():
 results=[]
 for suffix in ['','-irq']:
  source=ROOT/('validation/sprite-scene-timed'+suffix);native=ROOT/('validation/sprite-scene-timed'+suffix+'-68k');report=json.loads(read(ROOT/('analysis/sprite_scene_timed'+suffix.replace('-','_')+'_68k_report.json')))
  kernel=read(native/'out/release/rom.bin');assert sha(kernel)==report['kernel_sha256'];symbols={m[2]:int(m[1],16) for line in read(native/'out/release/symbol.txt').decode().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))}
  for region in ['ntsc','pal']:
   raw=read(source/(region+'-records.bin'));packed=read(native/('src/'+region+'.bin'));address=symbols['scene_trace_'+region];assert kernel[address:address+len(packed)]==packed
   pos=cursor=cases=points=0
   while pos<len(raw):
    tag,size=struct.unpack_from('<II',raw,pos);pos+=8;events=raw[pos:pos+size];pos+=size
    count,phase,r,f,tstates,m1,irqs,elapsed,sprites=struct.unpack_from('<IIBB2xIIIII',packed,cursor);cursor+=32;assert count==size//608
    state=bytearray(packed[cursor:cursor+581]);cursor+=581;origin=struct.unpack_from('<I',events,4)[0];time=0
    assert tag==cases and (phase,r,f)==struct.unpack_from('<III',events,8)
    for n in range(count):
     pc,delta,refresh,iff,changes=struct.unpack_from('<HHBBH',packed,cursor);cursor+=8;time+=delta
     for _ in range(changes):
      index,value=struct.unpack_from('<HB',packed,cursor);cursor+=3;assert index<581;state[index]=value
     original=events[n*608:(n+1)*608];opc,master,_,oreg,oiff,_=struct.unpack_from('<6I',original)
     assert pc==opc and time==(master-origin)&0xffffffff and refresh==oreg and iff==oiff
     assert state==original[24:24+581]
    assert elapsed==time;cases+=1;points+=count
   assert cursor==len(packed) and cases==133 and points==110143
   results.append(dict(interrupts=bool(suffix),region=region,cases=cases,points=points,ram_bytes_per_point=581,raw_records_sha256=sha(raw),native_packed_sha256=sha(packed),kernel_sha256=sha(kernel)));print(suffix or 'di',region,'lossless trace and actual ROM assets verified')
 (ROOT/'analysis/sprite_scene_trace_codec_report.json').write_text(json.dumps(dict(results=results,limits=['Every source instruction PC/time/R/IFF and581 RAM bytes reconstructed exactly from native lossless assets. Native linked ROM bytes match these assets. This is evidence recovery/encoding validation; original full IRQ and video deadline remain unproved.']),indent=2)+'\n')
if __name__=='__main__':main()
