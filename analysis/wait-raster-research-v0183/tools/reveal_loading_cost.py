"""Instruction-derived original0397 word fill and1FA7 reveal prefix."""
def word_fill_cost(count):
 assert 0<=count<=65535
 words=count or 65536;chunks=(words+255)//256
 # RST28 includes DI,VDP control writes,EI and RET; no wait is introduced.
 rst28=sum([11,4,4,11,4,11,4,10])
 prefix=rst28+4+4+(12 if count%256==0 else 7+4)
 #039D..03A6 emits two bytes with PUSH/POP pacing,then DJNZ per chunk.
 body=words*sum([4,11,11,10,4,11,4,12])-5*chunks
 total=prefix+body+chunks*13-5+10
 return dict(foreground_tstates=total,words=words,bytes=words*2,scope='Original0397,RST28 and paced two-byte writes; BC0000 deliberately means65536 words. IRQ work excluded.')

def reveal_prefix_cost():
 clear=word_fill_cost(0x300)
 return dict(foreground_tstates=10+10+10+17+clear['foreground_tstates']+17,clear=clear,scope='Original1FA7 entry to0AA4 entry: clear768 VRAM words,then CALL0AA4. Initial wait/fade/contours outside interval.')

def reveal_prepare_cost_excluding_save_spin():
 #0AA4..0ACE copies the palette,clears current colors,enables display and
 #waits once. Exclude0B95..0BB3,retain its register restore and caller CALL.
 rst28=sum([11,4,4,11,4,11,4,10])
 copy=10+10+10+31*21+16
 clear=17+10+10+10+7+30*21+16+10
 before_wait=sum([13,4,7,8,rst28,11,17])
 restore=sum([10,13,14,14,10,10,10,10,4,4,10,10,10,10,10])
 after_wait=sum([8,rst28,4,13,13,4,7,rst28])
 return copy+clear+before_wait+restore+after_wait
