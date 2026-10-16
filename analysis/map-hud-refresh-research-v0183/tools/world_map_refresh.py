"""Compose graphics and map M1/R from a single 16D0 entry state."""
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from graphics_load_refresh import predict_graphics_load_refresh
from world_map_phase import predict_world_map

def predict_world_map_refresh(rom,phase,ram,sound,room,refresh,flags=1):
 initial={}
 def graphics_model(*args):
  points=predict_graphics_load_refresh(*args,refresh);initial.update(points[0x24b9]);return points
 def cpu_factory(*args):
  class ScopedPhase(GraphicsPrefixRefreshPhase):entry_refresh=initial['refresh']
  return ScopedPhase(*args)
 return predict_world_map(rom,phase,ram,sound,room,flags,cpu_factory=cpu_factory,graphics_model=graphics_model)
