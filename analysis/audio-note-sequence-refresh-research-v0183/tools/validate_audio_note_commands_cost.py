"""Original deterministic sequencer controls through8357, complete state/cost."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_note_sequence_cost import note_sequence_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

COMMANDS=[0xe0,0xe1,0xe2,0xe4,0xe5,0xe6,0xe8,0xe9,0xea,0xeb,0xed,0xee,0xf0,0xf4,0xf5,0xf6,0xfa,0xfb,0xfc,0xfd]
def main():
 streams=[]
 for command,value in itertools.product(COMMANDS,[0,1,7,127,128,255]):
  operands=bytes([value,7,2,255,128])
  size=5 if command in [0xe0,0xe9] else 4 if command==0xf0 else 2 if command in [0xea,0xf6] else 1
  if command==0xf6:operands=bytes([0x00,0x3e])
  streams.append(bytes([command])+operands[:size]+bytes([0x91,7,0x81,7]))
 records=[]
 for index,flags,tone,scale,gate,stereo in itertools.product(range(len(streams)),[0,4,64,128],[128,160,192,224],[0,1,2,255],[0,1],[0,255]):
  if streams[index][0]==0xe2 and stereo:continue
  address=0x3600+index*12;records.append((address&255,address>>8,flags,tone,scale,gate,stereo,0))
 rom,folder=generate('commands',records,[0x43,0x44,0x40,0x41,0x42,0xb,0x12,0x66],0x8357,'audio-note-commands',0xde40)
 image=bytearray(rom.read_bytes());image[0x3600:0x3600+len(streams)*12]=b''.join(s.ljust(12,b'\x81') for s in streams);image[0x3e00:0x3e04]=bytes([0x91,7,0x81,7]);rom.write_bytes(image)
 assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefix_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
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
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,records[case],'RAM',[(n,a,b) for n,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records),max(checked,default=-1),done[-1:] )
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'deterministic commands state/cost exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),commands=[f'{n:02X}' for n in COMMANDS],cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original8357 and bank6 unchanged,custom fixedROM streams/two-caller-free boot,IXDE40,IRQs disabled.400-byte state/full instruction cost.','Six operand values0/1/7/127/128/255,four channel types,four flags,four scales,two fade gates,two stereo latches except E2: previous stereo byte and latch zero, preserving SMS cartridge/RAM mapping on mirrored port06. F6 target fixed3E00,EA two-byte arguments,F0 four-byte arguments,E0/E9 five-byte ADSR. Some boundaries are synthetic.','R-register-dependent commands E3/EC/FE/FF,F3 ownership has a separate fixture,EF invalid table-code target,restoration8211,noise/whole channel/reader/loading remain open.'])
 (ROOT/'analysis/audio_note_commands_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
