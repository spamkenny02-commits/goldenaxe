"""Check instruction-derived models against retained unmodified live source exits."""
import hashlib,json
from actor_reference import ROOT
from class0_graphics_loading_cost import class0_graphics_cost
from full_actor_loading_cost import full_actor_cost
from room_map_loading_cost import room_map_cost

PHASES=[
 ('classify_and_bank_change',0x16d0,0x16ef),
 ('palette_and_patterns',0x16ef,0x1706),
 ('metatiles',0x1706,0x170e),
 ('metatile_backup',0x170e,0x1720),
 ('terrain_patch',0x1720,0x1723),
 ('dungeon_palette_skip',0x1723,0x172b),
 ('extra_metatiles',0x172b,0x1733),
 ('terrain_pointer',0x1733,0x173a),
 ('terrain_decode',0x173a,0x1748),
 ('SRAM_enable',0x1748,0x174b),
 ('terrain_SRAM_copy',0x174b,0x1756),
 ('SRAM_disable_return',0x1756,0x24b9)]

def main():
 source=(ROOT/'input/original.sms').read_bytes()
 graphics=class0_graphics_cost(source);rows=[];evidence=[]
 for region in ['auto','pal']:
  path=ROOT/f'validation/paid-passage-loader/{region}-cycle-events.json'
  events=json.loads(path.read_text());evidence.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  def interval(start,end,after=0):
   a=next(e for e in events if e[1]==start and e[4]==0x96 and e[2]>after)
   b=next(e for e in events if e[1]==end and e[2]>a[2])
   delta=(b[2]-a[2])-(b[3]-a[3])
   assert delta%15==0,(region,start,end,delta)
   return delta//15
  checked={}
  for name,start,end in PHASES:
   observed=interval(start,end);expected=graphics['components'][name]
   assert observed==expected,(region,name,observed,expected)
   checked[name]=observed
  for name,start,end,expected in [
   ('whole_graphics',0x16d0,0x24b9,graphics['foreground_tstates']),
   ('room_map_preparation',0x2279,0x1de5,room_map_cost()['foreground_tstates']),
   ('whole_actors',0x1780,0x18e1,full_actor_cost(source,0x96,255)['foreground_tstates'])]:
   observed=interval(start,end);assert observed==expected,(region,name,observed,expected)
   checked[name]=observed
  map_hud=interval(0x24bc,0x24bf)
  commit_start=next(e[2] for e in events if e[1]==0x1de8 and e[4]==0x96)
  wait_spin=interval(0xb95,0xbb3,after=commit_start)
  # This span contains register saves and the busy loop; restoration is outside it.
  rows.append(dict(region=region,exact_modeled_phases=checked,map_HUD_and_wait_tstates=map_hud,wait_save_spin_tstates=wait_spin,remaining_map_HUD_tstates=map_hud-wait_spin))
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),evidence=evidence,regions=rows,exact_phase_comparisons=len(rows)*(len(PHASES)+3),production_ROM_changed=False,full_game_ported=False,limits=[
  'Retained live original6D->96 paid-exit profiles; original source routines are unpatched. Controlled entrance/hero/initial clock only; destination enemies retained.',
  'Twelve graphics components plus complete graphics,map preparation and actors match separately in PAL/NTSC. Models cover the stated class0,C0AC0,maskFF live path; controlled graphics36 and actor1536 validations broaden only those model scopes.',
  'The0B95->0BB3 span includes wait register saves and busy loop,not its restoration. It is selected after1DE8 to exclude earlier fade waits. Remaining PAL/NTSC totals differ by1T from the palette clock-bit branch,as independently derived in live_map_hud_loading_cost_report.json; not a universal calibrated constant.',
  'Source logical-clock freezes,native elapsed work,RNG and whole transition equivalence remain unfinished. Separate190B/HUD models cover only their explicitly validated scopes.'])
 (ROOT/'analysis/paid_passage_loading_phase_costs_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['exact_phase_comparisons'],'instruction-derived live loading phases exact',flush=True)

if __name__=='__main__':main()
