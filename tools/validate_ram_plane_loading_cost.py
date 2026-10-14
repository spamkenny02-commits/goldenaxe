"""Read-only timing-core check of1780 model across six rooms/all256 masks."""
import contextlib,ctypes as c,hashlib,io,json
from actor_reference import ROOT
from ram_plane_loading_cost import ram_plane_cost
from actor_loading_cost import rle_cost
from run_core import run
ORIGINAL=(ROOT/'input/original.sms').read_bytes();ASSETS=[]
for room in [0x1a,0x3c,0x36,0x87,0x6d,0x96]:
 bank=8+(room>>7);p=int.from_bytes(ORIGINAL[bank*0x4000+(room*2&255):bank*0x4000+(room*2&255)+2],'little');ASSETS.append((bank,p,0xdc00,1))
meta=rle_cost(ORIGINAL,0x3c010,0x4000)['source_end'];ASSETS += [(15,0x8000+(meta&0x3fff),0xc900,2),(11,0xb402,0xd100,4),(4,0xa6ab,0xdb00,2)]
ROWS=[(bank,pc,(dst&0xff00)+low,planes) for bank,pc,dst,planes in ASSETS for low in range(256)]
def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
 label('case');emit('af3202c03a08c032ffffdd2a06c0')
 for i in range(6):emit(f'dd7e{i:02x}32{0x80+i:02x}c0')
 emit('3a80c032ffff2a81c0ed5b83c03a85c04fcd000ccd1f1e3e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0');label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 data=b''.join(bytes([bank])+pc.to_bytes(2,'little')+dst.to_bytes(2,'little')+bytes([planes])+bytes(26) for bank,pc,dst,planes in ROWS);image[0x80000:0x80000+len(data)]=data
 image[0x1e1f]=0xc9
 folder=ROOT/'validation/ram-plane-loading-cost';folder.mkdir(exist_ok=True);rom=folder/'source.sms';rom.write_bytes(image);return rom,folder
def main():
 rom,folder=generate();source=(ROOT/'input/original.sms').read_bytes();core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loader_libretro.dll';dll=c.CDLL(str(core));dll.gaw_timing_reset();dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
 previous=[0];starts={};checked={};done=[]
 def observe(f,r):
  if r[4]:done.append(f)
  case=int.from_bytes(r[:2],'little');count=dll.gaw_timing_count();events=dll.gaw_timing_events()
  for n in range(previous[0],count):
   e=[events[n*8+k] for k in range(8)]
   if e[0]==0xc00:starts[case]=e
   elif e[0]==0x1e1f:
    a=starts[case];observed=((e[1]-a[1])-(e[2]-a[2]))//15-17;bank,pc,dst,planes=ROWS[case];model=ram_plane_cost(source,bank*0x4000+(pc&0x3fff),dst,planes);assert observed==model['tstates'],(case,ROWS[case],observed,model)
    checked[case]=dict(bank=bank,pc=pc,destination=dst,planes=planes,foreground_tstates=observed)
  previous[0]=count
 with contextlib.redirect_stdout(io.StringIO()):run(rom,20000,folder/'sms',set(),[],core=core,skip_intro=False,ram_observer=observe)
 assert done and len(checked)==len(ROWS),(len(checked),len(ROWS));report=dict(source_sha256=hashlib.sha256(source).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=len(checked),nine_original_streams_all_256_destination_low_bytes_exact=True,rows=list(checked.values()),production_ROM_changed=False,full_game_ported=False,limits=['Original0C00 unchanged. Custom boot supplies bank/source/destination/plane count and calls1E1F as a read-only end marker (RET patched there);17-T-state caller CALL removed from measurement. No decoder operation is replaced.', 'Nine streams: six destination maps,world metatiles,world terrain data and HUD. All256 low-byte destinations exercise carry branches and literal/repeated commands. Does not model callers, whole loader, waiting/IRQ/native work or physical VDP timing.'])
 (ROOT/'analysis/ram_plane_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'original0C00 costs exact')
if __name__=='__main__':main()
