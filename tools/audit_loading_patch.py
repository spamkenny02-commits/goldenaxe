"""Audit the resource-derived loading work, reports, and versioned binary."""
import hashlib,json,re
from actor_reference import ROOT
from actor_loading_cost import resource_cost

def main():
 data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(data).hexdigest();source=(ROOT/'input/original.sms').read_bytes()
 assert len(data)==524288 and int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[n:n+2],'big') for n in range(0x200,len(data),2))&65535
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==data
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16) for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 resources=json.loads((ROOT/'analysis/actor_assets.json').read_text())['resources'];costs={e['type']:resource_cost(source,dict(e,tile_base=0))['foreground_graphics_tstates'] for e in resources}
 for t in range(256):
  off=sy['actor_loading_costs']+t*4;assert int.from_bytes(data[off:off+4],'big')==costs.get(t,0),(t,'compiled cost metadata')
 names=['timing_report','timing-pal_report','loading_budget_report','actor_tick_report','vertical_report','merchant_report','service_transition_report','intro_report','intro-pal_report'];reports=[]
 for name in names:
  path=ROOT/f'validation/{name}.json';raw=path.read_bytes();d=json.loads(raw);assert d['md_sha256']==digest,name
  reports.append(dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest()))
 for suffix in ['', '-pal']:
  d=json.loads((ROOT/f'validation/timing{suffix}_report.json').read_text());assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']);assert d['enemy']['differing_motion_counter_frames']==0
 budget=json.loads((ROOT/'validation/loading_budget_report.json').read_text());assert len(budget['cases'])==8;assert all(abs(x['native_minus_source_completion_frames'])<=1 for x in budget['cases'])
 profiles=[]
 for suffix in ['', '-pal']:
  p=ROOT/f'analysis/actor_loading_profile{suffix}.json';d=json.loads(p.read_text());assert d['source_sha256']==hashlib.sha256(source).hexdigest();assert all(x['observed_tstates']==x['reference_core_tstates'] for x in d['remap_source_cycle_checks']);profiles.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 report=dict(md_sha256=digest,compiled_resource_cost_types=len(costs),targeted_reports=reports,source_cycle_profiles=profiles,natural_vertical_route_loading_timing_exact_in_pal_and_ntsc=True,controlled_persistence_cases=8,remaining_persistence_case_offsets=[dict(region=x['region'],mask=x['persistence_mask'],frames=x['native_minus_source_completion_frames']) for x in budget['cases'] if x['native_minus_source_completion_frames']],full_game_regression=False,clock_budget_model='Nominal ROM instruction work plus approximate 20000T loader control and 3072T IRQ allowance per frame; not cycle-accurate for all rooms.',original_rng_and_sprite_overflow_still_incomplete=True)
 (ROOT/'validation/loading_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Nine reports and 33 compiled ROM-derived resource costs verified; remaining one-frame cases retained')
if __name__=='__main__':main()
