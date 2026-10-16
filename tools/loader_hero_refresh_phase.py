"""Chain original loader through hero using only full16D0 RAM as external state."""
from actor_graphics_refresh_phase import predict_actor_graphics
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from hero_refresh_phase import predict_hero
from world_collision_map import world_collision_map

def predict_loader_hero(rom,phase,initial,sound,refresh):
 assert len(initial)==8192
 mem=bytearray(initial);room=int.from_bytes(mem[0xb9:0xbb],'little');hud=bytes([mem[0x318],*mem[0xda:0xde],*mem[0xcf:0xd8],mem[0xbf],mem[0xf1]])
 prior=predict_actor_graphics(rom,phase,bytes(mem[:80]+mem[0x1d00:0x1e00]),sound,room,hud,refresh,mem[0x1cf0:0x1d00],mem[0x200:0x300]);end=prior['graphics_points'][-1];base=end['prediction']
 class ScopedPhase(GraphicsPrefixRefreshPhase):entry_refresh=base['refresh']
 cpu=ScopedPhase(rom,base['phase'],base['ram'],base['sound']);cpu.execute(10);cpu.execute(17);cpu.checkpoint();start=cpu.result()
 for k in ['wall_master_cycles','foreground_tstates','IRQ_tstates','foreground_M1','IRQ_M1']:start[k]+=base[k]
 start['events']=base['events']+[dict(e,entry_offset_master=e['entry_offset_master']+base['wall_master_cycles']) for e in start['events']]
 mem[:80]=start['ram'][:80];mem[0x1d00:0x1e00]=start['ram'][80:];mem[0x1e00:0x1f90]=start['sound']
 mem[0x65]=0xb0;mem[0x66]=15;mem[0x67]=end['allocated']
 mem[0x90:0xb0]=bytes(32);mem[0xa2]=prior['prior']['actor_points'][-1]['active_count'];mem[0x4b0:0x600]=bytes(336);mem[0x600:0x900]=end['actors']
 history_end=prior['prior']['prior']['history_points'][-1];mem[0x1cf0:0x1d00]=history_end['history'];mem[0x200:0x300]=history_end['flags']
 collision=world_collision_map(rom,room,mem[0x100+room]);mem[0x1600:0x1b00]=collision['tilemap'];before=bytes(mem)
 hero=predict_hero(rom,start['phase'],before,start['sound'],start['refresh']);points={}
 for pc,p in hero.items():
  combined=dict(p)
  for k in ['wall_master_cycles','foreground_tstates','IRQ_tstates','foreground_M1','IRQ_M1']:combined[k]+=start[k]
  combined['events']=start['events']+[dict(e,entry_offset_master=e['entry_offset_master']+start['wall_master_cycles']) for e in p['events']];points[pc]=combined
 return dict(prior=prior,hero_entry=start,hero_entry_ram=before,hero_points=points,collision=collision)
