"""Execute unmodified8097 across priorities,request ordering and boundaries."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_arbitration_cost import arbitration_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=[]
 for slot,value,priority in itertools.product(range(3),range(256),[0,1,15,127,128,255]):
  r=[0,0,0,priority,0x80];r[slot]=value;records.append(tuple(r))
 for music,effect1,effect2,priority in itertools.product(list(range(0x81,0x8e))+[0xb0],range(0x90,0xad),range(0x90,0xad),[0,1]):records.append((music,effect1,effect2,priority,0x80))
 records=list(dict.fromkeys(records));assert len(records)<65536
 rom,folder=generate('arbitration',records,[6,7,8,0x11,5],0x8097,'audio-arbitration')
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefix_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64
 dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[];branches={}
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
    case=int.from_bytes(r[:2],'little');predicted=arbitration_cost(SOURCE,before);cost=dll.gaw_prefix_tstates()
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted)
    assert after==predicted['state'],(region,case,'RAM')
    for decision in predicted['decisions']:branches[decision]=branches.get(decision,0)+1
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records))
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'original8097 costs and400 RAM bytes exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,branch_comparisons=branches,production_ROM_changed=False,full_game_ported=False,limits=['Unmodified original bank6 arbitration8097 and priority table8AD5. Custom boot/3000 caller supplies400-byte patterned state andfive request/priority fields;IRQs disabled. All400 RAM bytes and complete helper instruction cost independently predicted.','Every byte request in each ofthree slots,six prior priority values;all14 music/B0 x29 effects x29 effects xpriority0/1 combinations. Invalid high request/priority boundaries are synthetic.','Does not establish complete reader/dispatch/channel cost,live arbitration phase,PSG waveforms or physical loading prediction.'])
 (ROOT/'analysis/audio_arbitration_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
