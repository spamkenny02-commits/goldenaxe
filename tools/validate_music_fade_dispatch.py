"""Compare original/native87->B0->82 PSG reader under aligned IRQ inputs."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll';rows=[]
 for region in ['auto','pal']:
  records={};PSG={};errors={}
  for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
   states={};registers={};unsupported=[]
   writes=[(300,0x1e04,b'\0'),(300,0x1e06,b'\x87'),(500,0x1e06,b'\xb0'),(800,0x1e06,b'\x82')] if tag=='sms' else [(300,sy['sound_ram']+4,b'\0')]+[(f,sy['sound_request'],v.to_bytes(2,'big')) for f,v in [(300,0x87),(500,0xb0),(800,0x82)]]
   def observe(f,r):
    if f<301:return
    if tag=='sms':states[f]=bytes(r[0x1e00:0x1f90])
    else:
     states[f]=bytes(r[(sy['sound_ram']+i)^1] for i in range(0x190))
     unsupported.append(int.from_bytes(bytes(r[(sy['sound_unhandled_command']+i)^1] for i in range(2)),'big'))
   with contextlib.redirect_stdout(io.StringIO()):
    run(rom,1200,ROOT/f'validation/music-fade-{region}-{tag}',set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,core=core,psg_observer=lambda f,p:registers.update({f:p}),core_options={'genesis_plus_gx_region_detect':region})
   records[tag]=states;PSG[tag]=registers;errors[tag]=unsupported
  indices=list(range(1,5))+list(range(0xb,0xe))+[0x18]+list(range(0x40,0x190))
  for f,a in records['sms'].items():
   b=records['md'][f];assert all(a[i]==b[i] for i in indices),(region,f,[(hex(i),a[i],b[i]) for i in indices if a[i]!=b[i]][:12])
   audible=lambda p:p[:6]+((p[6] if p[7] else 0),p[7])
   assert audible(PSG['sms'][f])==audible(PSG['md'][f]),(region,f,'audible PSG registers')
  assert not any(errors['md'])
  assert records['md'][500][0xb:0xe]==bytes([12,18,18])
  assert records['md'][717][0xb]==0 and records['md'][800][0xb]==0
  retained={}
  for tag in ['sms','md']:
   states=b''.join(records[tag][f] for f in range(301,1201))
   registers=b''.join(v.to_bytes(2,'little') for f in range(301,1201) for v in PSG[tag][f])
   folder=ROOT/f'validation/music-fade-{region}-{tag}'
   (folder/'reader-records.bin').write_bytes(states);(folder/'psg-registers.bin').write_bytes(registers)
   retained[tag]=dict(reader_sha256=hashlib.sha256(states).hexdigest(),PSG_sha256=hashlib.sha256(registers).hexdigest())
  rows.append(dict(region=region,IRQ_records_exact=len(records['sms']),compared_reader_bytes=len(indices),audible_PSG_register_states_exact=len(records['sms']),normal_fade_steps=12,fade_period=18,unsupported_commands=0,retained_tables=retained))
  print(region,'87/B0/82 reader/fade/PSG states exact',len(records['sms']),flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=rows,full_game_ported=False,limits=['Controlled equal-time requests87 at300,B0 at500 and82 at800;60Hz compensation phase aligned at300. Original source ROM unpatched;current production native reader. Fade state,seven channel records and audible PSG registers compare900 IRQ snapshots per region.','Muted noise frequency register excluded as inaudible. No audio waveform/hardware assertion. Actual paid-exit command order is separately tested;its unequal physical loading duration is not normalized by this driver test.'])
 (ROOT/'validation/music_fade_dispatch_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
