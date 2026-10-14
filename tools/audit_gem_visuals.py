"""Compare actual gem and reward SAT entries/pixels in captured production VDP state."""
import hashlib,json
from actor_reference import ROOT
from audit_item_reward_visuals import sms_pixels,md_pixels

def entries(v,md=False):
 if not md:
  out=[]
  for n in range(64):
   if v[0x3f00+n]==0xd0:break
   out.append([v[0x3f00+n],v[0x3f80+n*2],v[0x3f81+n*2]])
  return out
 def w(a):return int.from_bytes(bytes([v[a^1],v[(a+1)^1]]),'big')
 out=[];n=0
 for i in range(80):
  a=0xf400+n*8;out.append([(w(a)-145)&255,(w(a+6)-128)&255,(w(a+4)&0x7ff)-272]);n=w(a+2)&127
  if not n:break
 return out

def main():
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();cases=[]
 for region in ['auto','pal']:
  for row in json.loads((ROOT/'analysis/gem_resources.json').read_text())['records']:
   d=row['dungeon'];tile=row['tile'];folders={tag:ROOT/f'validation/gem-{d}-24-{region}-{tag}' for tag in ['sms','md']}
   assert json.loads((folders['md']/'capture.json').read_text())['rom_sha256']==digest
   v={tag:(p/'vram_02803.bin').read_bytes() for tag,p in folders.items()}
   sat={tag:[e for e in entries(v[tag],tag=='md') if e[2]==tile] for tag in folders}
   assert len(sat['sms'])==1 and sat['sms']==sat['md'],(region,d,'gem sprite',sat)
   assert sms_pixels(v['sms'],256+tile)==md_pixels(v['md'],272+tile),(region,d,'gem sprite pixels')
   v={tag:(p/'vram_03100.bin').read_bytes() for tag,p in folders.items()}
   reward={tag:entries(v[tag],tag=='md') for tag in folders}
   assert reward['sms']==reward['md'] and len(reward['sms'])==5,(region,d,'reward SAT',reward)
   cases.append(dict(region=region,dungeon=d,gem_sprite=sat['sms'],gem_pattern_pixels_exact=True,reward_sat=reward['sms']))
 result=dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,full_game_ported=False,limits=['Actual gem SAT/pixels at frame 2803 and complete five-sprite reward SAT at frame 3100 of controlled exterior fixtures.','Neither complete framebuffers nor global rendering/timing and natural dungeon-specific scenes are proved.'])
 (ROOT/'validation/gem_visual_report.json').write_text(json.dumps(result,indent=2)+'\n');print('18 gem sprites/patterns and complete reward sprite lists match original')
if __name__=='__main__':main()
