"""Capture actual six-route paid exits with original IRQ/audio instrumentation."""
import json
from actor_reference import ROOT
from profile_paid_passage_loader_phases import main as profile

def main():
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:profile(town,mask,f'audio-irq/{town:02x}-{mask:02x}','genesis_plus_gx_audioirq_libretro.dll',capture_music=True)

if __name__=='__main__':main()
