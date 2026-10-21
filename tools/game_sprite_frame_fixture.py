"""Original sprite builder -> original0B95/full IRQ in a compact RAM caller."""
from validate_source_sprite_scene import ROOT,vectors
def generate():
 rom,rows=vectors();code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0xc100+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 label('case');emit('f32a80d12200c0af3252c03a85d147')
 label('raster');emit('db7eb8');jp('c2','raster');emit('dbbffbcd3809cd950bf33e013252c0')
 emit('2a80d12311'+len(rows).to_bytes(2,'little').hex()+'b7ed52');jp('ca','done')
 emit('3a82d132feff2a83d11100c001901fedb03e0132feff');jp('c3','case')
 label('done');jp('c3','done')
 for at,name in fix:code[at:at+2]=labels[name].to_bytes(2,'little')
 assert len(code)<512
 seeds=[]
 for index,(name,raw) in enumerate(rows):
  b=bytearray(raw);b[:2]=index.to_bytes(2,'little');b[0x52]=0;b[0x2e]=0;b[0x33]=0 if index%4==0 else 1;b[0x42]=b[0x45]=0
  b[0x34:0x36]=bytes.fromhex('00dd');b[0x1d00:0x1d40]=bytes(64)
  b[0x100:0x300]=bytes(512);b[0x100:0x100+len(code)]=code
  b[0x1180:0x1186]=index.to_bytes(2,'little')+bytes([16+(index+1)//2])+(0x4000+((index+1)%2)*8192).to_bytes(2,'little')+bytes([[0,180,188,190,191,192,200,218][index%8]])
  seeds.append((name,bytes(b)))
 image=bytearray(2*1024*1024);image[:len(rom)]=rom;image[:3]=bytes.fromhex('c38900')
 boot=bytearray(bytes.fromhex('f331f0dfed56af32fcff32fdff3e1032feff'))
 for reg,value in [(0,4),(1,160),(2,255),(3,255),(4,255),(5,255),(6,255)]:boot+=bytes([0x3e,value,0xd3,0xbf,0x3e,128+reg,0xd3,0xbf])
 boot+=bytes.fromhex('2100401100c001901fedb03e0132feffc300c1');assert 0x89+len(boot)<=0x137;image[0x89:0x89+len(boot)]=boot
 for index,(_,raw) in enumerate(seeds):start=(16+index//2)*16384+(index%2)*8192;image[start:start+8192]=raw
 for a,b in [(0x38,0x45),(0x137,0x227),(0x293,0x365),(0x938,0xaa4),(0xb95,0xbc6),(0x1f54,0x1f90),(0x3b07,0x3b50),(0x10000,0x14000),(0x18000,0x1c000),(0x30000,0x34000)]:assert image[a:b]==rom[a:b]
 return bytes(image),seeds,labels

def unpack_body(raw):
 """Source snapshot929 bytes plus mapper; patches only those source ranges."""
 result=[];k=0
 for address,count in [(0,80),(0x303,1),(0x1100,128)]+[(0x300+n*48+0x1b,2) for n in range(32)]+[(0x1d00,256),(0x1e00,400),(0x1fff,1)]:
  result.append((address,raw[k:k+count]));k+=count
 assert k==930;return result
