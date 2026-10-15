"""Instruction-derived24C5 prefix and1C15 class0 recent-room handling."""
from source_rng_reference import source_rng

def cpir_cost(position):
 assert position is None or 1<=position<=16
 return (position or 16)*21-5

def world_history_attempt_cost(history_position,random_position,seed,flag_nonzero=True):
 total=13+10+10+cpir_cost(history_position)
 if history_position is None:
  total+=7+10+10+10+(14*21+16)+13
 else:total+=12
 total+=17+source_rng(seed,0)['foreground_tstates']+10+10+cpir_cost(random_position)
 if random_position is not None:return total+11
 total+=5+12+4+7+7+4
 return total+(11 if flag_nonzero else 5+10+10)

def clear_and_history_cost(attempts):
 assert len(attempts)==3
 parts={}
 parts['clear30_and335_bytes']=sum([10,10,10,7,30*21+16,10,10,10,10,334*21+16])
 body=sum([13,4,7,7])+sum(11+17+world_history_attempt_cost(**a)+10+13 for a in attempts)-5+10
 parts['history']=17+body
 parts['call_actor_loader']=17
 return dict(foreground_tstates=sum(parts.values()),components=parts,scope='Original24C5 entry to1780 entry,class0 three1C25 attempts. Branch inputs include 1-based CPIR match positions (None=miss),RNG seed and persistence-byte zero state. Refresh output is not predicted.')
