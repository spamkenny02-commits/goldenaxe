"""Original hero fixture: timing/M1/R and475 bytes across terrain/gear branches."""
import contextlib,ctypes as c,hashlib,io,json,struct
from actor_reference import ROOT
from hero_refresh_phase import predict_hero
from validate_hero_initialization_cost import ROWS
from validate_actor_prefix_refresh_unit import Uninterrupted
from run_core import run

def main():
 rom=(ROOT/'input/original.sms').read_bytes();fixture=ROOT/'validation/hero-initialization-cost/source.sms';image=fixture.read_bytes();assert image[0x2c63:0x2d9e]==rom[0x2c63:0x2d9e] and image[0x369f:0x371d]==rom[0x369f:0x371d]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_herorefresh_libretro.dll';dll=c.CDLL(str(core));dll.gaw_foreground_phase_samples.restype=c.c_uint
 for name in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_hero_entry','gaw_hero_return']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
 folder=ROOT/'validation/hero-refresh-unit';folder.mkdir(exist_ok=True);rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];starts={};checked=set();done=[];metadata=bytearray()
  def observe(f,r):
   if r[4]:done.append(f)
   count=dll.gaw_foreground_phase_samples();case=int.from_bytes(r[:2],'little')
   for i in range(previous[0],count):
    raw=c.string_at(c.addressof(dll.gaw_foreground_phase_events().contents)+i*800,800);pc,t=struct.unpack_from('<2Q',raw);meta=c.string_at(c.addressof(dll.gaw_foreground_m1_events().contents)+i*16,16);m1,refresh,_=struct.unpack('<Q2I',meta)
    if pc==0x2c63:starts[case]=(raw,meta)
    elif pc==0x24e7:
     first,mfirst=starts.pop(case);t0=struct.unpack_from('<Q',first,8)[0];m0,r0,_=struct.unpack('<Q2I',mfirst);before=c.string_at(dll.gaw_hero_entry(),8192);after=c.string_at(dll.gaw_hero_return(),8192)
     assert int.from_bytes(before[:2],'little')==case;phase=list(struct.unpack_from('<12I',first,16));phase[6]|=32
     points=predict_hero(rom,phase,before,first[400:800],r0,cpu_class=Uninterrupted);p=points[0x24e7]
     assert p['wall_master_cycles']==t-t0 and p['foreground_M1']==m1-m0 and p['refresh']==refresh,(region,case,ROWS[case],'cost/M1/R',p['foreground_M1'],m1-m0)
     indices=list(range(0x41,0x6c))+list(range(0x300,0x4b0));assert all(p['hero_ram'][n]==after[n] for n in indices),(region,case,'RAM')
     checked.add(case);metadata.extend(mfirst+meta)
   previous[0]=count
   if count>24000 and r[2]:dll.gaw_timing_reset();previous[0]=0
  with contextlib.redirect_stdout(io.StringIO()):run(fixture,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(ROWS);(folder/f'{region}-m1.bin').write_bytes(metadata);rows.append(dict(region=region,cases=len(checked),M1_sha256=hashlib.sha256(metadata).hexdigest()));print(region,len(checked),'hero terrain/gear M1/R/cost/475 bytes exact',flush=True)
 report=dict(cases=sum(r['cases'] for r in rows),rows=rows,fixture_sha256=hashlib.sha256(image).hexdigest(),production_ROM_changed=False,limits=['Existing independent-dimension hero fixture,IRQ disabled. Virtual phase used only for constructor bounds; no synthetic phase equivalence claimed. Actual original instructions/M1/R/cost and475 bytes checked. Full Cartesian product/hardware/full game unproved.'])
 (ROOT/'analysis/hero_refresh_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
