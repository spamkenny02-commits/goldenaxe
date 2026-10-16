"""Original04E1 seed transition and cost; refresh-register output stays explicit."""
def source_rng(seed,refresh):
 assert 0<=seed<=65535 and 0<=refresh<=255
 high,low=seed>>8,seed&255
 def rrc(value):return (value>>1)|((value&1)<<7)
 a=rrc(rrc(high))^high;a=rrc(a)^low
 for _ in range(4):a=rrc(a)
 a^=low;carry=a&1
 next_seed=((seed<<1)+carry)&65535;zero=not next_seed
 if zero:next_seed=0x733c
 #130T normal branch; zero fallback replaces taken JR12 by JR7+LDHL10.
 cost=sum([16,4,8,4,4,4,16,4,4,15,12,9,4,16,10])+(5 if zero else 0)
 return dict(seed=next_seed,value=refresh^(next_seed&255),foreground_tstates=cost,zero_seed_replaced=zero)
