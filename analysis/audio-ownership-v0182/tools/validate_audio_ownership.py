"""Compare original8357 F3 ownership stop with compiled native sound_sequence."""
import contextlib,ctypes as c,hashlib,io,itertools,json,re,sys
from actor_reference import ROOT
from validate_audio_prefix_cost import generate,SOURCE,SEED
from run_core import run

def records():return list(itertools.product([0,4,64,128,196],[128,160,192,224],[0,1,127,128,255],[0,128]))

def setup():
 rows=records();folder=ROOT/'validation/audio-ownership';folder.mkdir(exist_ok=True)
 (folder/'cases.inc').write_text('static const u8 raw_cases[][4]={\n'+''.join('{'+','.join(map(str,r))+'},\n' for r in rows)+'};\nstatic const u8 raw_seed[400]={'+','.join(map(str,SEED))+'};\n')
 rom,unit=generate('raw-note',rows,[0x40,0x41,0x0f,0x130],0x8357,'audio-ownership',0xde40,True)
 image=bytearray(rom.read_bytes());image[0x3473:0x3475]=(0x9b2b).to_bytes(2,'little');rom.write_bytes(image)
 assert SOURCE[0x19b2b:0x19b2e]==bytes([0xf3,0xe7,0])
 return rows,folder,rom

def main():
 rows,folder,rom=setup()
 if '--setup' in sys.argv:return
 harness=ROOT.parents[1]/'work/audio-ownership-harness'
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(harness/'src'/('game_main.inc' if p.name=='main.c' else 'actors.inc' if p.name=='actors.c' else p.name)).read_bytes(),('stale harness source',p.name)
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_tableenvelope_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 results=[]
 for region in ['auto','pal']:
  snapshots={};done=[];previous=[0];dll.gaw_timing_reset()
  def source_observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1;case=int.from_bytes(r[:2],'little')
    snapshots[case]=c.string_at(dll.gaw_prefix_return(),400);previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(rows)*4+100,folder/f'{region}-sms',set(),[],core=core,skip_intro=False,ram_observer=source_observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(snapshots)==len(rows)
  native={};done=[]
  def native_observe(f,r):
   data=lambda name,n:bytes(r[(sy[name]+i)^1] for i in range(n))
   if int.from_bytes(data('harness_done',2),'big'):done.append(f)
   if int.from_bytes(data('harness_ready',2),'big'):
    case=int.from_bytes(data('harness_case',2),'big');native[case]=data('sound_ram',400)
  with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',len(rows)*4+100,folder/f'{region}-md',set(),[],skip_intro=False,ram_observer=native_observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(native)==len(rows)
  differences=[dict(case=i,fixture=rows[i],byte_indices=[n for n in range(400) if snapshots[i][n]!=native[i][n]],source_duration=snapshots[i][0x4a],native_duration=native[i][0x4a],source_cursor=snapshots[i][0x43:0x45].hex(),native_cursor=native[i][0x43:0x45].hex()) for i in range(len(rows)) if snapshots[i]!=native[i]]
  for tag,states in [('sms',snapshots),('md',native)]:(folder/f"{region}-{'baseline-' if '--baseline' in sys.argv else ''}{tag}-states.bin").write_bytes(b''.join(states[i] for i in range(len(rows))))
  results.append(dict(region=region,cases=len(rows),mismatches=len(differences),differences=differences))
  print(region,len(rows),'F3 ownership cases;',len(differences),'mismatches',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),cases=sum(r['cases'] for r in results),rows=results,all_cases_exact=all(not r['mismatches'] for r in results),full_game_ported=False,limits=['Unmodified original8357 and bank6; actual ROM9B2B F3/E7/00 bytes interpreted as control/argument/duration. Custom caller,IRQs disabled. Native harness copies every production source and invokes actual sound_sequence with original assets.','Five flags,four channel types,five priorities and active/inactive borrowed channel. Compares400 driver bytes; targeted boundaries do not prove natural reachability.','No full channel execution,PSG waveform or hardware claim.'])
 name='audio_ownership_baseline_report.json' if '--baseline' in sys.argv else 'audio_ownership_report.json'
 (ROOT/'analysis'/name).write_text(json.dumps(report,indent=2)+'\n')
 if '--baseline' in sys.argv:assert not report['all_cases_exact'],'Baseline regression not reproduced'
 else:assert report['all_cases_exact'],'Native raw-note duration differs from source'

if __name__=='__main__':main()
