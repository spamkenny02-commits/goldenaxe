"""Compare legacy loot expiry failure against v0141 without changing production ROM."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 base=ROOT/'versions/v0141-51ff11b9';ref=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();loot=bytearray(336)
 for slot in range(7):loot[slot*48]=8;loot[slot*48+0x11]=32+slot*16;loot[slot*48+0x13]=32+slot*28
 traces={};folders={}
 for tag,rom,syfile in [('sms',ROOT/'input/original.sms',None),('baseline',base/'gaw-megadrive-v0141.bin',base/'symbol.txt'),('current',ROOT/'gaw-megadrive.bin',ROOT/'megadrive/out/release/symbol.txt')]:
  sy={} if syfile is None else {m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in syfile.read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
  sw=[(3741,0x4b0,bytes(loot)),(3741,0x600,bytes(768)),(3741,0x310,(0x7000).to_bytes(2,'little')+(0x8800).to_bytes(2,'little'))] if tag=='sms' else [(3741,sy['world_loot_state'],bytes(loot)),(3741,sy['world_actor_state'],bytes(768)),(3741,sy['hero_x'],(0x8800).to_bytes(2,'big')),(3741,sy['hero_y'],(0x7000).to_bytes(2,'big')),(3741,sy['vtimer'],int(ref[0x2f]).to_bytes(4,'big'))]
  rows={}
  def observe(f,r):
   if 3741<=f<=4110:rows[f]=bytes(r[0x4b0:0x600]) if tag=='sms' else bytes(r[(sy['world_loot_state']+i)^1] for i in range(336))
  folder=ROOT/f'validation/loot-expiry-diagnostic-{tag}'
  with contextlib.redirect_stdout(io.StringIO()):run(rom,4110,folder,{3984,3985,3986},([(200,220,0)] if tag=='sms' else [])+PRESSES,ram_writes=sw,ram_observer=observe)
  traces[tag]=rows;folders[tag]=folder
 assert traces['sms']==traces['current']==traces['baseline']
 differences=[]
 for f in [3984,3985,3986]:
  a=Image.open(folders['sms']/f'frame_{f:05}.png').convert('RGB');colors=set(a.getdata());counts={};imgs={}
  for tag in ['baseline','current']:
   b=Image.open(folders[tag]/f'frame_{f:05}.png').convert('RGB').crop((0,16,256,208));imgs[tag]=b.tobytes();conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};counts[tag]=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()))
  differences.append(dict(frame=f,source_pixel_differences=counts,native_baseline_and_current_pixels_identical=imgs['baseline']==imgs['current']))
 assert all(x['native_baseline_and_current_pixels_identical'] for x in differences),differences
 assert differences[1]['source_pixel_differences']==dict(baseline=105,current=105),differences
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),baseline_md_sha256=hashlib.sha256((base/'gaw-megadrive-v0141.bin').read_bytes()).hexdigest(),all_370_loot_record_frames_exact_for_source_baseline_and_current=True,samples=differences,legacy_full_expiry_visual_validator_passed=False,full_game_ported=False,limits=['Inherited pre-thief expiry visual gap at3985 under legacy controlled fixture, which writes vtimer from an old source clock snapshot.','All336 loot bytes over370 expiry frames compare. Only three images near the first legacy failure are compared to the prior ROM; complete expiry framebuffer fidelity is not proved.'])
 (ROOT/'validation/loot_expiry_regression_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print('370 loot records exact; prior/current images identical near legacy105-pixel expiry gap.')
if __name__=='__main__':main()
