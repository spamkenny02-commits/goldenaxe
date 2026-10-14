"""Execute original0397 across count/chunk boundaries and verify live1FA7 prefix."""
import contextlib,ctypes as c,hashlib,io,json
from actor_reference import ROOT
from reveal_loading_cost import word_fill_cost,reveal_prefix_cost
from run_core import run

COUNTS=list(range(1025))+[2047,2048,4095,4096,32767,32768,65535]

def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000)
 code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
 label('case');emit('af3202c03a08c032ffff2a06c04e234621ff18110078cde51d3e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0')
 label('pointer');emit('2206c02a00c0232200c001'+len(COUNTS).to_bytes(2,'little').hex()+'b7ed42')
 jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 data=b''.join(n.to_bytes(2,'little')+bytes(30) for n in COUNTS)
 image[0x80000:0x80000+len(data)]=data
 image[0x1de5:0x1de8]=bytes.fromhex('cd9703');image[0x1de8]=0xc9
 folder=ROOT/'validation/reveal-loading-cost';folder.mkdir(exist_ok=True)
 rom=folder/'source.sms';rom.write_bytes(image);return rom,folder

def main():
 rom,folder=generate();source=(ROOT/'input/original.sms').read_bytes()
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loader_libretro.dll'
 dll=c.CDLL(str(core));dll.gaw_timing_count.restype=c.c_uint
 dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);regions=[]
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
     model=word_fill_cost(COUNTS[case]);assert observed==model['foreground_tstates'],(region,case,COUNTS[case],observed,model)
     checked[case]=dict(BC=COUNTS[case],foreground_tstates=observed)
   previous[0]=count
  with contextlib.redirect_stdout(io.StringIO()):
   run(rom,len(COUNTS)*8+2500,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(COUNTS),(region,len(checked),len(COUNTS))
  events=json.loads((ROOT/f'validation/paid-passage-loader/{region}-cycle-events.json').read_text())
  a=next(e for e in events if e[1]==0x1fa7 and e[4]==0x96)
  b=next(e for e in events if e[1]==0xaa4 and e[2]>a[2])
  live=((b[2]-a[2])-(b[3]-a[3]))//15
  assert live==reveal_prefix_cost()['foreground_tstates'],(region,live)
  regions.append(dict(region=region,cases=len(checked),rows=list(checked.values()),live_reveal_prefix_tstates=live))
  print(region,len(checked),'original0397 costs and live1FA7 prefix exact',flush=True)
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in regions),regions=regions,production_ROM_changed=False,full_game_ported=False,limits=[
  'Original0397 and RST28 unchanged. Custom boot supplies HL18FF,DE7800,BC count.1DE5 is changed to CALL0397 and1DE8 RET as timing markers;17-T-state CALL removed. All counts0..1024 plus2047,2048,4095,4096,32767,32768,65535 in both regions.',
  'Read-only timing excludes IRQ work. Live unpatched6D->96 reveal prefix independently matches51628T in PAL/NTSC. It spans two/one observed frame boundaries respectively,so instruction work is not a constant frame delay.',
  'No assertion of physical hardware contention,VDP pixels,initial fade waits,contour cadence,whole loader or native equivalence.'])
 (ROOT/'analysis/reveal_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
