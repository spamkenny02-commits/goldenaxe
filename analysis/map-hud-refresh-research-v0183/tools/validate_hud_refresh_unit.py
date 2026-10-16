"""Original HUD gauge fixture: M1 counts for varied gauges, gold and gem masks."""
import contextlib,ctypes as c,hashlib,io,json,struct
from actor_reference import ROOT
from validate_hud_loading_cost import ROWS
from map_hud_phase import hud
from graphics_prefix_refresh import audited_fetches
from source_rng_refresh import advance_refresh
from run_core import run

class Counter:
 def __init__(self,rom):self.rom=rom;self.foreground_tstates=0;self.M1=0
 def execute(self,ticks,effect=None):self.foreground_tstates+=ticks;self.M1+=audited_fetches(ticks,effect)

def main():
 source=(ROOT/'input/original.sms').read_bytes();fixture=ROOT/'validation/hud-loading-cost/source.sms';image=fixture.read_bytes()
 assert image[0x1e4e:0x1f78]==source[0x1e4e:0x1f78] and image[0xc00:0xc31]==source[0xc00:0xc31] and image[0x7357:0x7378]==source[0x7357:0x7378]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_waitrefresh_libretro.dll';dll=c.CDLL(str(core));dll.gaw_foreground_phase_samples.restype=c.c_uint
 for name in ['gaw_foreground_phase_events','gaw_foreground_m1_events']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
 folder=ROOT/'validation/hud-refresh-unit';folder.mkdir(exist_ok=True);rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];start={};checked=set();done=[];metadata=bytearray()
  def observe(f,r):
   if r[4]:done.append(f)
   count=dll.gaw_foreground_phase_samples();base=c.addressof(dll.gaw_foreground_phase_events().contents);mbase=c.addressof(dll.gaw_foreground_m1_events().contents);case=int.from_bytes(r[:2],'little')
   for i in range(previous[0],count):
    raw=c.string_at(base+i*800,800);pc,t=struct.unpack_from('<2Q',raw);meta=c.string_at(mbase+i*16,16);m1,refresh,_=struct.unpack('<Q2I',meta)
    if pc==0x1de5:start[case]=(t,m1,refresh,meta)
    elif pc==0x1de8:
     value=ROWS[case];context=bytes([*value[:5],*[128 if value[5]&(1<<n) else 0 for n in range(9)],0,0]);cpu=Counter(source);hud(cpu,context);t0,m0,r0,meta0=start.pop(case)
     assert (t-t0)//15==17+cpu.foreground_tstates and m1-m0==1+cpu.M1,(region,case,value,'cost/M1',m1-m0,cpu.M1)
     assert refresh==advance_refresh(r0,1+cpu.M1),(region,case,'R');checked.add(case);metadata.extend(meta0+meta)
   previous[0]=count
  with contextlib.redirect_stdout(io.StringIO()):run(fixture,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(ROWS);(folder/f'{region}-m1.bin').write_bytes(metadata);rows.append(dict(region=region,cases=len(checked),M1_sha256=hashlib.sha256(metadata).hexdigest()));print(region,len(checked),'HUD gauge M1/R/cost cases exact',flush=True)
 report=dict(cases=sum(r['cases'] for r in rows),rows=rows,fixture_sha256=hashlib.sha256(image).hexdigest(),production_ROM_changed=False,limits=['Existing HUD fixture, interrupts disabled. Gauges varied independently; not full Cartesian product. Hardware/full game unproved.'])
 (ROOT/'analysis/hud_refresh_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
