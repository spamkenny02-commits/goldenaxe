"""Exercise original fullIRQ with custom caller and controlled input/timer boundaries."""
import contextlib,ctypes as c,hashlib,io,itertools,json,struct
from actor_reference import ROOT
from validate_audio_prefix_cost import generate,SOURCE
from audio_reader_cost import reader_cost
from full_irq_cost import full_irq_cost
from run_core import run

def main():
 records=list(itertools.product([0,1],[0,1,2,3],[0,1,2,127,255],[0,1,255],[0,255],[0,1,255],[0,1]))
 rom,folder=generate('full-irq',records,list(range(0x20,0x27)),0x3040,'full-irq-unit')
 image=bytearray(rom.read_bytes());image[0x3430:0x3430+400]=bytes(400);stub=bytearray()
 for n,address in enumerate([0xc033,0xc045,0xc01c,0xc030,0xc020,0xc022,0xde03]):stub+=b'\x3a'+(0xde20+n).to_bytes(2,'little')+b'\x32'+address.to_bytes(2,'little')
 stub+=bytes.fromhex('3e803205de2100dd2234c036003e01322ec0f5c33701');image[0x3040:0x3040+len(stub)]=stub;rom.write_bytes(image)
 assert image[0x10000:0x14000]==SOURCE[0x10000:0x14000] and image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_fullirq_libretro.dll';dll=c.CDLL(str(core));dll.gaw_full_irq_samples.restype=c.c_uint;dll.gaw_full_irq_records.restype=c.POINTER(c.c_uint8);dll.gaw_live_envelope_samples.restype=c.c_uint;dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];retained=bytearray()
  def observe(f,r):
   if r[4]:done.append(f)
   count=dll.gaw_full_irq_samples()
   if count!=previous[0]:
    assert count==previous[0]+1;case=int.from_bytes(r[:2],'little');raw=c.string_at(dll.gaw_full_irq_records(),count*800)[-800:];points=struct.unpack_from('<12Q',raw);values=struct.unpack_from('<8I',raw,96)
    readers=dll.gaw_live_envelope_samples();assert readers==count;reader=c.string_at(dll.gaw_live_envelope_events(),readers*824)[-824:];ix,de,finalde,a,cost,unwind=struct.unpack_from('<6I',reader)
    audio=reader_cost(SOURCE,reader[24:424],de);assert not unwind and cost==audio['tstates'] and finalde==audio['de'] and reader[424:824]==audio['state']
    prediction=full_irq_cost(SOURCE,raw[128:464],*values[:4],values[4],audio['tstates']);times=[points[0]]+list(points[2:11]);assert [(b-a)//15 for a,b in zip(times,times[1:])]==list(prediction['stages'].values()),(region,case,records[case],'stage')
    assert raw[464:800]==prediction['state'],(region,case,'RAM');checked[case]=hashlib.sha256(raw).digest();retained.extend(raw);previous[0]=count
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records));(folder/f'{region}-records.bin').write_bytes(retained);rows.append(dict(region=region,cases=len(checked),raw_sha256=hashlib.sha256(retained).hexdigest()))
  print(region,len(checked),'controlled fullIRQ boundary cases exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Original fixedIRQ/banks4/6 unchanged. Custom boot/stub supplies caller AF frame,fullIRQ flag,empty queue andsound80/inactive channels. Hardware IRQ generation disabled;original handler enables CPU interrupts but VDP IRQs stay disabled.','Palette skip0/1,HUDflags0/1/2/3,pause timer0/1/2/127/255,delay0/1/255,oldbuttons0/255,oldpause0/1/255,compensation0/1;both regions. Captured palette decisions andactual input ports supplied;336-byte state/nine complete stage costs andreader400-byte state/DE/cost compared.','Not raster-phase prediction,queue boundary exhaustiveness,native equivalence or hardware/full game proof.'])
 (ROOT/'analysis/full_irq_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
