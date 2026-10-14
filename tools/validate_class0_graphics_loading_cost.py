"""Execute original16D0 for six paid-exit destinations in both video regions."""
import contextlib,ctypes as c,hashlib,io,json
from actor_reference import ROOT
from class0_graphics_loading_cost import class0_graphics_cost
from run_core import run

ROWS=[(room,previous) for room in [0x1a,0x3c,0x36,0x87,0x6d,0x96]
      for previous in [0,14,255]]

def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000)
 code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
 label('case')
 emit('f3af3202c032acc03211c03a08c032ffff2a06c07e32b9c0237e3266c0cd d016 cd b924'.replace(' ',''))
 emit('3e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer')
 emit('2100803a08c03c3208c0');label('pointer')
 emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42')
 jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 image[0x80000:0x80000+len(ROWS)*32]=b''.join(bytes([r,p])+bytes(30) for r,p in ROWS)
 image[0x24b9]=0xc9
 folder=ROOT/'validation/class0-graphics-loading-cost';folder.mkdir(exist_ok=True)
 rom=folder/'source.sms';rom.write_bytes(image);return rom,folder

def main():
 rom,folder=generate();source=(ROOT/'input/original.sms').read_bytes()
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loader_libretro.dll'
 dll=c.CDLL(str(core));dll.gaw_timing_count.restype=c.c_uint
 dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
 model=class0_graphics_cost(source);rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];starts={};checked={};done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   case=int.from_bytes(r[:2],'little');count=dll.gaw_timing_count();events=dll.gaw_timing_events()
   for n in range(previous[0],count):
    e=[events[n*8+k] for k in range(8)]
    if e[0]==0x16d0:starts[case]=e
    elif e[0]==0x24b9:
     a=starts[case];observed=((e[1]-a[1])-(e[2]-a[2]))//15-17
     assert observed==model['foreground_tstates'],(region,case,ROWS[case],observed,model)
     checked[case]=dict(region=region,room=ROWS[case][0],previous_graphics_bank=ROWS[case][1],foreground_tstates=observed)
   previous[0]=count
  with contextlib.redirect_stdout(io.StringIO()):
   run(rom,1200,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(ROWS),(region,len(checked),len(ROWS))
  rows.extend(checked.values())
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=len(rows),model=model,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'Original16D0,032A,0C00,1A30,banked helpers and SRAM operations execute unchanged. Custom boot supplies ordinary class0 room,previous graphics bank,C0AC0 and display-off state.24B9 is patched RET only as the post-return marker; its17-T-state CALL is removed.',
  'Six paid-passage destinations,three distinct previous banks,PAL/NTSC reference core. Read-only timing excludes IRQ cycles. Other graphics classes,C0AC nonzero,already-loaded graphics and display-on entry are outside this model.',
  'Reference GX INI timing is retained. Physical hardware contention,190B/map/HUD callers,native elapsed work and complete transition cadence remain unverified.'])
 (ROOT/'analysis/class0_graphics_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(len(rows),'original16D0 world graphics costs exact',model['foreground_tstates'],flush=True)

if __name__=='__main__':main()
