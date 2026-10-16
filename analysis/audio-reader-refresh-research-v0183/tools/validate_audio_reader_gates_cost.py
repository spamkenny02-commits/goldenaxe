"""Original F1/F2 termination with inactive restoration gate; state/cost/unwind."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_reader_cost import reader_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=[(gate,enabled,phase,0x80 if gate==0 else 0x87) for gate,enabled,phase in itertools.product(range(256),[0,1,255],[0,1,4,5,6,254,255])]
 rom,folder=generate('gates',records,[0xa,3,4,5],0x8000,'audio-reader-gates',None,False,0xde3e)
 image=bytearray(rom.read_bytes());image[0x3430:0x3430+400]=bytes(400);image[0x3430+0x3e:0x3430+0x40]=(0x8a0b).to_bytes(2,'little');rom.write_bytes(image)
 assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
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
    predicted=reader_cost(image,before,de=0x8a0b);cost=dll.gaw_prefix_tstates()
    assert bool(dll.gaw_envelope_did_unwind())==False
    assert dll.gaw_envelope_return_de()==predicted['de'],(region,case,'DE',dll.gaw_envelope_return_de(),predicted['de'])
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records)
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'reader gate state/cost/DE exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original8000/allbank6 unchanged. Custom caller,zero seed apart from explicitDE8A0B,input gate/phase/command,IRQs disabled.400-byte state/full reader cost/returnedDE asserted.','All256 stall gate bytes,phase enable0/1/255,phase counters0/1/4/5/6/254/255. Channels inactive when reader proceeds,command80;stall paths start with87 to verify mute clears dispatch latch only for negative gates.','No complete command/channel combination coverage,PSG waveform/native/hardware or physical loading correction proof.'])
 (ROOT/'analysis/audio_reader_gates_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
