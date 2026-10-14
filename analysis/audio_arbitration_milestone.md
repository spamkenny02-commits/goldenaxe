# Predict original8097 audio request arbitration, v0180

An independent state/cost model now handles all three original request slots
DE06/07/08 in order,using ROM priority table8AD5 and current thresholdDE11.
Accepted requests publish their command inDE05 and the masked priority inDE11;
lower priorities are discarded. All slots are cleared even when their masked
request is zero. Equal priorities are accepted,so later slots can replace the
command selected by earlier slots. Instruction counts include the two CALLs
and the third fall-through80A8 execution.

The isolated suite executes unchanged original8097/bank6 with IRQs disabled.
It covers every request byte in each slot with six priority values,and all
14 music/B0 x29 sound effects x29 sound effects xpriority0/1 combinations.
28144 distinct states per region yield56288 exact cost/400-byte RAM matches.
High priorities and invalid high request bytes are explicit synthetic bounds.

The live6D->96/full-mask route captures601 arbitration calls per region,
1202 total. These independently predicted costs and states match the original,
along with2404 tempo/fade calls captured in the same run. Original cycle-event
arrays are identical to the archived v0179 reference. Observers alter neither
the original ROM instructions nor the observed cycle counts.

This component predicts arbitration work from input state;dispatch and channel
processing remain to be modeled before full future audio/IRQ cost prediction.
The production ROM and all production sources remain byte-identicalv0180.
No fixed loading delay or incomplete full-reader prediction has been added.
