"""Original8679 M1 count for six priority-bit selections andrest termination."""
from audio_noise_note_cost import noise_note_cost

def noise_note_refresh(state,note,offset=0xd0):
 output=noise_note_cost(state,note,offset);count=0
 for bit in range(6):
  count+=2
  if note&(1<<bit):
   count+=4+(0 if bit==0 else 1)+8
   count+=1 if state[offset]&4 else 6
   output['m1_fetches']=count;return output
  count+=1
 count+=5+(1 if state[offset]&4 else 6);output['m1_fetches']=count;return output
