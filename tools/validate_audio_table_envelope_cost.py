"""Unmodified table envelopes,exact returned A/DE and source stack unwinding."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_table_envelope_cost import table_envelope_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 read=lambda a:SOURCE[0x18000+a-0x8000]
 pointers=[read(0x897f+i*2)|(read(0x8980+i*2)<<8) for i in range(16)]+[0x8a52]
 records=[]
 for mode in range(1,17):
  for index,flags,tone,de in itertools.product(range(pointers[mode]-pointers[mode-1]),[0,4,16,20,128,255],[128,160,192,224],[0x8a0b,0x899e,0x89a1]):
   records.append((mode,index,flags,tone,de&255,de>>8))
 for index,flags in itertools.product(range(256),[0,4]):records.append((0,index,flags,128,11,138))
 rom,folder=generate('table',records,[0x47,0x5f,0x40,0x41,0x3e,0x3f],0x854b,'audio-envelope',0xde40,True,0xde3e)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_tableenvelope_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_prefix_samples','gaw_envelope_return_a','gaw_envelope_return_de','gaw_envelope_did_unwind']:getattr(dll,name).restype=c.c_uint
 dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];unwinds=[0]
  def observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
    case=int.from_bytes(r[:2],'little');de=int.from_bytes(before[0x3e:0x40],'little');predicted=table_envelope_cost(SOURCE,before,de=de)
    observed=(dll.gaw_prefix_tstates(),dll.gaw_envelope_return_a(),dll.gaw_envelope_return_de(),bool(dll.gaw_envelope_did_unwind()))
    assert observed==(predicted['tstates'],predicted['accumulator'],predicted['de'],predicted['unwind']),(region,case,records[case],observed,predicted)
    assert after==predicted['state'],(region,case,'RAM')
    checked[case]=observed[0].to_bytes(4,'little')+bytes([observed[1],observed[3]])+observed[2].to_bytes(2,'little')+hashlib.sha256(after).digest();previous[0]=sample;unwinds[0]+=observed[3]
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records))
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),caller_unwind_cases=unwinds[0],results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'table envelope costs/state/A/DE/unwind exact;',unwinds[0],'unwinds',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Original854B/8602/863E andallbank6 unchanged. Custom two-caller trampoline,IXDE40,IRQs disabled. All16 ROM table envelopes/every offset up to nexttable,six channel flags,four tone types andthree explicitDE inputs;zero mode separately.','Checks400 bytes,returnedA,DE,cost and source81/82 caller-frame unwinding. The83 stream command reads(++DE),not necessarily the adjacent table operand;explicit DE is an input,not a natural-game equivalence claim.','Invalid out-of-table indices and arbitrary RAM DE inputs excluded. Live table/envelope phase,PSG waveform and complete channel/futureIRQ/loading prediction remain open.'])
 (ROOT/'analysis/audio_table_envelope_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
