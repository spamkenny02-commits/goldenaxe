"""Actual source/production reader edge states after prefix integration."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from run_core import run

def main():
 source=(ROOT/'input/original.sms').read_bytes();sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cases=[]
 vectors=[]
 for volume in [0,10,11,12,127,255]:
  r=bytearray(400);r[5]=128;r[11:14]=bytes([2,1,18])
  for a in [0x48,0x78,0xa8,0x18]:r[a]=volume
  vectors.append((f'fade-volume-{volume}',r))
 for command in [0xb5,0xff,0x7f]:
  r=bytearray(400);r[5]=128;r[6]=command;r[0x22]=77;vectors.append((f'priority-{command:02x}',r))
 for pause in [1,128,255]:
  r=bytearray(400);r[5]=7;r[10]=pause;r[0x22]=77;vectors.append((f'pause-{pause}',r))
 for region in ['auto','pal']:
  for name,initial in vectors:
   expected=reader_refresh(source,initial)['state'];records={}
   for tag,cartridge in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    folder=ROOT/f'validation/production-audio-prefix/{name}-{region}-{tag}';result={}
    writes=[(300,0x1e00,bytes(initial))] if tag=='sms' else [(300,sy['sound_ram'],bytes(initial)),(300,sy['sound_request'],bytes(2)),(300,sy['sound_effect_request'],bytes(2))]
    def observe(frame,ram):
     if frame==300:result['state']=bytes(ram[0x1e00:0x1f90]) if tag=='sms' else bytes(ram[(sy['sound_ram']+i)^1] for i in range(400))
    with contextlib.redirect_stdout(io.StringIO()):run(cartridge,300,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    assert result['state']==expected,(region,name,tag,[(i,a,b) for i,(a,b) in enumerate(zip(expected,result['state'])) if a!=b][:10])
    (folder/'reader.bin').write_bytes(result['state']);records[tag]=hashlib.sha256(result['state']).hexdigest()
   cases.append(dict(region=region,name=name,records=records));print(region,name,'source/native400 reader bytes exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,synthetic_state_injection=True,full_game_ported=False,limits=['One aligned IRQ with controlled400-byte reader state; source ROM unchanged. Covers fade wrap/clamp,requests previously filtered atindex>34h,andpause. Does not claim these rare states occur naturally or waveform/fullgame equivalence.'])
 (ROOT/'validation/production_audio_prefix_edges_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
