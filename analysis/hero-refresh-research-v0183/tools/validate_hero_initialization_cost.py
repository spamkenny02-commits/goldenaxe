"""Execute unmodified2C63 across terrain,gear,coordinate and collision branches."""
import contextlib,ctypes as c,hashlib,io,json,itertools
from actor_reference import ROOT
from hero_initialization_cost import hero_initialization_cost
from run_core import run

SOURCE=(ROOT/'input/original.sms').read_bytes()
#x,y,class,old terrain,selected,secondary,curse,boat,amulet,armor,shield,dir,left/right tile,attrs.
BASE=(136,80,0,0,0,0,0,0,0,1,1,1,10,11,0,32)
def row(**changes):
 keys=['x','y','graphics','old_terrain','selected','secondary','curse','boat','amulet','armor','shield','direction','left','right','left_attr','right_attr']
 values=list(BASE)
 for k,v in changes.items():values[keys.index(k)]=v
 return tuple(values)

ROWS=[]
for graphics,old,selected,secondary,direction in itertools.product(range(3),range(6),range(17),[0,3,11,255],range(4)):
 ROWS.append(row(graphics=graphics,old_terrain=old,selected=selected,secondary=secondary,direction=direction))
for graphics in [0,2]:
 base=0x2544 if graphics==0 else 0x2569;values=set()
 for n in range(5):
  record=SOURCE[base+n*4:base+n*4+4];p=int.from_bytes(record[:2],'little');values.update(SOURCE[p:p+record[2]])
 for left,right in itertools.product(sorted(values|{0,255}),repeat=2):ROWS.append(row(graphics=graphics,left=left,right=right))
for graphics,boat,amulet,a,b in itertools.product(range(3),range(2),range(2),[0,32,64,96,128,160,192,224],[0,32,64,96,128,160,192,224]):
 ROWS.append(row(graphics=graphics,boat=boat,amulet=amulet,left_attr=a,right_attr=b))
for armor,shield,curse in itertools.product([0,1,2,3,255],[0,1,2,3,255],[0,1,255]):ROWS.append(row(armor=armor,shield=shield,curse=curse))
for dx,dy in itertools.product(range(8),repeat=2):ROWS.append(row(x=128+dx,y=64+dy))
for x,y in itertools.product([16,23,24,231,232,239],[16,23,24,151,152,159]):ROWS.append(row(x=x,y=y))
ROWS=list(dict.fromkeys(ROWS))

def packed(r):
 x,y,graphics,old,selected,secondary,curse,boat,amulet,armor,shield,direction,left,right,la,ra=r
 address=0xd600+((y-12)&248)*8+(((x-12)&255)>>2&62)
 neighborhood=bytes([left,la,right,ra,left,la,right,ra])*3
 return bytes(r[:12])+address.to_bytes(2,'little')+bytes(18)+neighborhood+bytes(8)

def generate():
 assert len(ROWS)*64+0x80000<=0x200000
 image=bytearray(SOURCE)+bytearray(0x200000-len(SOURCE));code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
 label('case');emit('af3202c03a08c032ffff2100c31101c301af0136a5edb021e0c011e1c00110003601edb0dd2a06c0')
 for i,address in enumerate([0xc313,0xc311,0xc040,0xc041,0xc0df,0xc0e1,0xc0bf,0xc0ec,0xc0f0,0xc0f1,0xc0f2,0xc30a]):
  emit(f'dd7e{i:02x}32'+address.to_bytes(2,'little').hex())
 emit('3e183218c02a06c0110c00195e2356eb2a06c001200009')
 for n in range(3):emit('010800edb0'+('e521380019ebe1' if n<2 else ''))
 emit('cde4243e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011400019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0')
 label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42')
 jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 data=b''.join(packed(r) for r in ROWS);assert len(data)==len(ROWS)*64
 image[0x80000:0x80000+len(data)]=data;image[0x24e7]=0xc9
 folder=ROOT/'validation/hero-initialization-cost';folder.mkdir(exist_ok=True)
 rom=folder/'source.sms';rom.write_bytes(image);return rom,folder

def main():
 rom,folder=generate();core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_hero_libretro.dll'
 dll=c.CDLL(str(core));dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
 dll.gaw_hero_samples.restype=c.c_uint;dll.gaw_hero_entry.restype=c.POINTER(c.c_uint8);dll.gaw_hero_return.restype=c.POINTER(c.c_uint8)
 regions=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];previous_sample=[0];starts={};costs={};checked={};done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   count=dll.gaw_timing_count();events=dll.gaw_timing_events()
   for n in range(previous[0],count):
    e=[events[n*8+k] for k in range(8)]
    if e[0]==0x2c63:starts['current']=e
    elif e[0]==0x24e7:
     a=starts['current'];costs['current']=((e[1]-a[1])-(e[2]-a[2]))//15
   previous[0]=count
   sample=dll.gaw_hero_samples()
   if sample!=previous_sample[0]:
    assert sample==previous_sample[0]+1
    before=c.string_at(dll.gaw_hero_entry(),8192);after=c.string_at(dll.gaw_hero_return(),8192)
    case=int.from_bytes(before[:2],'little');model=hero_initialization_cost(SOURCE,before)
    assert model['foreground_tstates']==costs['current'],(region,case,ROWS[case],costs['current'],model['components'])
    indices=list(range(0x41,0x6c))+list(range(0x300,0x4b0))
    differences=[i for i in indices if model['ram'][i]!=after[i]]
    assert not differences,(region,case,ROWS[case],'RAM',[(hex(i+0xc000),model['ram'][i],after[i]) for i in differences[:12]])
    checked[case]=(costs['current'],hashlib.sha256(bytes(after[i] for i in indices)).digest());previous_sample[0]=sample
   if count>24000 and r[2]:dll.gaw_timing_reset();previous[0]=0;previous_sample[0]=0
  with contextlib.redirect_stdout(io.StringIO()):
   run(rom,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(ROWS),(region,len(checked),len(ROWS))
  data=b''.join(checked[n][0].to_bytes(4,'little')+checked[n][1] for n in range(len(ROWS)))
  (folder/f'{region}-results.bin').write_bytes(data)
  regions.append(dict(region=region,cases=len(checked),table_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'original2C63 costs and475 RAM bytes exact',flush=True)
 report=dict(source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=len(ROWS)*len(regions),regions=regions,compared_RAM_bytes_per_case=475,production_ROM_changed=False,full_game_ported=False,limits=[
  'Original2C63 and every callee unchanged. Custom boot supplies class/hero/gear/terrain neighborhood;original24E4 CALL used,24E7 patched RET as end marker. Read-only core snapshots RAM at entry/return;interrupts disabled in this isolated test.',
  'Classes0/1/2,all six old terrain states,17 selections,four directions;secondary0/3 plus11/255 boundary probes;all classifier tile pairs from both ROM tables;water/amulet and eight attribute combinations;gear/curse boundaries,64 sub-tile phases and36 edge coordinates. Independent dimensions are not a full Cartesian product.',
  'Checks instruction cost and475 affected/preserved RAM bytes,not rendered pixels,audio IRQ scheduling,source refresh RNG,whole load duration or natural full progression. Boundary gear states are explicitly synthetic.'])
 (ROOT/'analysis/hero_initialization_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
