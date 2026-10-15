"""Original F3 ownership control and conditional sequence unwind."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_note_sequence_cost import note_sequence_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=[(address&255,address>>8,flags,tone,priority,borrowed) for address,flags,tone,priority,borrowed in itertools.product([0x3c00+i*8 for i in range(8)],[0,4,64,68,128,255],[128,160,192,224],[0,1,127,128,255],[0,128])]
 rom,folder=generate('ownership',records,[0x43,0x44,0x40,0x41,0xf,0x130],0x8357,'audio-note-sequence',0xde40,True)
 image=bytearray(rom.read_bytes());
 for i,value in enumerate([0,1,2,3,127,128,254,255]):image[0x3c00+i*8:0x3c08+i*8]=bytes([0xf3,value,0x91,7,0x81,7,0x81,7])
 rom.write_bytes(image)
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
    assert bool(dll.gaw_envelope_did_unwind())==predicted.get('unwind',False)
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,'RAM')
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records)
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'F3 state/cost/unwind exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original bank6 unchanged; synthetic F3 streams/custom two-level caller,IXDE40,IRQs disabled.400-byte state,complete helper cost and caller unwind.','Eight operand values0/1/2/3/127/128/254/255;channel types80/A0/C0/E0;flags0/4/64/68/128/255;priority0/1/127/128/255;borrowed tone active/inactive. Natural reachability and whole reader/load timing remain unproven.'])
 (ROOT/'analysis/audio_note_ownership_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
