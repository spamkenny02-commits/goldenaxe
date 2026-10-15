"""Original wait with synthetic caller phases,IFF/latched IRQ and EI boundary contexts."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct,collections,sys
from actor_reference import ROOT
from validate_audio_prefix_cost import generate,SOURCE
from wait_raster_prediction import predict_save_wait
from run_core import run

def main():
 extra='--pal-latched' in sys.argv
 delays=sorted(set([0,1,127,511,1023,2047]+list(range(1800,2201,7))))
 if extra:delays=list(range(2400,2701,7))
 records=[(delay&255,delay>>8,mode,palette,comp,timer) for delay,mode,palette,comp,timer in itertools.product(delays,[0,1,2],[0,1],[0,1],[0,1,255])]
 rom,folder=generate('wait',records,list(range(0x20,0x26)),0x3040,'wait-raster-unit-pal' if extra else 'wait-raster-unit')
 image=bytearray(rom.read_bytes());image[0x3430:0x3430+400]=bytes(400);image[0xb94]=0xfb
 stub=bytearray();labels={};fix=[]
 def emit(h):stub.extend(bytes.fromhex(h))
 def label(name):labels[name]=0x3040+len(stub)
 def jump(op,name):emit(op);fix.append((len(stub),name));emit('0000')
 emit('f32100dd2234c0af773a23de3233c03a24de3203de3a25de3230c03e803205de3ea0d3bf3e81d3bfdbbfed4b20de78b128050b78b120fb3a22deb7')
 jump('ca','disabled');emit('fe01');jump('ca','enabled');emit('cd940b');jump('c3','finish')
 label('enabled');emit('fb00cd950b');jump('c3','finish')
 label('disabled');emit('cd950b')
 label('finish');emit('f33e80d3bf3e81d3bfc9')
 for p,name in fix:stub[p:p+2]=labels[name].to_bytes(2,'little')
 assert 0x3040+len(stub)<0x3100;image[0x3040:0x3040+len(stub)]=stub;rom.write_bytes(image)
 assert image[0xb95:0xbc6]==SOURCE[0xb95:0xbc6] and image[0x10000:0x14000]==SOURCE[0x10000:0x14000] and image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_waitraster_libretro.dll';dll=c.CDLL(str(core));dll.gaw_wait_samples.restype=c.c_uint;dll.gaw_wait_events.restype=c.POINTER(c.c_uint64);dll.gaw_wait_entry_events.restype=c.POINTER(c.c_uint8);dll.gaw_audio_irq_count.restype=c.c_uint;dll.gaw_audio_irq_events.restype=c.POINTER(c.c_uint64)
 rows=[]
 for region in (['pal'] if extra else ['auto','pal']):
  dll.gaw_timing_reset();previous=[0];checked={};done=[];observed=bytearray();entries=bytearray();contexts=collections.Counter();kinds=collections.Counter();irq_evidence=[]
  def observe(f,r):
   if r[4]:done.append(f)
   count=dll.gaw_wait_samples()
   if count!=previous[0]:
    assert count==previous[0]+1;case=int.from_bytes(r[:2],'little');raw=c.string_at(dll.gaw_wait_events(),count*112)[-112:];entry=c.string_at(dll.gaw_wait_entry_events(),count*784)[-784:];w=struct.unpack('<14Q',raw);phase=struct.unpack_from('<12I',entry)
    model=predict_save_wait(SOURCE,phase,entry[48:384],entry[384:784])
    assert (model['taken'],model['exits'])==w[4:6],(region,case,records[case],'loop',model,w,phase)
    assert model['wall_master_cycles']==w[2]-w[0] and model['IRQ_tstates']*15==w[3]-w[1],(region,case,records[case],'wall',model,w,phase)
    assert model['gate']==w[7] and model['clock']==w[9]
    events=dll.gaw_audio_irq_events();actual=[]
    for j in range(dll.gaw_audio_irq_count()-1,-1,-1):
     timestamp=events[j*14+1]
     if timestamp<=w[0]:break
     if timestamp<w[2] and events[j*14]==0x137:actual.append((timestamp-w[0],bool(events[j*14+4])))
    actual.reverse();assert actual==[(i['entry_offset_master'],i['kind']=='full') for i in model['events']],(region,case,'IRQ acceptance',actual,model['events'])
    irq_evidence.append(dict(case=case,observed_entries=actual))
    checked[case]=True;observed.extend(raw);entries.extend(entry);contexts[str(tuple(phase[8:11]))]+=1;kinds[','.join(e['kind'] for e in model['events'])]+=1;previous[0]=count
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*10+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records));(folder/f'{region}-waits.bin').write_bytes(observed);(folder/f'{region}-entries.bin').write_bytes(entries)
  (folder/f'{region}-irq-offsets.json').write_text(json.dumps(irq_evidence)+'\n')
  rows.append(dict(region=region,cases=len(checked),contexts=dict(contexts),IRQ_sequences=dict(kinds),wait_sha256=hashlib.sha256(observed).hexdigest(),entry_sha256=hashlib.sha256(entries).hexdigest()));print(region,len(checked),'wait boundary contexts exact',dict(contexts),dict(kinds),flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Custom boot/caller,busy delays,VINT-enabled mode4 with stale VINT status cleared before delay and source0B95 helper/banks4/6 unchanged. Preceding caller byte0B94 changed toEI for one boundary context;not original routine semantics. Sound80/inactive channels andempty queue;palette skip0/1,compensation0/1,delay0/1/255.','ModesDI-entry,EI+NOP caller,andEI fallthrough at0B94. Capture is after the instruction-boundary interrupt check;model does not repeat that check for the first PUSH. Later EI inhibits the next instruction normally. Latched IRQ,disabled IRQ,prefix audio-only/full sequences and each actual IRQ acceptance offset checked where encountered.','Synthetic phases/state;not every possible latch/phase/queue/driver combination,native equivalence,hardware or full game validation.'])
 (ROOT/'analysis'/('wait_raster_pal_latched_unit_report.json' if extra else 'wait_raster_unit_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
