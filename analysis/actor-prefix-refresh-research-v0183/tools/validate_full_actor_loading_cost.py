"""Read-only timing-core check of1780 model across six rooms/all256 masks."""
import contextlib,ctypes as c,hashlib,io,json
from actor_reference import ROOT
from full_actor_loading_cost import full_actor_cost
from run_core import run
ROWS=[(room,mask) for room in [0x1a,0x3c,0x36,0x87,0x6d,0x96] for mask in range(256)]
def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
 label('case');emit('af3202c03a08c032ffff2a06c07e32b9c06f26c2eb2a06c0237eeb773e013240c0cd80173e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 data=b''.join(bytes([r,m])+bytes(30) for r,m in ROWS);image[0x80000:0x80000+len(data)]=data
 folder=ROOT/'validation/full-actor-loading-cost';folder.mkdir(exist_ok=True);rom=folder/'source.sms';rom.write_bytes(image);return rom,folder
def main():
 rom,folder=generate();source=(ROOT/'input/original.sms').read_bytes();core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_timing_libretro.dll';dll=c.CDLL(str(core));dll.gaw_timing_reset();dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
 previous=[0];starts={};checked={};done=[]
 def observe(f,r):
  if r[4]:done.append(f)
  case=int.from_bytes(r[:2],'little');count=dll.gaw_timing_count();events=dll.gaw_timing_events()
  for n in range(previous[0],count):
   e=[events[n*8+k] for k in range(8)]
   if e[0]==0x1780:starts[case]=e
   elif e[0]==0x18e1:
    a=starts[case];observed=((e[1]-a[1])-(e[2]-a[2]))//15;model=full_actor_cost(source,*ROWS[case]);assert observed==model['foreground_tstates'],(case,ROWS[case],observed,model)
    checked[case]=dict(room=ROWS[case][0],mask=ROWS[case][1],foreground_tstates=observed)
  previous[0]=count
 with contextlib.redirect_stdout(io.StringIO()):run(rom,70000,folder/'sms',set(),[],core=core,skip_intro=False,ram_observer=observe)
 assert done and len(checked)==len(ROWS),(len(checked),len(ROWS));report=dict(source_sha256=hashlib.sha256(source).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=len(checked),all_six_destinations_all_256_persistence_masks_exact=True,rows=list(checked.values()),production_ROM_changed=False,full_game_ported=False,limits=['Actual1780/RLE/remap executes; custom source boot selects room/persistence only, no arithmetic/frontend routine replaced. Input banks32+ preserve original graphics/stats/bank12 lists. Read-only core observes instruction/cycle deltas and IRQ cost is subtracted.','Model assumes ordinary room/boss-defeat byte0; six ordinary destinations only. GX20-T-state INI behavior retained. VDP contention, initial background/map/HUD work, native elapsed work, IRQ scheduling and complete transition timing are not solved by this cost model.'])
 (ROOT/'analysis/full_actor_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'original1780 full loader costs exact')
if __name__=='__main__':main()
