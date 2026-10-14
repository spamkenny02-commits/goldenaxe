"""Execute unchanged854B ADSR through attack/decay/sustain/release boundaries."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_adsr_cost import adsr_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 records=[];steps=[0,1,15,16,127,128,254,255];bounds=[0,1,15,16,127,128,254,255]
 for value,step,phase,flags in itertools.product(range(256),steps,[0,8,16,24,32,40,64,72],[0,4]):records.append((128,flags,128,phase,value,step,step,127,step,step))
 for value,step,phase,limit,flags in itertools.product(bounds,steps,[32,40],bounds,[0,4]):records.append((128,flags,128,phase,value,step,step,limit,step,step))
 for phase,value,step,flags,tone in itertools.product([0,8,16,32,64,112,255],bounds,steps,[0,4],[128,160,192,224]):records.append((255,flags,tone,phase,value,step,step,255,step,step))
 for phase,value in itertools.product(range(256),bounds):records.append((0,4,128,phase,value,0,0,0,0,0))
 records=list(dict.fromkeys(records));assert len(records)<65536
 rom,folder=generate('adsr',records,[0x47,0x40,0x41,0x5d,0x5f,0x60,0x61,0x62,0x63,0x64],0x854b,'audio-envelope',0xde40)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_envelope_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_envelope_return_a.restype=c.c_uint
 dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
    case=int.from_bytes(r[:2],'little');predicted=adsr_cost(before);cost=dll.gaw_prefix_tstates();a=dll.gaw_envelope_return_a()
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'] and a==predicted['accumulator'],(region,case,records[case],'state/A',a,predicted['accumulator'])
    checked[case]=cost.to_bytes(4,'little')+bytes([a])+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records))
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'original854B ADSR costs,400 RAM bytes and returned A exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Unchanged original854B and ADSR termination863E,all bank6 bytes preserved. Custom boot/3000 caller,IXDE40,IRQs disabled. Complete400-byte state,returned A and helper cost predicted independently.','All256 values,eight step boundaries,phase and bounce flags,decay limit boundaries,muted/unmuted channel termination,four PSG tone types,zero envelope and synthetic multi-phase/high-bit flags. Dimensions are not a full Cartesian product.','Only zero/ADSR modes:table envelopes with stack unwinding are excluded. Live ADSR/PSG waveforms,complete channel processing and physical IRQ/loading prediction remain open.'])
 (ROOT/'analysis/audio_adsr_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
