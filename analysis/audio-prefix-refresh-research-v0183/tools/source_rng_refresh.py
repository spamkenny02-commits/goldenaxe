"""Original04E1 output from R at entry; no intervening IRQ assumed."""
from source_rng_reference import source_rng

def advance_refresh(value,fetches):
 assert 0<=value<=255 and fetches>=0
 return (value&128)|((value+fetches)&127)

def source_rng_from_entry(seed,entry_refresh):
 #Entry observer is after the first M1 of LD HL,(C028).
 #Remaining pre-read fetches:15,then two for ED5F; fallback adds one.
 transition=source_rng(seed,0);fallback=int(transition['zero_seed_replaced'])
 sampled=advance_refresh(entry_refresh,17+fallback)
 result=source_rng(seed,sampled)
 result.update(sampled_refresh=sampled,refresh_at_RET_entry=advance_refresh(sampled,3),routine_M1_fetches=21+fallback)
 return result
