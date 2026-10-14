"""Check original190B with all saved flag bytes in six paid-exit destinations."""
import contextlib,ctypes as c,hashlib,io,json
from actor_reference import ROOT
from world_map_loading_cost import world_map_cost,ROOMS
from run_core import run

ROWS=[(room,flags) for room in ROOMS for flags in range(256)]

def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000)
 code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c03e01324dc0')
 label('case');emit('af3202c03a08c032ffff2a06c07e32b9c06f26c1eb2a06c0237eeb772100dd2234c0cdb9243e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011200019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0')
 label('pointer');emit('2206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42')
 jp('c2','case');emit('af3202c03e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 data=b''.join(bytes([room,flags])+bytes(30) for room,flags in ROWS)
 image[0x80000:0x80000+len(data)]=data;image[0x24bc]=0xc9
 folder=ROOT/'validation/world-map-loading-cost';folder.mkdir(exist_ok=True)
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
    if e[0]==0x24b9:starts[case]=e
    elif e[0]==0x24bc:
     a=starts[case];observed=((e[1]-a[1])-(e[2]-a[2]))//15-17
     model=world_map_cost(source,*ROWS[case]);assert observed==model['foreground_tstates'],(region,case,ROWS[case],observed,model)
     checked[case]=dict(room=ROWS[case][0],flags=ROWS[case][1],foreground_tstates=observed)
   previous[0]=count
   if count>24000 and r[2]:dll.gaw_timing_reset();previous[0]=0
  with contextlib.redirect_stdout(io.StringIO()):
   run(rom,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(ROWS),(region,len(checked),len(ROWS))
  rows.append(dict(region=region,cases=len(checked),rows=list(checked.values())))
  print(region,len(checked),'original190B world map costs exact',flush=True)
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),regions=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'Original190B,175F,0C00,1976,1951,1A7C,1B0E,1A02 and1A30 execute unchanged. Custom boot selects room/flags,C04D1 and valid queue pointer,with C0AC0/C0410 and class0.24BC patched RET as end marker;17-T-state CALL190B removed.',
  'All256 saved room flags in all six paid-exit destinations,both regions. Tests cover actual metadata lookup/missing default,visited transform and secondary cell branch. Metatile source initialized zero; decoded map bytes are original. Does not verify their rendered output.',
  'Other destinations/classes,C0AC nonzero,bridge C0415,whole HUD/VDP wait,native elapsed work,clock freeze and complete transition fidelity are outside this validator.'])
 (ROOT/'analysis/world_map_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
