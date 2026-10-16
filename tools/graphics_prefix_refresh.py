"""M1/R for the audited class0 16D0..1706 instruction plan only."""
from foreground_phase import ForegroundPhase
from audio_reader_refresh import reader_refresh
from audio_irq_wrapper_refresh import audio_irq_wrapper_refresh
from source_rng_refresh import advance_refresh
from graphics_prefix_phase import predict_graphics_prefix

def audited_fetches(ticks,effect=None):
 assert ticks in [4,5,6,7,8,10,11,12,13,14,15,16,17,19,20,21]
 return 1 if effect=='M1_1' else (2 if ticks in [14,16,19,20,21] or effect=='M1_2' else 1)

class GraphicsPrefixRefreshPhase(ForegroundPhase):
 entry_refresh=None
 def __init__(self,*args):
  super().__init__(*args);assert self.entry_refresh is not None
  self.refresh=self.entry_refresh;self.foreground_M1=0;self.IRQ_M1=0
 def boundary(self):
  before=len(self.events);sound=self.sound;timer=self.ram[0x30]
  super().boundary()
  for event in self.events[before:]:
   audio=reader_refresh(self.rom,sound);wrapper=audio_irq_wrapper_refresh(timer!=0)
   fetches=wrapper['whole_IRQ_excluding_reader_M1']+audio['m1_fetches']
   self.refresh=advance_refresh(self.refresh,fetches);self.IRQ_M1+=fetches
   sound=audio['state'];timer=max(0,timer-1)
  assert sound==self.sound
 def execute(self,ticks,effect=None):
  #Specific to this plan:16/21T are LDI/LDIR;20T is ED53/ED5B.
  #8T is terminal DJNZ unless explicitly marked RES 7,B by the plan.
  fetches=audited_fetches(ticks,effect);first=self.first
  super().execute(ticks,effect)
  self.foreground_M1+=fetches;self.refresh=advance_refresh(self.refresh,fetches-int(first))
 def checkpoint(self):
  super().checkpoint();self.refresh=advance_refresh(self.refresh,1)
 def result(self):
  return dict(super().result(),refresh=self.refresh,foreground_M1=self.foreground_M1,IRQ_M1=self.IRQ_M1)

def predict_graphics_prefix_refresh(rom,phase,ram,sound,refresh):
 class ScopedPhase(GraphicsPrefixRefreshPhase):entry_refresh=refresh
 return predict_graphics_prefix(rom,phase,ram,sound,cpu_class=ScopedPhase)
