"""Reach the first innkeeper and stay one night through controller input only."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 inputs=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3370,4),(3430,3478,7),(3550,3650,4),(4000,4010,8),(4300,4310,8)]
 a=ROOT/'validation/sms-healer-natural';b=ROOT/'validation/md-healer-natural'
 frames={3900,4200,4500}|set(range(3980,4191))
 with contextlib.redirect_stdout(io.StringIO()):
  run(ROOT/'input/original.sms',4500,a,frames,[(200,220,0)]+inputs)
  run(ROOT/'gaw-megadrive.bin',4500,b,frames,inputs)
 def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
 for frame in [3900,4200,4500]:
  sms=(a/f'ram_{frame:05}.bin').read_bytes();md=native(b,frame)
  for k,o,l in [('game_state',0x1d,1),('hero_health',0x318,1),('hero_magic',0xdb,1),('hero_gold',0xdd,1),('hero_x',0x312,2),('hero_y',0x310,2)]:assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),('natural night',frame,k)
 assert value(native(b,3900),'healer_phase')==1 and value(md,'healer_phase')==0
 source_rest=[f for f in range(3980,4191) if not ((a/f'vdp_regs_{f:05}.bin').read_bytes()[1]&64)]
 target_rest=[f for f in range(3980,4191) if not ((b/f'vdp_regs_{f:05}.bin').read_bytes()[1]&64)]
 assert len(source_rest)==len(target_rest)>=60,('natural night duration',source_rest,target_rest)
 assert source_rest==list(range(source_rest[0],source_rest[-1]+1)) and target_rest==list(range(target_rest[0],target_rest[-1]+1))
 # Whole-path timing is not exact yet: report the observed shift explicitly.
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),no_ram_mutations=True,natural_walk_confirmation_night_exit_verified=True,settled_field_comparisons=18,night_display_duration_source_exact=True,night_display_absolute_interval_source_exact=(source_rest==target_rest),source_night_frame_range=[source_rest[0],source_rest[-1]],native_night_frame_range=[target_rest[0],target_rest[-1]],absolute_interval_offset_frames=target_rest[0]-source_rest[0],night_display_disabled_frames=len(target_rest))
 (ROOT/'validation/healer_natural_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Natural innkeeper/night/exit OK')
if __name__=='__main__':main()
