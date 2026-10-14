"""Execute original80FF dispatch,all music/SFX and defined control branches."""
import contextlib,ctypes as c,hashlib,io,itertools,json
from actor_reference import ROOT
from audio_dispatch_cost import dispatch_cost
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def main():
 commands=[v for v in range(256) if v not in [0x8e,0x8f,0xad,0xae,0xaf,0xb4]]
 records=list(itertools.product(commands,[0,1,4,16,64,128,192,255],[0,1,128,255],[0,128,255]))
 rom,folder=generate('dispatch',records,[5,0x160,0xf,0xe],0x80ff,'audio-dispatch')
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefix_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_prefix_samples.restype=c.c_uint;dll.gaw_prefix_tstates.restype=c.c_uint64
 dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[]
  def observe(f,r):
   if r[4]:done.append(f)
   sample=dll.gaw_prefix_samples()
   if sample!=previous[0]:
    assert sample==previous[0]+1
    before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400)
    case=int.from_bytes(r[:2],'little');predicted=dispatch_cost(SOURCE,before);cost=dll.gaw_prefix_tstates()
    assert cost==predicted['tstates'],(region,case,records[case],cost,predicted['tstates'])
    assert after==predicted['state'],(region,case,records[case],'RAM',[(i,a,b) for i,(a,b) in enumerate(zip(after,predicted['state'])) if a!=b][:12])
    checked[case]=cost.to_bytes(4,'little')+hashlib.sha256(after).digest();previous[0]=sample
  with contextlib.redirect_stdout(io.StringIO()):run(rom,len(records)*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(records),(region,len(checked),len(records))
  data=b''.join(checked[n] for n in range(len(records)));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=len(checked),results_sha256=hashlib.sha256(data).hexdigest()))
  print(region,len(checked),'original80FF costs and400 RAM bytes exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,excluded_commands=[0x8e,0x8f,0xad,0xae,0xaf,0xb4],production_ROM_changed=False,full_game_ported=False,limits=['Unmodified original80FF and bank6 callees/tables;custom boot/caller,IRQs disabled. All13 music starts,29 effects,B0/B1/B2/B3,80 idle and defined low/high reset branches compare complete400-byte state and instruction cost.','Eight noise ownership flag patterns,four DE0F values,three DE0E values;invalid high/reset values are explicit synthetic probes. Six unsupported/out-of-table command values are excluded,includingB4 jump7000.','Does not compare actual PSG output waveforms,full channel processing/live dispatch phase,source IRQ scheduling or physical loading timing.'])
 (ROOT/'analysis/audio_dispatch_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
