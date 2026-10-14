"""Separate actual source/native loader,fade and contour phases on all six routes."""
import hashlib,json
from actor_reference import ROOT
from class0_graphics_loading_cost import class0_graphics_cost
from full_actor_loading_cost import full_actor_cost
from world_map_loading_cost import world_map_cost
from reveal_loading_cost import reveal_prefix_cost
from profile_paid_passage_loader_phases import main as profile

PHASES=[('graphics',0x16d0,0x24b9),('map',0x24b9,0x24bc),
 ('HUD_wait_palette',0x24bc,0x24bf),('call_setup',0x24bf,0x24c5),
 ('clear_and_room_history',0x24c5,0x1780),('actors',0x1780,0x18e1),
 ('hero_initialization',0x18e1,0x24e7),('room_script_setup',0x24e7,0x24ea),
 ('music_setup',0x24ea,0x24ed),('load_return',0x24ed,0x1fa7),
 ('VRAM_clear',0x1fa7,0x0aa4),('initial_reveal_wait',0x0aa4,0x0ace),
 ('palette_fade',0x0ace,0x1fb6),('contour_reveal',0x1fb6,0x2002)]

def main():
 source=(ROOT/'input/original.sms').read_bytes();rows=[]
 routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']
 for town,target,*_ in routes:
  for mask in [0,255]:
   output=f'paid-passage-transition-matrix/{town:02x}-{mask:02x}'
   profile(town,mask,output,'genesis_plus_gx_transition_libretro.dll')
   folder=ROOT/'validation'/output
   for region in ['auto','pal']:
    event_path=folder/f'{region}-cycle-events.json';events=json.loads(event_path.read_text())
    def phase(start,end):
     a=next(e for e in events if e[1]==start and e[4]==target)
     b=next(e for e in events if e[1]==end and e[2]>a[2])
     foreground=(b[2]-a[2])-(b[3]-a[3]);assert foreground%15==0,(town,mask,region,start,end,foreground)
     return dict(start_frame=a[0],end_frame=b[0],video_frame_boundaries=b[0]-a[0],foreground_tstates=foreground//15,IRQ_master_cycles=b[3]-a[3],begin_clock=a[5],end_clock=b[5])
    phases={name:phase(start,end) for name,start,end in PHASES}
    assert phases['graphics']['foreground_tstates']==class0_graphics_cost(source)['foreground_tstates']
    assert phases['map']['foreground_tstates']==17+world_map_cost(source,target,1)['foreground_tstates']
    assert phases['actors']['foreground_tstates']==full_actor_cost(source,target,mask)['foreground_tstates']
    assert phases['VRAM_clear']['foreground_tstates']==reveal_prefix_cost()['foreground_tstates']
    whole=phase(0x16d0,0x2002)
    assert sum(r['foreground_tstates'] for r in phases.values())==whole['foreground_tstates']
    p=json.loads((folder/f'{region}-profiles.json').read_text());native=p['md'];original=p['sms']
    first=lambda items,predicate:next(int(f) for f,r in items.items() if predicate(r))
    native_fade=first(native,lambda r:r['resume_phase']==3)
    native_contour=first(native,lambda r:r['resume_phase']==4)
    native_idle=next(int(f) for f,r in native.items() if int(f)>native_contour and r['resume_phase']==0 and r['hero'][0]==1)
    source_idle=next(int(f) for f,r in original.items() if int(f)>=whole['end_frame'] and r['hero'][0]==1)
    row=dict(town=town,target=target,mask=mask,region=region,source_phases=phases,source_whole_loading_and_reveal=whole,source_first_idle=source_idle,native_first_fade=native_fade,native_first_contour=native_contour,native_first_idle=native_idle,native_idle_frame_gap=native_idle-source_idle,raw_events_path=str(event_path.relative_to(ROOT)),raw_events_sha256=hashlib.sha256(event_path.read_bytes()).hexdigest())
    rows.append(row)
    print('Transition phases',hex(town),hex(target),mask,region,'native idle gap',row['native_idle_frame_gap'],flush=True)
 report=dict(diagnostic_only=True,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=len(rows),rows=rows,full_game_ported=False,limits=[
  'Actual unpatched source paid exits; six routes,empty/full destination masks,PAL/NTSC. Initial entrance/hero/clock and pre-entry persistence controlled; no RNG or post-load actor injection. Native ROM v0176 remains unchanged during all captures.',
  'Four previously instruction-derived components independently match96 live comparisons. Fourteen contiguous source intervals telescope to total loading/reveal foreground work; interrupts and frame boundaries are recorded separately.',
  'Empty rooms now find idle by room arrival/hero state,not actor slot0 existence. Native fade/contour stage fields are observations at frame boundaries,not exact sub-frame PC timestamps.',
  'Orchestration costs,RNG/refresh,IRQ alignment and global/natural transition fidelity are still not modeled or asserted equal. This is diagnostic evidence,not a calibrated wait table.'])
 (ROOT/'analysis/paid_passage_transition_matrix_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(len(rows),'actual paid transition phase profiles collected',flush=True)

if __name__=='__main__':main()
