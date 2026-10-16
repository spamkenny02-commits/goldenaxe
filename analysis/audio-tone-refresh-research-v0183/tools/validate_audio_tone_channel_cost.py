"""Original864F held envelopes and noise notes/envelopes and F6/F7 sequence control costs."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_tone_channel_cost import tone_channel_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 streams=[bytes([note,duration,0x81]) for note,duration in itertools.product([0,1,127,128,129,159,191,223],[0,7,128,255])]
 records=[]
 for i,flags,scale,count,mode,env,release,transpose in itertools.product(range(len(streams)),[0,2,4,16,32,64,128],[0,1,255],[0,1,2],[0,1,128],[0,1,128],[0,1],[0,128]):
  if (i+flags+scale+count+mode+env+release+transpose)%7:continue
  address=0x3600+i*4;records.append((address&255,address>>8,flags,scale,count,mode,env,release,transpose,0x0b,0x8a))
 rom,folder=generate('tone-channel',records,[0x43,0x44,0x40,0x42,0x4a,0x46,0x47,0x4e,0x65,0x3e,0x3f],0x84c7,'audio-tone-channel',0xde40,True,0xde3e)
 image=bytearray(rom.read_bytes());image[0x3600:0x3600+len(streams)*4]=b''.join(s.ljust(4,b'\x81') for s in streams)
 image[0x3430+0x41]=0x80;image[0x3430+0x50:0x3430+0x52]=(0x8a0b).to_bytes(2,'little');image[0x3430+0x55]=0;image[0x3430+0x5f]=0;rom.write_bytes(image)
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
    predicted=tone_channel_cost(image,before,de=0x8a0b);cost=dll.gaw_prefix_tstates()
    assert bool(dll.gaw_envelope_did_unwind())==predicted['unwind']
    assert dll.gaw_envelope_return_de()==predicted['de'],(region,case,'DE',dll.gaw_envelope_return_de(),predicted['de'])
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records)
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'tone channel state/cost exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original84C7/allbank6 helpers/tables unchanged. Custom fixedROM streams/double caller,IXDE40,entryDE8A0B,IRQs disabled.400-byte state/complete channel costs.','Sampled deterministic product of notes/durations,flags,scales,counters,pitch0/1/128,envelope0/1/128,release0/1,transpose0/128;initial pitch/envelope indices0,explicit vibrato table8A0B. Modulo7 selection bounds fixture size;not natural reachability.','Other pitch/envelope modes,indices,channel types,command boundaries and whole reader/loading remain unproven by this isolated matrix.'])
 (ROOT/'analysis/audio_tone_channel_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
