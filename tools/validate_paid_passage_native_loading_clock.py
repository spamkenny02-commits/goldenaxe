"""Execute full production native loader through the paid-passage clock wrapper."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

ROOMS=[0x1a,0x3c,0x36,0x87,0x6d,0x96]

def main():
 reference=json.loads((ROOT/'analysis/paid_passage_source_loading_clock_report.json').read_text())
 assert reference['cases']==24 and all(r['logical_ticks']==1 and r['original_wait_calls']==1 for r in reference['rows'])
 harness=ROOT.parents[1]/'work/paid-passage-clock-harness'
 for path in (ROOT/'megadrive/src').iterdir():
  if not path.is_file():continue
  target=harness/'src'/('game_main.inc' if path.name=='main.c' else 'actors.inc' if path.name=='actors.c' else path.name)
  assert target.read_bytes()==path.read_bytes(),('stale production source',path)
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 folder=ROOT/'validation/paid-passage-native-clock';folder.mkdir(exist_ok=True);regions=[]
 for region in ['auto','pal']:
  checked={};done=[]
  def observe(f,r):
   def read(k,size=2):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(size)),'big')
   if read('harness_done'):done.append(f)
   if not read('harness_ready'):return
   case=read('harness_case')
   if case in checked:return
   room,mask=ROOMS[case//256],case&255;before=read('harness_clock_before');after=read('harness_clock_after');elapsed=read('harness_elapsed',4)
   assert (room,mask)==(read('harness_room'),read('harness_mask')),(region,case,'room/mask')
   assert before==mask and after==(before+1)&255,(region,case,before,after,elapsed)
   assert elapsed>0,(region,case,'actual loader did not consume interrupt time')
   checked[case]=dict(room=room,mask=mask,before_clock=before,after_clock=after,elapsed_video_ticks=elapsed)
  with contextlib.redirect_stdout(io.StringIO()):
   run(harness/'out/release/rom.bin',50000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==1536,(region,len(checked),len(done))
  regions.append(dict(region=region,cases=len(checked),rows=list(checked.values())))
  print(region,len(checked),'actual native paid loading clocks exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=reference['source_sha256'],source_clock_report_sha256=hashlib.sha256((ROOT/'analysis/paid_passage_source_loading_clock_report.json').read_bytes()).hexdigest(),harness_sha256=hashlib.sha256((harness/'out/release/rom.bin').read_bytes()).hexdigest(),cases=sum(r['cases'] for r in regions),regions=regions,full_game_ported=False,limits=[
  'All production source files byte-identical to harness inputs. Actual load_paid_passage_room/load_house_room decode,convert,load enemy patterns and publish VDP data. Harness supplies class1 origin9F,target/hero/valid inventory/save state; no loader stub or forced vtimer advancement.',
  'All six destinations/all256 enemy persistence masks,both regions. Initial logical clock sweeps all256 values including wrap255->0. Source24 live paths independently establish the single logical tick rule; intermediate masks use the original IRQ gate invariant.',
  'Checks logical-clock delta only. Physical loading/fade/contour duration,source RNG/refresh,natural combat and whole transition equivalence remain open. Harness is not a full natural gameplay test.'])
 (ROOT/'validation/paid_passage_native_loading_clock_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
