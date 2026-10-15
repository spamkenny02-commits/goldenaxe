"""Original F1/F2 termination with inactive restoration gate; state/cost/unwind."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_note_sequence_cost import note_sequence_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=[(address&255,address>>8,flags,tone,borrowed,noise,0) for address,flags,tone,borrowed,noise in itertools.product([0x3c00,0x3c08],[0,4,64,68,128,255],[128,160,192,224],[0,128],[0,128])]
 rom,folder=generate('termination',records,[0x43,0x44,0x40,0x41,0x160,0x130,0x0e],0x8357,'audio-note-sequence',0xde40,True)
 image=bytearray(rom.read_bytes());image[0x3c00]=0xf1;image[0x3c08]=0xf2;rom.write_bytes(image)
 assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_tableenvelope_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_envelope_did_unwind.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64
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
    predicted=note_sequence_cost(image,before);cost=dll.gaw_prefix_tstates()
    assert bool(dll.gaw_envelope_did_unwind())==predicted['unwind']
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,'RAM')
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records)
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'F1/F2 state/cost/unwind exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original bank6 unchanged; synthetic F1/F2 streams/custom two-level caller,IXDE40,IRQs disabled. All400 RAM bytes,complete helper cost and caller unwind asserted.','Channel types80/A0/C0/E0,own flags0/4/64/68/128/255,borrowed tone/noise flags0/128. DE0E=0 only; nonzero restoration8211 explicitly unsupported. No full reader/loading or natural progression claim.'])
 (ROOT/'analysis/audio_note_termination_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
