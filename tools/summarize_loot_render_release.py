"""Bind lifetime, pickup and native rendering evidence to the recommended ROM."""
import json
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_sprite_overflow_bands import body
from validate_sprite_cache_cursor import extract

def main():
 digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());original=sha((ROOT/'input/original.sms').read_bytes());cases=[];images=frames=0
 for kind in range(8,15):
  for region in ['ntsc','pal']:
   tag=f'v0270-type{kind}-{region}';path=ROOT/f'analysis/loot_lifetime_{tag}_report.json';r=json.loads(path.read_bytes());assert r['passed'] and r['md_sha256']==digest and r['records_equal'] and r['states_equal'] and r['all_pixels_equal'];assert len(r['images'])==36 and all(x['pixels']==0 for x in r['images']);assert r['record_frames_compared']==401
   assert r['expiry_frame']==dict(sms=None,md=None) if kind==14 else r['expiry_frame']==dict(sms=3361,md=3361)
   traces=[]
   for core in ['sms','md']:
    folder=ROOT/f'validation/loot-lifetime-{tag}-{core}';capture=json.loads((folder/'capture.json').read_bytes());assert capture['rom_sha256']==(original if core=='sms' else digest)
    traces.append(json.loads((folder/'loot-records.json').read_bytes()))
   assert all(traces[0][str(f)]==traces[1][str(f)] for f in range(3000,3401))
   cases.append(path.name);images+=len(r['images']);frames+=r['record_frames_compared']
 baseline=json.loads((ROOT/'analysis/loot_lifetime_v0267-gold_report.json').read_bytes());assert not baseline['records_equal'] and baseline['expiry_frame']==dict(sms=3361,md=3363)
 pickup=json.loads((ROOT/'analysis/loot_pickup_v0270_report.json').read_bytes());assert pickup['md_sha256']==digest and pickup['pickup_frames_exact']==280 and pickup['normalized_images_exact']==266 and [r['type'] for r in pickup['cases']]==list(range(8,15))
 bands=json.loads((ROOT/'analysis/sprite_overflow_bands_host_report.json').read_bytes());cursor=json.loads((ROOT/'analysis/sprite_cache_cursor_host_report.json').read_bytes());assert bands['passed'] and bands['cases']==23584 and cursor['passed'] and cursor['cases']==24000
 assert bands['production_body_sha256']['current']==sha(body((ROOT/'megadrive/src/main.c').read_text()).encode())
 assert cursor['production_body_sha256']['current']==sha(extract((ROOT/'megadrive/src/actors.c').read_text()).encode())
 spell=[]
 for name in ['level1','level1-pal','actors2','actors2-pal','house','dungeon']:
  r=json.loads((ROOT/f'analysis/screen_spell_v0270-{name}_report.json').read_bytes());assert r['passed'] and r['md_sha256']==digest and r['display_sprite_positions_equal'] and r['display_sprite_tiles_equal'];spell.append(name)
 for name in ['water','water-pal']:
  r=json.loads((ROOT/f'analysis/ice_bell_v0270-{name}_report.json').read_bytes());assert r['passed'] and r['md_sha256']==digest and r['stage_first_frames']['sms']==r['stage_first_frames']['md']
 coherence=json.loads((ROOT/'analysis/world_frame_coherence_v0270_report.json').read_bytes());assert coherence['passed'] and coherence['md_sha256']==digest and len(coherence['cases'])==12
 result=dict(md_sha256=digest,source_sha256=original,passed=True,lifetime_cases=14,lifetime_reports=cases,lifetime_state_frames=frames,lifetime_normalized_images=images,pickup_cases=7,pickup_state_frames=280,pickup_normalized_images=266,overflow_host_cases=bands['cases'],emitter_host_cases=cursor['cases'],spell_regressions=spell,bell_regressions=2,natural_composition_frames=12,full_game_verified=False,limits=['Initial ownership/loot/actor/hero states and one clock alignment are controlled; no natural drop RNG or full-campaign proof.','Lifetime records compare401 consecutive frames per case; normalized images sample36 selected frames per case. Key items are still present at3400, not proven forever.','Host actual-body comparisons establish decision/cache equivalence; native PAL/NTSC captures establish the tested integrations only. No general frame-rate, physical raster or analogue waveform claim.'])
 (ROOT/'analysis/loot_render_release_v0270_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print({k:v for k,v in result.items() if k not in ['lifetime_reports','limits']})
if __name__=='__main__':main()
