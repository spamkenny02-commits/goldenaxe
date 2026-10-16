"""M1 fetch counts for original tempo/fade/stop/request arbitration helpers."""
from audio_prefix_cost import tempo_cost,fade_cost,stop_cost
from audio_arbitration_cost import arbitration_cost

def tempo_refresh(state):
 output=tempo_cost(state)
 output['m1_fetches']=4 if not state[1] else 24 if state[1]==1 else 6
 return output

def stop_refresh(state):
 output=stop_cost(state)
 #394 LDIR iterations and10 OTIR iterations each fetch ED+opcode.
 output['m1_fetches']=7+394*2+3+5+10*2+2+4
 return output

def fade_refresh(state):
 output=fade_cost(state)
 if not state[0xb]:count=3
 elif (state[0xc]-1)&255:count=8
 elif state[0xb]==1:count=12+stop_refresh(state)['m1_fetches']
 else:
  volume=lambda value:4 if ((value+1)&255)>=12 else 6
  count=15+sum(3+volume(state[0x48+n*0x30]) for n in range(3))+1+volume(state[0x18])
 output['m1_fetches']=count
 return output

def arbitration_refresh(rom,state):
 output=arbitration_cost(rom,state)
 #DD/FD register/address instructions fetch twice;ordinary instructions once.
 output['m1_fetches']=7+sum({'empty':7,'rejected':16,'accepted':22}[d] for d in output['decisions'])
 return output
