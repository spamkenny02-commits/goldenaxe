"""Unmodified8357 notes/rest/raw/tie costs against independent state model."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_note_sequence_cost import note_sequence_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 streams=[(bytes([0xe7]) if tie else b'')+bytes([note,second,duration]) for note,second,duration,tie in itertools.product([0,1,127,128,129,159,191,223],[0,1,127,128,255],[0,7,128,255],[False,True])]
 records=[]
 def row(i,flags,scale,transpose,env,old):
  address=0x3600+i*4;return (address&255,address>>8,flags,scale,transpose,env,old)
 for i,flags,scale,env in itertools.product(range(len(streams)),[0,4,8,12,64,72,128,136],[0,1,2,255],[0,128]):records.append(row(i,flags,scale,0,env,7))
 for i,flags,scale,transpose,env,old in itertools.product(range(len(streams)),[0,8],[0,2],[0,127,128,255],[0,128],[0,7,255]):records.append(row(i,flags,scale,transpose,env,old))
 records=[r+(0x30,0,0x5f,0x3c) for r in records]
 for address,flags,scale,transpose,env,old,counter in itertools.product([0x3c00,0x3c08,0x3c10,0x3c18,0x3c30,0x3c50],[0,4,8,12,64,72,128,136],[0,2],[0,128],[0,128],[0,255],[0,1,2,255]):
  records.append((address&255,address>>8,flags,scale,transpose,env,old,0x2e if address==0x3c50 else 0x30,counter,0x5f,0x3c))
 records=list(dict.fromkeys(records));assert len(records)<65536
 rom,folder=generate('notes',records,[0x43,0x44,0x40,0x42,0x45,0x47,0x4d,0x49,0x67,0x6e,0x6f],0x8357,'audio-note-sequence',0xde40)
 image=bytearray(rom.read_bytes());image[0x3600:0x3600+len(streams)*4]=b''.join(s.ljust(4,b'\x81') for s in streams)
 for n,count in enumerate([0,1,2,255]):image[0x3c00+n*8:0x3c08+n*8]=bytes([0xf7,0,count,0x20,0x3c,0x92,7,0x81])
 for address,data in [(0x3c20,[0x91,7,0x81]),(0x3c30,[0xf8,0x40,0x3c,0x91,7]),(0x3c40,[0x94,7,0x81]),(0x3c50,[0xf9]),(0x3c60,[0x93,7,0x81])]:image[address:address+len(data)]=bytes(data)
 rom.write_bytes(image)
 assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 fixture=bytes(image);core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefix_libretro.dll';dll=c.CDLL(str(core))
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
    predicted=note_sequence_cost(fixture,before);cost=dll.gaw_prefix_tstates()
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,records[case],'RAM',[(n,a,b) for n,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records))
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'original8357 ordinary note/rest/raw/tie costs and400 bytes exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(fixture).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Original8357/allbank6 callees/tables unchanged. Synthetic streams placed in fixed ROM3600/3C00,custom boot/caller,IXDE40,IRQs disabled.400-byte state and complete helper instruction cost predicted independently.','Duration-only,note,rest,raw16bit,E7 tie,F7 counted loops,F8 calls,F9 returns;explicit/omitted durations,scale0/1/2/255,transpose sign/wrap,table/ADSR envelope reset,borrowed-channel flags,loop counts0/1/2/255 and initialized channel return stack. Many boundaries are synthetic.','This fixture covers E7/F7/F8/F9 controls; F1/F2 termination has a separate fixture. Other sequencer commands remain unsupported. Noise864F,PSG waveforms/full reader/futureIRQ/loading prediction remain open.'])
 (ROOT/'analysis/audio_note_sequence_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
