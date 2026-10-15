"""Original864F held envelopes and noise notes/envelopes and F6/F7 sequence control costs."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_noise_channel_cost import noise_channel_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 streams=[bytes([note,duration,0x81]) for note,duration in itertools.product([0,1,127,128,129,130,132,136,144,160,191,192,223],[0,1,127,128,255])]
 records=[]
 for i,flags,scale,count,mode,index in itertools.product(range(len(streams)),[0,2,4,16,64,128],[0,1,2,255],[0,1,2,255],[0,1,128],[0]):
  address=0x3600+i*4;records.append((address&255,address>>8,flags,scale,count,mode,index,0x0b,0x8a))
 records=[r+(0,) for r in records]
 for address,flags,scale,counter,mode in itertools.product([0x3c00,0x3c08,0x3c10,0x3c18,0x3c28],[0,2,4,16,64,128],[0,1,2,255],[0,1,2,255],[0,128]):
  records.append((address&255,address>>8,flags,scale,1,mode,0,0x0b,0x8a,counter))
 rom,folder=generate('noise-channel',records,[0xd3,0xd4,0xd0,0xd2,0xda,0xd7,0xef,0x3e,0x3f,0xf7],0x864f,'audio-noise-channel',0xded0,True,0xde3e)
 image=bytearray(rom.read_bytes());image[0x3600:0x3600+len(streams)*4]=b''.join(s.ljust(4,b'\x81') for s in streams);image[0x3430+0xd1]=0xe0;
 for n,count in enumerate([0,1,2,255]):image[0x3c00+n*8:0x3c08+n*8]=bytes([0xf7,0,count,0x20,0x3c,0x82,7,0x81])
 image[0x3c20:0x3c23]=bytes([0x81,7,0x81]);image[0x3c28:0x3c2b]=bytes([0xf6,0x20,0x3c]);rom.write_bytes(image)
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
    predicted=noise_channel_cost(image,before,de=0x8a0b);cost=dll.gaw_prefix_tstates()
    assert bool(dll.gaw_envelope_did_unwind())==predicted['unwind']
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records)
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'noise channel state/cost exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original864F and all bank6 helpers/tables unchanged. Custom caller/fixedROM streams,IXDED0,explicit DE8A0B,IRQs disabled. Complete channel instruction cost and400 RAM bytes compared.','Thirteen note bytes,five following durations,six flags,four scales,four duration counters,three envelope modes andzero initial envelope index. Non-boundary held notes execute854B and volume tail. Duration-only and new-noise notes execute common839B/83A4 reset. F6 jumps,F7 counts0/1/2/255 and prior counters0/1/2/255 tested separately. Many contexts synthetic.','Only F6/F7 noise sequence controls supported;other commands explicitly unsupported. Other envelope modes/indices,whole reader/futureIRQ/loading and natural progression unproved.'])
 (ROOT/'analysis/audio_noise_channel_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
