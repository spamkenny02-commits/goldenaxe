"""Execute original HUD preparation with variable health,magic,gold and gems."""
import contextlib,ctypes as c,hashlib,io,json
from actor_reference import ROOT
from hud_loading_cost import hud_cost
from run_core import run

BASE=(24,24,24,24,10,0)
ROWS=[]
for maximum in range(8,129,8):
 for value in range(256):
  ROWS.extend([(value,maximum,24,24,10,0),(24,24,value,maximum,10,0)])
for maximum in [0,7,129,255]:
 for value in [0,1,7,8,127,128,254,255]:
  ROWS.extend([(value,maximum,24,24,10,0),(24,24,value,maximum,10,0)])
ROWS.extend((24,24,24,24,gold,0) for gold in range(256))
ROWS.extend((24,24,24,24,10,gems) for gems in range(512))
ROWS=list(dict.fromkeys(ROWS))

def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000)
 code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
 label('case');emit('af3202c03a08c032ffffdd2a06c0')
 for i,address in enumerate([0xc318,0xc0da,0xc0db,0xc0dc,0xc0dd]+list(range(0xc0cf,0xc0d8))):
  emit(f'dd7e{i:02x}32'+address.to_bytes(2,'little').hex())
 emit('cde51d3e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0')
 label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42')
 jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 data=b''.join(bytes([*r[:5],*[128 if r[5]&(1<<n) else 0 for n in range(9)]])+bytes(18) for r in ROWS)
 image[0x80000:0x80000+len(data)]=data;image[0x1de8]=0xc9
 folder=ROOT/'validation/hud-loading-cost';folder.mkdir(exist_ok=True)
 rom=folder/'source.sms';rom.write_bytes(image);return rom,folder

def main():
 rom,folder=generate();source=(ROOT/'input/original.sms').read_bytes()
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loader_libretro.dll'
 dll=c.CDLL(str(core));dll.gaw_timing_count.restype=c.c_uint
 dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];starts={};checked={};done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   case=int.from_bytes(r[:2],'little');count=dll.gaw_timing_count();events=dll.gaw_timing_events()
   for n in range(previous[0],count):
    e=[events[n*8+k] for k in range(8)]
    if e[0]==0x1de5:starts[case]=e
    elif e[0]==0x1de8:
     a=starts[case];observed=((e[1]-a[1])-(e[2]-a[2]))//15-17
     model=hud_cost(source,*ROWS[case]);assert observed==model['foreground_tstates'],(region,case,ROWS[case],observed,model)
     checked[case]=dict(inputs=ROWS[case],foreground_tstates=observed)
   previous[0]=count
   # Read-only observation buffers are finite; reset only after consuming events.
   if count>24000 and r[2]:dll.gaw_timing_reset();previous[0]=0
  with contextlib.redirect_stdout(io.StringIO()):
   run(rom,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(ROWS),(region,len(checked),len(ROWS))
  rows.append(dict(region=region,cases=len(checked),rows=list(checked.values())))
  print(region,len(checked),'original1E4E HUD costs exact',flush=True)
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),regions=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'Original1E4E and all its decoder/icon/gauge routines execute unchanged. Custom boot supplies input bytes and invokes original1DE5 CALL1E4E.1DE8 is patched RET only as a post-call marker;17-T-state CALL is removed.',
  'Both regions: all256 health/magic values for each valid capacity8..128 step8; boundary values for capacity0,7,129,255; all256 gold values; all512 gem masks. Dimensions varied independently around baseline24/24/24/24/gold10/no gems; not their full Cartesian product.',
  'Capacity0 demonstrates original DJNZ0->256 iteration behavior. Timing hook is read-only and excludes IRQ work. Does not model map caller,VDP transfer,palette restoration,busy waits,native elapsed work or complete transition equivalence.'])
 (ROOT/'analysis/hud_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
