"""Execute unmodified807E tempo/80C8 fade and compare400 RAM bytes and cost."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_prefix_cost import tempo_cost,fade_cost
from run_core import run

SOURCE=(ROOT/'input/original.sms').read_bytes()
SEED=bytes((i*37+17)&255 for i in range(400))

def rows(kind):
 if kind=='tempo':return [(a,b,12,1,18,0,10,11,255,0,1,254,255) for a,b in itertools.product(range(256),[0,1,6,255])]
 return [(7,6,b,counter,18,*v,0,1,254,255) for b,counter,v in itertools.product([0,1,2,12],[0,1,2,18],itertools.product([0,10,11,255],repeat=4))]

def generate(kind,records):
 image=bytearray(SOURCE)+bytearray(0x200000-len(SOURCE));code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3100+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
 label('case');emit('2130341100de019001edb03a08c032ffffdd2a06c0')
 offsets=[1,2,0xb,0xc,0xd,0x48,0x78,0xa8,0x18,0x4a,0x7a,0xaa,0xda]
 for i,offset in enumerate(offsets):emit(f'dd7e{i:02x}32'+(0xde00+offset).to_bytes(2,'little').hex())
 emit('3e0632ffffcd00300603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a06c011100019cb74');jp('ca','pointer');emit('2100803a08c03c3208c0')
 label('pointer');emit('2206c02a00c0232200c001'+len(records).to_bytes(2,'little').hex()+'b7ed42')
 jp('c2','case');emit('3e013204c0');label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30031');image[0x3100:0x3100+len(code)]=code
 image[0x3430:0x3430+400]=SEED
 image[0x3000:0x3004]=b'\xcd'+(0x807e if kind=='tempo' else 0x80c8).to_bytes(2,'little')+b'\xc9'
 data=b''.join(bytes(r)+bytes(16-len(r)) for r in records);image[0x80000:0x80000+len(data)]=data
 assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000],'original bank6 modified'
 folder=ROOT/f'validation/audio-prefix/{kind}';folder.mkdir(parents=True,exist_ok=True)
 rom=folder/'source.sms';rom.write_bytes(image);return rom,folder

def main():
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefix_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64
 dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 cases=[]
 for kind,model in [('tempo',tempo_cost),('fade',fade_cost)]:
  records=rows(kind);rom,folder=generate(kind,records)
  for region in ['auto','pal']:
   dll.gaw_timing_reset();previous=[0];checked={};done=[]
   def observe(f,r):
    if r[4]:done.append(f)
    sample=dll.gaw_prefix_samples()
    if sample!=previous[0]:
     assert sample==previous[0]+1,(kind,region,'multiple helper calls in one frame')
     before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
     case=int.from_bytes(r[:2],'little');predicted=model(before);cost=dll.gaw_prefix_tstates()
     assert cost==predicted['tstates'],(kind,region,case,records[case],cost,predicted['tstates'])
     assert after==predicted['state'],(kind,region,case,'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
     checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
   with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   assert done and len(checked)==len(records),(kind,region,len(checked),len(records))
   result=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(result)
   cases.append(dict(kind=kind,region=region,cases=len(checked),results_sha256=hashlib.sha256(result).hexdigest(),fixture_rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest()))
   print(kind,region,len(checked),'original costs and400 RAM bytes exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(x['cases'] for x in cases),rows=cases,production_ROM_changed=False,full_game_ported=False,limits=['Unmodified original bank6 helpers807E and80C8,including83EF stop/mute path. Custom boot/3000 caller supplies400-byte patterned RAM and16-byte input records from extra banks;IRQs disabled. Independent semantic/cycle models compare all400 bytes and complete helper costs.','Tempo:all256 counters,four reload values,phase increment wrap. Fade:B0/1/2/12,C0/1/2/18,all four-volume combinations0/10/11/255. Invalid boundary255 is synthetic. Regions checked separately.','Isolated helper tests do not establish full reader cost,PSG mute waveform,live prefixes/IRQ phase,physical loading duration or natural progression.'])
 (ROOT/'analysis/audio_prefix_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
