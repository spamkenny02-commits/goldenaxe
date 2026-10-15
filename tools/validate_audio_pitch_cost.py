"""Execute unchanged82C5 across delay/counter/sign/wrap/table control paths."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_pitch_cost import pitch_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=[]
 def row(mode,base,delta,delay,rate,step,phase,flags=0):return (mode,base&255,base>>8,delta&255,delta>>8,delay,rate,step,phase,0xc0,0x8a,flags)
 for mode,base,delta,delay,rate,step,phase in itertools.product([128,255],[0,1,255,256,1023,32767,32768,65535],[0,1,255,256,32767,32768,65535],[0,1,2,255],[0,1,2,255],[128,129,255,0,1,127],[0,1,2,255]):records.append(row(mode,base,delta,delay,rate,step,phase))
 for mode,index,base,flags in itertools.product(range(1,9),range(256),[0x8ab8,0x8a61],[0,4,32,255]):records.append(row(mode,base,0,1,index,0,1,flags))
 for base in [0,1,255,256,1023,32767,32768,65535]:records.append(row(0,base,65535,0,0,128,0))
 records=list(dict.fromkeys(records));assert len(records)<65536
 rom,folder=generate('pitch',records,[0x46,0x4b,0x4c,0x52,0x53,0x54,0x55,0x56,0x57,0x50,0x51,0x40],0x82c5,'audio-pitch',0xde40,True)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_pitch_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_pitch_return_hl.restype=c.c_uint;dll.gaw_envelope_did_unwind.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64
 dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];unwinds=[0]
  def observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
    case=int.from_bytes(r[:2],'little');predicted=pitch_cost(SOURCE,before,return_address=0x3003)
    observed=(dll.gaw_prefix_tstates(),dll.gaw_pitch_return_hl(),bool(dll.gaw_envelope_did_unwind()))
    assert observed==(predicted['tstates'],predicted['hl'],predicted['unwind']),(region,case,records[case],observed,predicted)
    assert after==predicted['state'],(region,case,'RAM')
    checked[case]=observed[0].to_bytes(4,'little')+observed[1].to_bytes(2,'little')+bytes([observed[2]])+hashlib.sha256(after).digest();previous[0]=sample;unwinds[0]+=observed[2]
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records))
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),caller_unwind_cases=unwinds[0],results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'original82C5 cost/state/HL/unwind exact;',unwinds[0],'unwinds',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Original82C5/allbank6 unchanged;custom two-level caller,IXDE40,IRQs disabled. Compares400-byte state,returnedHL and cost against independent model. Unwind81/82 is modeled but not encountered in the original table/index ranges used here;it is not validated by a zero unwind count.','Vibrato:two high-bit modes,eight base boundaries,seven signed delta boundaries,four delay/rate/phase counters,six signed step boundaries. Tables:all8 modes/all256 indices,two explicit ROM-reading base values,four channel flag patterns. Many table indices/base/counter bounds are synthetic.','Does not establish live pitch,PSG waveforms,complete channel/sequencer cost,native futureIRQ/load scheduling or natural progression.'])
 (ROOT/'analysis/audio_pitch_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
