"""Extend the audited prefix M1/R plan through class0 graphics return 24B9."""
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase,predict_graphics_prefix_refresh
from graphics_load_phase import predict_graphics_load

def predict_graphics_load_refresh(rom,phase,ram,sound,refresh):
 initial={}
 def prefix_model(*args):
  result=predict_graphics_prefix_refresh(*args,refresh);initial.update(result);return result
 def cpu_factory(*args):
  #New 16/21T nodes remain LDI/LDIR; RAM-plane loops are ordinary opcodes.
  #The two SLA C operations are explicitly annotated in the shared plan.
  class ScopedPhase(GraphicsPrefixRefreshPhase):entry_refresh=initial['refresh']
  return ScopedPhase(*args)
 return predict_graphics_load(rom,phase,ram,sound,cpu_factory=cpu_factory,prefix_model=prefix_model)
