"""Bound the source nonzero velocity lifetime before an arena border is reached."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
r=(ROOT/'input/original.sms').read_bytes();vectors=[]
for n in range(8):
 dx=int.from_bytes(r[0x9d86+n*4:0x9d88+n*4],'little',signed=True);dy=int.from_bytes(r[0x9d88+n*4:0x9d8a+n*4],'little',signed=True);assert dx and dy
 ticks=min(math.ceil(176*256/abs(dx)),math.ceil(104*256/abs(dy)))+1
 vectors.append(dict(octant=n,dx=dx,dy=dy,maximum_actor_updates_before_border_callback=ticks))
assert max(v['maximum_actor_updates_before_border_callback'] for v in vectors)==154
for t in [0x4d,0x4e]:assert r[0x320ea+(t-32)*4+3]==0x20
report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(r).hexdigest(),vectors=vectors,source_segment_ticks=32,source_lifetime_segments=128,maximum_segment_decrements_before_border=4,interior_lifetime_expiry_unreachable_under_invariant=True,full_game_ported=False,assumptions=['Initial9C29/9C30 sets one of eight nonzero vectors and lifetime128; border checks precede timer/lifetime checks.','Interior coordinate bounds are40<=X<216 and40<=Y<144, including arbitrary low fixed-point bytes.','Generic surviving hurt preserves velocities because both source stats flags20 exclude knockback08. Freeze/pause does not consume AI lifetime segments; room reload replaces records.','Externally corrupted actor RAM, unsupported mechanics or a forced zero velocity break this invariant; direct routine tests cover only explicit inheritedE0..3 in that forced branch.'])
(ROOT/'validation/dungeon_drain_bounds_report.json').write_text(json.dumps(report,indent=2)+'\n');print('All eight vectors hit a boundary within154 actor updates: at most4 of128 lifetime decrements.')
