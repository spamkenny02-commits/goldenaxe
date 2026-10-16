"""Original audio-only0137..0226 wrapper M1 counts;GPG acknowledge convention explicit."""
from audio_irq_wrapper_cost import audio_irq_wrapper_cost

def audio_irq_wrapper_refresh(delay_nonzero):
 result=audio_irq_wrapper_cost(delay_nonzero)
 stages=dict(gate=3,save_and_map=21,audio_call=1,delay=5 if delay_nonzero else 3,restore=19)
 result['M1_stages']=stages;result['to_return_excluding_reader_M1']=sum(stages.values())
 result['return_instruction_M1']=1
 #Six real vector instructions38/39/3B/3C/3F/42. LocalGPG IM1 accept has noR++.
 result['vector_instructions_M1']=6;result['GPG_acknowledge_M1']=0
 result['whole_IRQ_excluding_reader_M1']=sum(stages.values())+1+6
 return result
