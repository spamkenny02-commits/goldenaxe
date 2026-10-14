"""Measure production wait_frame with display on/off at224 scanline positions."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
 harness=ROOT.parents[1]/'work/reveal-wait-harness'
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(harness/'src'/('game_main.inc' if p.name=='main.c' else 'actors.inc' if p.name=='actors.c' else p.name)).read_bytes(),p
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (harness/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 for region in ['auto','pal']:
  captured=[]
  def observe(f,r):
   read=lambda name,n:bytes(r[(sy[name]+i)^1] for i in range(n))
   if not captured and int.from_bytes(read('harness_done',2),'big'):captured.append(read('harness_wait_results',1792))
  folder=ROOT/f'validation/reveal-wait/{region}'
  with contextlib.redirect_stdout(io.StringIO()):run(harness/'out/release/rom.bin',4000,folder,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert captured,'harness did not finish'
  raw=captured[0];(folder/'wait-results.bin').write_bytes(raw)
  values=[int.from_bytes(raw[n:n+2],'big') for n in range(0,len(raw),2)]
  rows=[]
  for enabled in range(2):
   for fresh in range(2):
    ticks=values[(enabled*2+fresh)*224:(enabled*2+fresh+1)*224]
    if fresh:assert all(t==1 for t in ticks),(region,enabled,'fresh wait',[(i,t) for i,t in enumerate(ticks) if t!=1])
    if not enabled and not fresh:assert 0 in ticks,'disabled display issue not reproduced'
    rows.append(dict(display_enabled=bool(enabled),fresh_IRQ_required=bool(fresh),ticks_by_start_scanline=ticks,zero_tick_calls=ticks.count(0)))
  cases.append(dict(region=region,rows=rows));print(region,'scanline sweep passed;',rows[0]['zero_tick_calls'],'display-off calls returned before next IRQ',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),harness_sha256=hashlib.sha256((harness/'out/release/rom.bin').read_bytes()).hexdigest(),cases=cases,limits=['Compiled production wait_frame,224 start scanlines,display enabled/disabled,with/without explicit fresh vtimer gate,PAL/NTSC. Dedicated harness has no game/audio workload.','Source0BA7..0BB3 setsC02E and waits for its IRQ acknowledgement. This test establishes fresh IRQ waiting semantics only;not full reveal timing or hardware equivalence.'])
 (ROOT/'validation/reveal_wait_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
