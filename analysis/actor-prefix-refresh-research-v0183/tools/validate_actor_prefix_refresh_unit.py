"""All six actor lists/all256 masks: original stats/count M1/R and 768 bytes."""
import contextlib,ctypes as c,hashlib,io,json,struct
from actor_reference import ROOT
from actor_prefix_refresh_phase import actor_prefix_work
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from validate_full_actor_loading_cost import ROWS
from run_core import run

class Uninterrupted(GraphicsPrefixRefreshPhase):
 def boundary(self):pass

def main():
 rom=(ROOT/'input/original.sms').read_bytes();fixture=ROOT/'validation/full-actor-loading-cost/source.sms';image=fixture.read_bytes()
 assert image[0x1780:0x18e2]==rom[0x1780:0x18e2] and image[0x30000:0x34000]==rom[0x30000:0x34000]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_actorprefixrefresh_libretro.dll';dll=c.CDLL(str(core));dll.gaw_foreground_phase_samples.restype=c.c_uint
 for name in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_actor_load_context_events']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
 dll.gaw_timing_reset();previous=[0];starts={};checked=set();done=[];metadata=bytearray();folder=ROOT/'validation/actor-prefix-refresh-unit';folder.mkdir(exist_ok=True)
 def observe(f,r):
  if r[4]:done.append(f)
  count=dll.gaw_foreground_phase_samples();case=int.from_bytes(r[:2],'little')
  for i in range(previous[0],count):
   raw=c.string_at(c.addressof(dll.gaw_foreground_phase_events().contents)+i*800,800);pc,t=struct.unpack_from('<2Q',raw);meta=c.string_at(c.addressof(dll.gaw_foreground_m1_events().contents)+i*16,16);m1,refresh,_=struct.unpack('<Q2I',meta)
   if pc==0x1780:starts[case]=(raw,meta)
   elif pc==0x1853:
    first,mfirst=starts.pop(case);t0=struct.unpack_from('<Q',first,8)[0];m0,r0,_=struct.unpack('<Q2I',mfirst)
    #The fixture disables VINT. Supply a valid mode descriptor but suppress
    #IRQ boundaries explicitly; compare uninterrupted work/counts,not its phase.
    phase=list(struct.unpack_from('<12I',first,16));phase[6]|=0x20
    base=dict(phase=phase,ram=first[64:400],sound=first[400:800],refresh=r0,wall_master_cycles=0,foreground_tstates=0,IRQ_tstates=0,foreground_M1=0,IRQ_M1=0,events=[])
    result=actor_prefix_work(rom,base,*ROWS[case],cpu_class=Uninterrupted)['actor_points'][-1];p=result['prediction'];actual=c.string_at(c.addressof(dll.gaw_actor_load_context_events().contents)+i*769,769)
    assert p['wall_master_cycles']==t-t0 and p['foreground_M1']==m1-m0 and p['refresh']==refresh,(case,ROWS[case],'cost/M1/R')
    assert result['actors']==actual[:768] and result['active_count']==actual[768],(case,ROWS[case],'actor state/count')
    checked.add(case);metadata.extend(mfirst+meta)
  previous[0]=count
 with contextlib.redirect_stdout(io.StringIO()):run(fixture,70000,folder/'auto',set(),[],core=core,skip_intro=False,ram_observer=observe)
 assert done and len(checked)==len(ROWS);(folder/'m1.bin').write_bytes(metadata)
 report=dict(cases=len(checked),fixture_sha256=hashlib.sha256(image).hexdigest(),M1_sha256=hashlib.sha256(metadata).hexdigest(),production_ROM_changed=False,limits=['Six ordinary room lists/all256 persistence masks; original routine and list/stat bank unchanged. Synthetic caller disables IRQs;uninterrupted stats/count M1/R and768 actors checked. Boss suppression/graphics/later work not covered.'])
 (ROOT/'analysis/actor_prefix_refresh_unit_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checked),'actor-prefix masks M1/R/cost/768 bytes/count exact',flush=True)
if __name__=='__main__':main()
