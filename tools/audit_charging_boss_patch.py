"""Check production scope, literal data and normal charge lifetime invariant."""
import difflib,hashlib,json,re,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';old=(ROOT/'analysis/charging-boss-baseline-v0112/actors.c').read_text();new=(src/'actors.c').read_text();s=new
 a=s.index('extern const u8 charging_boss_walk[]');b=s.index('extern const u8 actor_homing_template[]',a);s=s[:a]+s[b:]
 a=s.index('            else if(entity[0]==0x68 ||');b=s.index('            else if(entity[0]==7)',a);s=s[:a]+s[b:]
 old_condition=next(l for l in old.splitlines() if 'if((entity[0]==0x0f' in l)
 new_condition=next(l for l in s.splitlines() if 'if((entity[0]==0x0f' in l)
 s=s.replace(new_condition,old_condition);assert s==old,'Unrelated actor implementation changed'
 previous=json.loads((ROOT/'versions/v0112-f01b1bee/composite_boss_patch_audit.json').read_text())
 for n in ['main.c','composite_boss_data.c']:assert sha(src/n)==previous['source_files'][n]
 rom=(ROOT/'input/original.sms').read_bytes();resources=(src/'charging_boss_data.c').read_text()
 for name,start,size in [('charging_boss_walk',0x548a,33),('charging_boss_vectors',0x54ab,32),('charging_boss_facing',0x54cb,8),('charging_boss_chase',0x57db,16)]:
  values=re.search(name+r'\[\]=\{([^}]+)',resources)[1];assert bytes(int(v,0) for v in values.split(','))==rom[start:start+size]
 vectors=[(int.from_bytes(rom[a:a+2],'little',signed=True),int.from_bytes(rom[a+2:a+4],'little',signed=True)) for a in range(0x54ab,0x54cb,4)]
 assert all(sorted(map(abs,v))==[171,413] for v in vectors)
 minimum_major_axis_pixels_per_segment=(32*413)//256
 segments_before_boundary=math.ceil(160/minimum_major_axis_pixels_per_segment)
 assert segments_before_boundary==4 and segments_before_boundary<128
 (ROOT/'analysis/charging_boss_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0112/actors.c',tofile='v0113/actors.c')))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','charging_boss_data.c']},only_shared51AE_behavior_dispatch_and_collision_publication_changed=True,main_and_composite_resources_unchanged=True,literal_resources_exact=True,normal_charge_invariant=dict(vectors=vectors,major_axis_pixels_per_32_tick_segment_at_least=minimum_major_axis_pixels_per_segment,interior_maximum_axis_width_pixels=160,boundary_within_at_most_segments=segments_before_boundary,initialized_segment_lifetime=128,assumptions='Normal68/69 state16/rebound velocities remain one of eight source vectors; every active tick checks bounds; normal damage flags40 do not apply knockback; freeze suspends integration and counters. This is not a claim about arbitrary externally forced records or future7A/7B spawning.'),original_random_stream_reproduced=False,full_game_ported=False)
 (ROOT/'validation/charging_boss_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Shared51AE scope/literals verified; normal charge hits boundary within four segments, before interior lifetime expiry')
if __name__=='__main__':main()
