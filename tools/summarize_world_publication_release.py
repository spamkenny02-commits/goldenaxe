"""Bind the playable publication release to its source/render/timing gates."""
import json
from run_core import ROOT
from validate_sprite_scene_timed import sha

def main():
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom);reports={}
 def checked(name):
  path=ROOT/name;raw=path.read_bytes();r=json.loads(raw);assert r['md_sha256']==digest,(name,'different ROM');reports[name]=sha(raw);return r
 coherence=checked('analysis/world_frame_coherence_v0218_report.json');assert coherence['passed'] and len(coherence['cases'])==12 and all(not c['differing_pixels'] and not c['audio_unhandled_command'] and c['queued_tile_jobs']<=68 for c in coherence['cases'])
 end=checked('analysis/playable_sprite_end_v0218_report.json');assert end['release_accepted'] and len(end['cases'])==4 and all(c['frames']==10 for c in end['cases'])
 limit=checked('analysis/playable_sprite_limit_v0218_report.json');assert len(limit['cases'])==2 and all(c['overflow_frames']==12 for c in limit['cases'])
 scroll=checked('analysis/world_publish_regression_v0218_report.json');assert scroll['passed'] and len(scroll['cases'])==4 and sum(len(c['transitions']) for c in scroll['cases'])==10
 assert all(not any(t['post_completion_differences']) for c in scroll['cases'] for t in c['transitions'])
 source_steps=[s for c in scroll['cases'] for s in c['source_scroll_cadence']];assert len(source_steps)==4
 assert all(s['native_publication_minus_source_completion_frames']==0 and s['native_intervals']==s['source_intervals']==[1]*19 for s in source_steps)
 inventory=checked('validation/inventory_restore_report.json');assert len(inventory['cases'])==6
 for suffix in ['', '-pal']:
  intro=checked('validation/intro'+suffix+'_report.json');assert len(intro['story_lines'])==65 and intro['no_accumulating_text_delay'] and intro['title_returns_after_intro']
 menu=checked('validation/natural_start_menu_sfx_report.json');assert len(menu['cases'])==4 and menu['same_choice_presses_silent']
 timing=[]
 for suffix in ['', '_ntsc']:
  path=ROOT/('analysis/sprite_publish_timing'+suffix+'_report.json');r=json.loads(path.read_bytes());reports[path.relative_to(ROOT).as_posix()]=sha(path.read_bytes());target=next(c for c in r['results'] if c['label']=='v0218');assert target['rom_sha256']==digest;groups=[g for g in target['groups'] if g['kind'].startswith('sat')];assert len(groups)==5 and all(g['kind']=='sat-dma' and g['first_line']>=224 and g['last_line']>=224 for g in groups);timing.append(dict(region='auto' if suffix else 'pal',transfers=len(groups),last_scanline=max(g['last_line'] for g in groups)))
 source=ROOT/'analysis/source_scroll_cadence_report.json';reports[source.relative_to(ROOT).as_posix()]=sha(source.read_bytes())
 assert int.from_bytes(rom[0x18e:0x190],'big')==sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 result=dict(md_sha256=digest,rom_bytes=len(rom),checksum=f'{int.from_bytes(rom[0x18e:0x190],"big"):04X}',reports=reports,sources={n:sha((ROOT/n).read_bytes()) for n in ['megadrive/src/main.c','megadrive/src/sound.inc','megadrive/src/actors.c']},sat_publication=timing,coherent_rgb_pixels=12*51200,source_vertical_steps_verified=4*20,inventory_routes=6,intro_lines_verified=130,menu_sfx_routes=4,passed=True,limits=['Playable integration, not a diagnostic kernel. Gates cover listed initial routes only. Provisional native PRNG and full source R/timing evolution remain incomplete; NPC chronology and other scenes are not declared identical. Sprite/clone/UI publication outside the normal world wait path retains its existing immediate behavior. No whole-game, hardware console or waveform equivalence claim.'])
 (ROOT/'analysis/world_publication_v0218_report.json').write_text(json.dumps(result,indent=2)+'\n');print('v0218 release gates passed:',digest)
if __name__=='__main__':main()
