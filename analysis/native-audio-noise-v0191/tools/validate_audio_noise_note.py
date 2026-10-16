"""Original8679 noise-note helper vs independent cost and compiled native PSG."""
import contextlib,ctypes as c,hashlib,io,itertools,json,re,sys,struct
from actor_reference import ROOT
from audio_noise_note_cost import noise_note_cost
from validate_audio_prefix_cost import generate,SOURCE,SEED
from run_core import run

def records():return list(itertools.product(range(256),[0,4,128,132],[0,15,255],[0,3,255]))
def setup():
 rows=records();folder=ROOT/'validation/audio-noise-note';folder.mkdir(exist_ok=True)
 (folder/'cases.inc').write_text('static const u8 raw_cases[][4]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in rows)+'};\nstatic const u8 raw_seed[400]={'+','.join(map(str,SEED))+'};\n')
 rom,unit=generate('helper',rows,[0x3e,0xd0,0x18,0x17],0x3040,'audio-noise-note',0xded0)
 image=bytearray(rom.read_bytes());image[0x3430+0xd1]=0xe0
 #Seed audible noise every case, then load A and tail-jump to untouched8679.
 stub=bytes.fromhex('3ee6d37f3ef0d37f3a3edec37986');image[0x3040:0x3040+len(stub)]=stub;rom.write_bytes(image)
 assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 return rows,folder,rom

def main():
 rows,folder,rom=setup()
 if '--setup' in sys.argv:return
 harness=ROOT.parents[1]/'work/audio-noise-note-harness'
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(harness/'src'/('game_main.inc' if p.name=='main.c' else 'actors.inc' if p.name=='actors.c' else p.name)).read_bytes(),('stale harness',p.name)
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefix_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 results=[]
 for region in ['auto','pal']:
  source={};source_psg={};costs={};done=[];previous=[0];psg=[None];dll.gaw_timing_reset()
  def source_observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1;case=int.from_bytes(r[:2],'little')
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
    predicted=noise_note_cost(before,rows[case][0]);cost=dll.gaw_prefix_tstates()-59
    assert cost==predicted['tstates'],(region,case,rows[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,'model RAM')
    source[case]=after;source_psg[case]=psg[0][6:8];costs[case]=cost;previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(rows)*4+100,folder/f'{region}-sms',set(),[],core=core,skip_intro=False,ram_observer=source_observe,psg_observer=lambda f,p:psg.__setitem__(0,p),core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(source)==len(rows)
  native={};native_psg={};done=[];psg=[None]
  def native_observe(f,r):
   data=lambda name,n:bytes(r[(sy[name]+i)^1] for i in range(n))
   if int.from_bytes(data('harness_done',2),'big'):done.append(f)
   if int.from_bytes(data('harness_ready',2),'big'):
    case=int.from_bytes(data('harness_case',2),'big');native[case]=data('sound_ram',400);native_psg[case]=psg[0][6:8]
  with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',len(rows)*4+100,folder/f'{region}-md',set(),[],skip_intro=False,core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll',ram_observer=native_observe,psg_observer=lambda f,p:psg.__setitem__(0,p),core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(native)==len(rows)
  differences=[dict(case=i,fixture=rows[i],ram_byte_indices=[n for n in range(400) if source[i][n]!=native[i][n]],source_psg=source_psg[i],native_psg=native_psg[i]) for i in range(len(rows)) if source[i]!=native[i] or source_psg[i]!=native_psg[i]]
  prefix=f"{region}-{'baseline-' if '--baseline' in sys.argv else ''}"
  for tag,states,registers in [('sms',source,source_psg),('md',native,native_psg)]:
   (folder/f'{prefix}{tag}-states.bin').write_bytes(b''.join(states[i] for i in range(len(rows))))
   (folder/f'{prefix}{tag}-psg.bin').write_bytes(b''.join(struct.pack('<2I',*(v&0xffffffff for v in registers[i])) for i in range(len(rows))))
  (folder/f'{prefix}costs.bin').write_bytes(b''.join(costs[i].to_bytes(4,'little') for i in range(len(rows))))
  results.append(dict(region=region,cases=len(rows),source_cost_and_state_model_exact=True,mismatches=len(differences),differences=differences));print(region,len(rows),'noise helper model exact;',len(differences),'native RAM/PSG mismatches',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),fixture_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in results),rows=results,all_cases_exact=all(not r['mismatches'] for r in results),full_game_ported=False,limits=['Original8679..86DA/863E and bank6 unchanged. Custom boot/stub loads explicitA and initializes PSG E6/F0 before calling helper. Stub cost59T subtracted;400 bytes and complete helper cost predicted independently;IRQs disabled.','All256 note bytes,flags0/4/128/132,global volume0/15/255 and noise offset0/3/255. Native harness copies production sources,invokes actualsound_noise_note,compares400 RAM bytes and noise PSG control/volume registers (including muted frequency). Synthetic boundaries;no natural-event reachability or waveform assertion.','Whole noise channel,commands,reader and physical loading prediction remain incomplete.'])
 name='noise_note_baseline_report.json' if '--baseline' in sys.argv else 'noise_note_report.json';(ROOT/'analysis'/name).write_text(json.dumps(report,indent=2)+'\n')
 if '--baseline' in sys.argv:assert not report['all_cases_exact'],'Baseline regression not reproduced'
 else:assert report['all_cases_exact'],'Native noise helper differs'
if __name__=='__main__':main()
