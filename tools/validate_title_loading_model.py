"""Bind source cycle model and native post-intro schedule to the current ROM."""
import hashlib,json,re
from run_core import ROOT
from title_loading_cost import title_cost

def main():
 rom=(ROOT/'input/original.sms').read_bytes();model=title_cost(rom);profiles=[]
 metadata=json.loads((ROOT/'analysis/title_assets.json').read_text());assert metadata['loading_cost']==model
 assert f"const u32 title_loading_tstates = {model['foreground_tstates']};" in (ROOT/'megadrive/src/title_data.c').read_text()
 for suffix in ['', '-pal']:
  path=ROOT/f'analysis/title_loading_profile{suffix}.json';profile=json.loads(path.read_text())
  assert profile['source_sha256']==hashlib.sha256(rom).hexdigest()
  assert profile['foreground_components_exact'] and profile['full_model']==model
  profiles.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),profile=profile))
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),instruction_derived_model=model,source_profiles=profiles,irq_reserve_per_frame_tstates=3072,regional_loading_frames={region:(model['foreground_tstates']+period-3072-1)//(period-3072) for region,period in [('ntsc',59736),('pal',71364)]},native_work_counts_toward_schedule=True,source_foreground_cycles_exact=True,all_irq_phases_cycle_exact=False,no_emulator_states_or_code_executed_in_native_rom=True)
 (ROOT/'validation/title_loading_model_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Title foreground model matches both source profiles:',model['foreground_tstates'])
if __name__=='__main__':main()
