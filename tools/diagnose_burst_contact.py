import contextlib,io,json,re,hashlib
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
source=(ROOT/'input/original.sms').read_bytes()
result={}
for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
 e=bytearray(768);e[0]=0x6b;e[0x18:0x1b]=source[0x320ea+(0x6b-32)*4:0x320ea+(0x6b-32)*4+3];e[3]=0x40
 writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
 if tag=='sms':writes += [(2800,0x310,(144<<8).to_bytes(2,'little')+(224<<8).to_bytes(2,'little')+bytes(4))]
 else:
  for k,v in [('hero_y',144<<8),('hero_x',224<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
 rows={}
 def observe(f,r):
  if not 2940<=f<=2990:return
  def word(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
  h={k:word(k) for k in ['hero_x','hero_y','hero_hurt','hero_health','hero_flags','hero_state','hero_direction','hero_animation','hero_terrain_context']} if tag=='md' else {'record':bytes(r[0x300:0x330]).hex(),'clock':r[0x2f],'terrain':r[0x41]}
  h['actors']= [bytes(r[0x600+n*48:0x630+n*48]).hex() if tag=='sms' else bytes(r[(sy['world_actor_state']+n*48+i)^1] for i in range(48)).hex() for n in range(8,16)]
  if tag=='md':
   h['clock']=(int.from_bytes(bytes(r[(sy['vtimer']+i)^1] for i in range(4)),'big')-int.from_bytes(bytes(r[(sy['world_clock_shift']+i)^1] for i in range(4)),'big'))&255
  rows[f]=h
 with contextlib.redirect_stdout(io.StringIO()):run(rom,2990,ROOT/f'validation/burst-contact-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe)
 result[tag]=rows
(ROOT/'validation/burst_contact_diagnostic.json').write_text(json.dumps(result,indent=2))
first=next(f for f in range(2940,2991) if result['sms'][f]['actors']!=result['md'][f]['actors'])
assert first==2977
assert result['md'][2977]['hero_hurt']==47 and bytes.fromhex(result['sms'][2977]['record'])[5]==0
assert bytes.fromhex(result['sms'][2978]['record'])[5]==47
assert all((result['sms'][f]['clock']-result['md'][f]['clock'])&255==73 for f in range(2940,2977))
report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),region='auto',known_difference=True,first_actor_difference_frame=first,native_contact_frame=2977,source_contact_frame=2978,source_minus_native_postframe_clock_mod256=73,production_clock_modified=False,full_game_ported=False,limits=['Controlled6B encounter in initial exterior; preserves unaligned production clocks. Records the unresolved absolute collision-phase difference separately from clock-aligned actor-logic checks.'])
(ROOT/'validation/burst_contact_phase_report.json').write_text(json.dumps(report,indent=2)+'\n')
print('Unaligned NTSC clock discrepancy retained: MD contact2977, SMS2978; phase delta73')
