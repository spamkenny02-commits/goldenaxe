"""Controlled reveal callers exercise IRQ/DIEI/status phase boundaries."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct,collections,sys
from actor_reference import ROOT
from validate_audio_prefix_cost import generate,SOURCE
from reveal_phase_prediction import predict_reveal
from validate_reveal_phase_prediction import check_checkpoint
from run_core import run

def main():
 sweep='--status-sweep' in sys.argv;coalescence='--coalescence-sweep' in sys.argv
 delays=sorted(set([0,1,127,511,1023,2047,4095]+list(range(2000,2301,11))))
 records=[(d&255,d>>8,m,p,k,t) for d,m,p,k,t in itertools.product(delays,[0,1,2],[0,1],[0,1],[0,1,255])]
 if sweep:records=[(d&255,d>>8,1,0,k,0) for d,k in itertools.product(list(range(250,551))+list(range(1800,2401)),[0,1])]
 if coalescence:records=[(d&255,d>>8,2,0,k,t) for d,k,t in itertools.product(range(4230,4321),[0,1],[0,1,255])]
 rom,folder=generate('reveal',records,list(range(0x20,0x26)),0x3040,'reveal-phase-coalescence-unit' if coalescence else 'reveal-phase-status-unit' if sweep else 'reveal-phase-unit')
 image=bytearray(rom.read_bytes());image[0x3430:0x3430+400]=bytes(400);image[0x1fa6]=0xfb;image[0xace]=image[0x1fb6]=0xc9
 stub=bytearray();labels={};fix=[]
 def emit(h):stub.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3040+len(stub)
 def jump(op,n):emit(op);fix.append((len(stub),n));emit('0000')
 emit('f32100dd2234c0af773e063210c03e803211c03a23de3233c03a24de3203de3a25de3230c03e803205de3ea0d3bf3e81d3bfdbbfed4b20de78b128050b78b120fb3a22deb7')
 jump('ca','disabled');emit('fe01');jump('ca','enabled');emit('cda61f');jump('c3','finish')
 label('enabled');emit('fb00cda71f');jump('c3','finish')
 label('disabled');emit('cda71f');label('finish');emit('f33e80d3bf3e81d3bfc9')
 for pos,name in fix:stub[pos:pos+2]=labels[name].to_bytes(2,'little')
 assert 0x3040+len(stub)<0x3100;image[0x3040:0x3040+len(stub)]=stub;rom.write_bytes(image)
 for start,end in [(0x1fa7,0x1fb6),(0xaa4,0xace),(0xb95,0xbc6),(0x397,0x3ab),(0x10000,0x14000),(0x18000,0x1c000)]:assert image[start:end]==SOURCE[start:end]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_revealphase_libretro.dll';dll=c.CDLL(str(core));dll.gaw_foreground_phase_samples.restype=c.c_uint;dll.gaw_foreground_phase_events.restype=c.POINTER(c.c_uint8);dll.gaw_wait_samples.restype=c.c_uint;dll.gaw_wait_events.restype=c.POINTER(c.c_uint64);dll.gaw_wait_entry_events.restype=c.POINTER(c.c_uint8);dll.gaw_audio_irq_count.restype=c.c_uint;dll.gaw_audio_irq_events.restype=c.POINTER(c.c_uint64)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];group=[];retained=bytearray();waits=bytearray();entries=bytearray();stats=collections.Counter();irq_evidence=[]
  def observe(f,r):
   if r[4]:done.append(f)
   count=dll.gaw_foreground_phase_samples()
   if count==previous[0]:return
   base=c.addressof(dll.gaw_foreground_phase_events().contents);raw=c.string_at(base+previous[0]*800,(count-previous[0])*800);previous[0]=count
   for offset in range(0,len(raw),800):
    rec=raw[offset:offset+800];pc,time=struct.unpack_from('<2Q',rec);actual=dict(pc=pc,time=time,phase=struct.unpack_from('<12I',rec,16),ram=rec[64:400],sound=rec[400:800]);retained.extend(rec)
    if pc==0x1fa7:group.clear()
    group.append(actual)
    if pc!=0xace:continue
    case=int.from_bytes(r[:2],'little');assert [x['pc'] for x in group]==[0x1fa7,0xaa4,0xbb3,0xac0,0xace]
    initial,clear,returned,restored,end=group;model=predict_reveal(SOURCE,initial['phase'],initial['ram'],initial['sound']);n=dll.gaw_wait_samples();wraw=c.string_at(c.addressof(dll.gaw_wait_events().contents)+(n-1)*112,112);e=c.string_at(c.addressof(dll.gaw_wait_entry_events().contents)+(n-1)*784,784);w=struct.unpack('<14Q',wraw);waits.extend(wraw);entries.extend(e)
    wait_entry=dict(pc=0xb95,time=w[0],phase=struct.unpack_from('<12I',e),ram=e[48:384],sound=e[384:784])
    for pred,act,span in [(model['clear'],clear,clear['time']-initial['time']),(model['before_wait'],wait_entry,w[0]-initial['time']),(model['wait'],returned,returned['time']-w[0]),(model['restored'],restored,restored['time']-returned['time']),(model['after'],end,end['time']-returned['time'])]:check_checkpoint(pred,act,span,(region,case,records[case]))
    assert model['wall_master_cycles']==end['time']-initial['time'] and (model['wait']['taken'],model['wait']['exits'])==w[4:6]
    predicted=[(i['entry_offset_master'],False) for i in model['before_wait']['events']]+[(model['before_wait']['wall_master_cycles']+i['entry_offset_master'],i['kind']=='full') for i in model['wait']['events']]+[(model['before_wait']['wall_master_cycles']+model['wait']['wall_master_cycles']+i['entry_offset_master'],False) for i in model['after']['events']]
    events=dll.gaw_audio_irq_events();observed=[]
    for j in range(dll.gaw_audio_irq_count()-1,-1,-1):
     timestamp=events[j*14+1]
     if timestamp<=initial['time']:break
     if timestamp<end['time'] and events[j*14]==0x137:observed.append((timestamp-initial['time'],bool(events[j*14+4])))
    observed.reverse();assert observed==predicted,(region,case,'IRQ offsets',observed,predicted)
    checked[case]=True;irq_evidence.append(dict(case=case,entries=observed));stats['status_suppressions']+=model['before_wait']['status_suppressions'];stats['vector_coalescences']+=model['before_wait']['vector_coalescences'];stats['prewait_audio_IRQs']+=len(model['before_wait']['events']);stats['postwait_audio_IRQs']+=len(model['after']['events'])
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*12+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records));(folder/f'{region}-foreground.bin').write_bytes(retained);(folder/f'{region}-waits.bin').write_bytes(waits);(folder/f'{region}-entries.bin').write_bytes(entries);(folder/f'{region}-irq-offsets.json').write_text(json.dumps(irq_evidence)+'\n')
  rows.append(dict(region=region,cases=len(checked),stats=dict(stats),raw_sha256=hashlib.sha256(retained).hexdigest()));print(region,len(checked),'reveal chains exact',dict(stats),flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Custom callers andunused-byte1FA6 EI entry;stops atACE/1FB6 RET after predicted target. Actual1FA7..1FB6,AA4..ACE,0397 and0B95 code/banks4/6 unchanged. Empty queue,inactive audio80 andzero palettes.','DI/EI/latched contexts,busy-delay phases,palette skip/compensation/delay counter boundaries;status-sweep mode targets fine phase differences. Five checkpoint phases,331 RAM bytes,400 sound bytes,wait decisions andall IRQ offsets assert independently against execution.','Palette/VRAM byte outputs,statusC01B/inputC020..23,native/hardware andfull game not proved. Entry state supplied;earlier load phase remains open.'])
 (ROOT/'analysis'/('reveal_phase_coalescence_unit_report.json' if coalescence else 'reveal_phase_status_unit_report.json' if sweep else 'reveal_phase_unit_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
