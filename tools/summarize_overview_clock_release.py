"""Bind modal counter evidence without post-activation clock injection."""
import gzip,json
from PIL import Image
from run_core import ROOT
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/overview-clock-v0273';m=json.loads((archive/'manifest.json').read_bytes());i=m['compressed'][path.relative_to(ROOT).as_posix()];encoded=(archive/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'];return raw

def main():
 digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());source=sha((ROOT/'input/original.sms').read_bytes());sy=symbols(ROOT/'megadrive/out/release/symbol.txt');reports=sorted((ROOT/'analysis').glob('overview_clock_v0273*_report.json'));assert len(reports)==22;cases=[];returns=[];images=0;generation_frames=0;physical_mismatches=0
 for p in reports:
  r=json.loads(p.read_bytes());assert r['passed'] and r['md_sha256']==digest and r['source_sha256']==source and r['generation_counter_frozen'];assert r['initial_clock_alignment_frame']==2850 and not r['clock_alignment_after_activation'];offset=r['steady_clock_phase_offset'];assert offset in [0,1]
  name=p.stem.removeprefix('overview_clock_').removesuffix('_report');folders={s:ROOT/f'validation/overview-clock-{name}-{s}' for s in ['sms','md']}
  for core,folder in folders.items():
   capture=json.loads((folder/'capture.json').read_bytes());assert capture['rom_sha256']==(source if core=='sms' else digest);assert all(w['frame']<=2850 for w in capture['test_ram_writes'])
  if r['graphics']:cases.append(dict(case=name,guard=True,clock_phase_offset=offset));continue
  assert all(v==[r['generation_expected_counter']] for v in r['generation_counter_values'].values())
  rows={s:json.loads((folder/'states.json').read_bytes()) for s,folder in folders.items()}
  for core in ['sms','md']:
   first=r['room_progress'][core][1]['frame'];last=r['room_progress'][core][-1]['frame'];selected=[x for x in rows[core] if first<=x['frame']<last];assert len(selected)==last-first and all(x['clock']==r['generation_expected_counter'] for x in selected);generation_frames+=len(selected)
  if not r['held_close_during_generation']:
   assert r['overview_planar_5120_bytes_exact'] and r['overview_tilemap_1280_bytes_exact']
   images+=len(r['logical_clock_pixel_comparisons']);physical_mismatches+=sum(bool(x['differences']) for x in r['pixel_comparisons'])
   assert all(x['differences']==0 and x['source_frame']-x['native_frame']==offset for x in r['logical_clock_pixel_comparisons'])
  before={s:read(folder/'ram_02859.bin') for s,folder in folders.items()};after={'sms':read(folders['sms']/f'ram_{4200+offset:05d}.bin'),'md':read(folders['md']/'ram_04200.bin')};data=lambda b,key,n:bytes(b[(sy[key]+i)^1] for i in range(n))
  assert before['sms'][0x1c00:0x1ca0]==after['sms'][0x1c00:0x1ca0] and data(before['md'],'scratch',0x8a0)[0x800:]==data(after['md'],'scratch',0x8a0)[0x800:]
  assert data(before['md'],'room_metadata',3)==data(after['md'],'room_metadata',3)
  for core in ['sms','md']:
   prior=bytearray(before[core][0x100:0x200] if core=='sms' else data(before[core],'game_save_state',0x150)[0x50:])
   if r['ice']:
    for room in [0x96,0xaa,0xcb]:prior[room]|=1
   current=after[core][0x100:0x200] if core=='sms' else data(after[core],'game_save_state',0x150)[0x50:];assert current==prior
  assert int.from_bytes(data(after['md'],'world_overview_active',2),'big')==0 and int.from_bytes(data(after['md'],'overview_pacing_error',2),'big')==0
  clock=(int.from_bytes(data(after['md'],'vtimer',4),'big')-int.from_bytes(data(after['md'],'world_clock_shift',4),'big'))&255;assert clock==after['sms'][0x2f]
  assert data(after['md'],'sms_vram',0x3e00)[0x3800:]==read(folders['sms']/f'vram_{4200+offset:05d}.bin')[0x3800:0x3e00]
  a=Image.open(folders['sms']/f'frame_{4200+offset:05d}.png').convert('RGB');b=Image.open(folders['md']/'frame_04200.png').convert('RGB').crop((0,16,256,208));pal=set(a.getdata());conv={v:min(pal,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,(name,diff)
  returns.append(dict(case=name,source_frame=4200+offset,native_frame=4200,same_logical_clock=clock,normalized_pixel_differences=diff,cells_preserved_bytes=160,flags_verified_bytes=256,map_hud_exact_bytes=1536))
  cases.append(dict(case=name,clock_phase_offset=offset,same_physical_clock=offset==0))
 assert len(returns)==18 and images==168
 baseline=json.loads((ROOT/'analysis/overview_clock_baseline271_report.json').read_bytes());assert not baseline['passed'] and not baseline['generation_counter_frozen'] and sum(bool(x['differences']) for x in baseline['pixel_comparisons'])==29
 closing=[]
 for tag in ['close-ntsc','close-pal']:
  es=json.loads((ROOT/f'validation/overview-source-{tag}/events.json').read_bytes());a=next(e for e in es if e[1]==0x3286);bs=[e for e in es if e[1]==0xbb3 and e[2]>a[2]];deltas=[(bs[0][5]-a[5])&255,(bs[1][5]-bs[0][5])&255];assert deltas==[1,1];closing.append(dict(case=tag,closing_counter_steps=deltas))
 cost=json.loads((ROOT/'analysis/world_overview_cost_report.json').read_bytes());assert cost['passed'] and cost['md_sha256']==digest and cost['restore_cells_tstates']==3559 and cost['restore_cells_cases']==5
 for path in ['analysis/loot_lifetime_v0273-health_report.json','analysis/screen_spell_v0273-actors2_report.json','analysis/world_frame_coherence_v0273_report.json']:
  r=json.loads((ROOT/path).read_bytes());assert r['passed'] and r['md_sha256']==digest
 result=dict(md_sha256=digest,source_sha256=source,passed=True,controlled_cases=22,cases=cases,generation_clock_frame_observations=generation_frames,logical_clock_overview_images_exact=images,physical_frame_sample_mismatches=physical_mismatches,return_checks=returns,source_closing_checks=closing,alignment_writes_after_activation=0,baseline_271_same_frame_marker_mismatches=29,full_game_verified=False,physical_clock_exact=False,limits=['One initial clock alignment at2850 and controlled ownership/flags. No post-activation clock or counter injection. Natural global boot phase is not established.','The modal counter holds through construction and advances by source full waits. Some UI/return frames remain one physical frame early, including ordinary PAL; comparisons at the same logical counter are exact.','Initial/closing counter transitions can occur one frame apart while the screen is hidden. Source raster publication, complete restoration timing, RNG and full campaign remain unfinished.'])
 (ROOT/'analysis/overview_clock_release_v0273_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(dict(cases=22,generation_clock_observations=generation_frames,logical_overview_images=images,returns=18,physical_sample_mismatches=physical_mismatches,phase_offsets=sorted({x['clock_phase_offset'] for x in cases})))
if __name__=='__main__':main()
