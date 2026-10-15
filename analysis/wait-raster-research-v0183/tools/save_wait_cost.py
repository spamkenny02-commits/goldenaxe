"""Original0B95..0BB3 instruction work with explicit observed branch decisions."""
def save_wait_cost(taken,exits=1):
 assert taken>=0 and exits==1
 saves=8*11+4+4+15+15+13+11+7+13
 enable=4;loop=taken*(13+4+12)+(13+4+7)
 return dict(prefix_before_EI=saves,foreground_tstates=saves+enable+loop,saved_stack_bytes=22,scope='Observed loop count is an input;IRQ work and future raster/interrupt phase are not predicted.')
