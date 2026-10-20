"""Independent mode4 scanline oracle versus native8x8 clone/SAT conversion."""
import ctypes as c,hashlib,json,os,random,subprocess
from pathlib import Path
from md_z80_source_video_fixture import convert_sms_patterns
ROOT=Path(__file__).resolve().parents[1]
class Frame(c.Structure):
 _fields_=[('columns',c.c_uint32*64),('sat',c.c_uint16*256),('source_tile',c.c_uint16*64),('rows',c.c_uint8*64),('count',c.c_uint16),('tile_base',c.c_uint16),('overflow',c.c_uint8)]
def sha(b):return hashlib.sha256(b).hexdigest()
def source_plane(sat,vram,r0,r6):
 out=bytearray(256*192);overflow=False;count=next((i for i,v in enumerate(sat[:64]) if v==208),64)
 for y in range(192):
  selected=[(i,(y-sat[i]-1)&255) for i in range(count) if ((y-sat[i]-1)&255)<8]
  overflow|=len(selected)>8
  for i,row in reversed(selected[:8]):
   x=sat[64+i*2]-(8 if r0&8 else 0);tile=(256 if r6&4 else 0)+sat[65+i*2];planes=vram[tile*32+row*4:tile*32+row*4+4]
   for col in range(8):
    xx=x+col
    if not 0<=xx<256 or (r0&32 and xx<8):continue
    color=sum(((v>>(7-col))&1)<<p for p,v in enumerate(planes))
    if color:out[y*256+xx]=color
 return bytes(out),bool(overflow),count
def native_plane(frame,tiles):
 out=bytearray(256*192)
 for y in range(192):
  eligible=[];index=0
  for _ in range(64):
   yy=(frame.sat[index*4]&511)-144
   if yy<=y<yy+8:eligible.append((index,y-yy))
   link=frame.sat[index*4+1]&127
   if not link:break
   assert link<64;index=link
  for i,row in reversed(eligible[:16]):
   x=(frame.sat[i*4+3]&511)-128;value=tiles[i][row]
   for col in range(8):
    xx=x+col
    if 0<=xx<256:
     color=(value>>((7-col)*4))&15
     if color:out[y*256+xx]=color
 return bytes(out)
def main():
 folder=ROOT/'validation/sms-sprite8';folder.mkdir(exist_ok=True);sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),str(ROOT/'megadrive/src/source_sms_sprite8.c'),'-o',str(folder/'sprite8.dll')]
 built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
 lib=c.CDLL(str(folder/'sprite8.dll'));p8=c.POINTER(c.c_uint8);p32=c.POINTER(c.c_uint32);pf=c.POINTER(Frame)
 prep=lib.source_sms_sprite8_prepare;prep.argtypes=[pf,p8,c.c_uint8,c.c_uint8,c.c_uint8,c.c_uint16];prep.restype=c.c_uint8
 tile=lib.source_sms_sprite8_tile;tile.argtypes=[pf,p32,c.c_uint16,p32];tile.restype=c.c_uint8
 source=ROOT/'validation/sms-vertical-check';provenance=json.loads((source/'capture.json').read_bytes());rom=(ROOT/'input/original.sms').read_bytes();assert provenance['rom_sha256']==sha(rom)
 rows=[];invalid=0;last_patterns=None
 def check_case(name,sat,vram,r0=6,r1=224,r6=255):
  nonlocal last_patterns
  packed=convert_sms_patterns(vram[:16384]);patterns=(c.c_uint32*4096)(*[int.from_bytes(packed[n:n+4],'big') for n in range(0,16384,4)]);frame=Frame();raw=(c.c_uint8*192).from_buffer_copy(sat)
  assert not prep(c.byref(frame),raw,r0,r1,r6,1024)
  expected,overflow,count=source_plane(sat,vram,r0,r6);assert frame.count==count and bool(frame.overflow)==overflow,(name,'metadata')
  tiles=[]
  for n in range(count):
   values=(c.c_uint32*8)();assert not tile(c.byref(frame),patterns,n,values);tiles.append(list(values))
  assert native_plane(frame,tiles)==expected,(name,'pixels')
  rows.append(dict(case=name,sprites=count,overflow=overflow,pixel_sha256=sha(expected)));last_patterns=patterns
  return frame
 for f in range(3101,3161):
  v=(source/f'vram_{f:05d}.bin').read_bytes();r=(source/f'vdp_regs_{f:05d}.bin').read_bytes();base=(r[5]&126)*128;sat=v[base:base+64]+v[base+128:base+256]
  check_case('source-'+str(f),sat,v,r[0],r[1],r[6])
  if f==3120:
   (folder/'source-sat.bin').write_bytes(sat);(folder/'source-patterns.sms').write_bytes(v[:16384]);(folder/'source-regs.bin').write_bytes(r)
 rng=random.Random(0x8a7864);vram=rng.randbytes(16384)
 for y in range(256):
  sat=bytearray([208]*192);sat[0]=y;sat[64]=255;sat[65]=255;check_case('all-y-'+str(y),sat,vram)
 for count in [0,1,8,9,16,17,63,64]:
  for y in [0,31,184,191,200,208,220,248,255]:
   for r0 in [4,12,36,44]:
    sat=bytearray([208]*192)
    for i in range(count):sat[i]=y;sat[64+i*2]=(255 if i%3==0 else i*7)&255;sat[65+i*2]=i*3
    check_case(f'stress-{count}-{y}-{r0}',sat,vram,r0,224,0)
 for k in range(96):
  sat=bytearray(rng.randbytes(192));count=rng.randrange(65)
  if count<64:sat[count]=208
  check_case('random-'+str(k),sat,vram,rng.choice([4,12,36,44]),224,rng.choice([0,4]))
 frame=Frame();c.memset(c.byref(frame),0xa5,c.sizeof(frame));sat=(c.c_uint8*192)();before=bytes(frame)
 for r0,r1,base in [(0,224,1024),(4,225,1024),(4,226,1024),(4,232,1024),(4,240,1024),(4,224,1985)]:
  assert prep(c.byref(frame),sat,r0,r1,255,base)==1 and bytes(frame)==before;invalid+=1
 assert prep(c.byref(frame),None,4,224,255,1024)==1 and bytes(frame)==before;invalid+=1
 assert prep(None,sat,4,224,255,1024)==1;invalid+=1
 frame=check_case('empty',bytes([208]*192),vram);out=(c.c_uint32*8)(*[0xa5a5a5a5]*8);before=bytes(out)
 for f,p,index in [(None,last_patterns,0),(c.byref(frame),None,0),(c.byref(frame),last_patterns,0)]:
  assert tile(f,p,index,out)==1 and bytes(out)==before;invalid+=1
 report=dict(source_rom_sha256=sha(rom),sources={name:sha((ROOT/'megadrive/src'/name).read_bytes()) for name in ['source_sms_sprite8.c','source_sms_sprite8.h']},cases=len(rows),pixels_compared=len(rows)*256*192,invalid_atomic_checks=invalid,results=rows,limits=['Component input is a mode4/192,8x8,no-zoom SAT and immutable512tile MD shadow.60real source snapshots plus allY/stress/random cases; independent planar SMS scanline oracle and MD first16sprite evaluation compare the full256x192 sprite plane. This is renderer input verification, not native actor/SAT production, status latency, whole-game integration or physical VDP proof.'])
 (ROOT/'analysis/sms_sprite8_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report['cases'],'sprite plane cases;',report['pixels_compared'],'pixels;',invalid,'atomic invalid checks')
if __name__=='__main__':main()
