"""Original F1/F2 termination with inactive restoration gate; state/cost/unwind."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_priority_effect_cost import priority_effect_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=[(request,priority,current,latch,tone,noise) for request,priority,current,latch,tone,noise in itertools.product([0,128]+list(range(0x90,0xad)),[0,1,127,255],[0x90,0x94,0xac],[0,1,127,128,255],[0,128,192],[0,128,192])]
 rom,folder=generate('priority',records,[9,0x10,0xe,0xf,0x130,0x160],0x81f8,'audio-priority-effect')
 image=rom.read_bytes()
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_tableenvelope_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_envelope_return_de.restype=c.c_uint;dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_envelope_did_unwind.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64
 dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little')
    predicted=priority_effect_cost(image,before);cost=dll.gaw_prefix_tstates()
    assert bool(dll.gaw_envelope_did_unwind())==False
    assert dll.gaw_envelope_return_de()==predicted['de'],(region,case,'DE',dll.gaw_envelope_return_de(),predicted['de'])
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records)
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'priority queue state/cost/DE exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original81F8/8211/80AD/81C6 and bank6 unchanged. Custom caller/400-byte patterned state,IRQs disabled;complete helper cost,state and returnedDE independently predicted.','Requests0/80/all29 valid effect IDs;priorities0/1/127/255;previous active90/94/AC;ownership0/1/127/128/255;DF30/DF60 inactive/active/active-withbit6. Synthetic combinations;invalid effect indices excluded.','PSG writes/waveforms,native equivalence,standalone8211 callers,whole reader and loading prediction remain unproven here.'])
 (ROOT/'analysis/audio_priority_effect_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
