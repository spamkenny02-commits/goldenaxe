"""Check source/native transition loading with different persistent enemy masks."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT,load_room_actors
from actor_loading_cost import resource_cost
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rom=(ROOT/'input/original.sms').read_bytes();cases=[]
 for region in ['auto','pal']:
  for mask in [255,240,128,8]:
   values={};final={}
   for tag,path,offset in [('sms',ROOT/'input/original.sms',0x200+0xa4),('md',ROOT/'gaw-megadrive.bin',sy['game_save_state']+0x150+0xa4)]:
    states=[]
    def observe(frame,d):
     if frame<3040:return
     if tag=='sms':state=d[0x1d];room=int.from_bytes(d[0xb9:0xbb],'little')
     else:state=int.from_bytes(d[sy['game_state']:sy['game_state']+2],'little');room=int.from_bytes(d[sy['room_id']:sy['room_id']+2],'little')
     if state==10:states.append(frame)
     if frame==3160:
      final[tag]=(d[0xa2],d[0x67]) if tag=='sms' else tuple(int.from_bytes(d[sy[k]:sy[k]+2],'little') for k in ['world_actor_count','world_actor_tiles'])
      if tag=='md':final['cost']=int.from_bytes(d[sy['world_actor_load_tstates']+2:sy['world_actor_load_tstates']+4],'little')+(int.from_bytes(d[sy['world_actor_load_tstates']:sy['world_actor_load_tstates']+2],'little')<<16)
    folder=ROOT/f'validation/loading-{region}-{mask:02x}-{tag}'
    with contextlib.redirect_stdout(io.StringIO()):run(path,3160,folder,set(),([(200,220,0)] if tag=='sms' else [])+PRESSES,ram_writes=[(3040,offset,bytes([mask]))],ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    values[tag]=[min(states),max(states),len(states)]
   resources=load_room_actors(rom,0xa4,persistence=mask)[4]
   expected=sum(resource_cost(rom,dict(e,tile_base=0))['foreground_graphics_tstates'] for e in resources)
   assert final['sms']==final['md'],(region,mask,'allocation',final)
   assert final['cost']==expected,(region,mask,'work metadata',final['cost'],expected)
   if mask==255:assert values['sms']==values['md'],(region,'natural route timing')
   cases.append(dict(region=region,persistence_mask=mask,unique_resources=[e['type'] for e in resources],expected_nominal_graphics_tstates=expected,native_graphics_tstates=final['cost'],transition_frames=values,native_minus_source_completion_frames=values['md'][1]-values['sms'][1],actor_count_and_tile_allocation_exact=True))
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,scope='Room94->A4, four persistence masks in PAL/NTSC. Resources count once per unique surviving type; no constant room-specific delay.',general_interrupt_budget_exact=False,source_rng_reproduced=False)
 (ROOT/'validation/loading_budget_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
