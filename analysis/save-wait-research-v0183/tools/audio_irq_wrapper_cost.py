"""Original0137 -> audio-only01E3 ->0226 instruction-derived wrapper costs."""

def audio_irq_wrapper_cost(delay_nonzero):
 gate=13+4+10 # LD A,(C02E),OR A,JP z
 save_and_map=sum([11,11,11,4,4,11,11,11,11,15,15,13,11,13,11,7,13,7,13])
 call=17
 delay=13+4+(7+4+13 if delay_nonzero else 12)
 restore=sum([10,13,10,13,14,14,10,10,10,10,4,4,10,10,10,10,4])
 return dict(gate=gate,save_and_map=save_and_map,audio_call=call,delay=delay,restore=restore,to_return_excluding_reader=gate+save_and_map+call+delay+restore,return_instruction=10,interrupt_accept_and_vector=13+11+11+4+10+13+10)
