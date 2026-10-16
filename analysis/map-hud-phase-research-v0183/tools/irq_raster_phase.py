"""SMS mode4/192-line vertical counter and palette polling from entry raster phase."""
def vertical_counter(raster_master,lines,overflow):
 assert (lines,overflow) in [(262,0xda),(313,0xf2)]
 line=(raster_master//3420)%lines
 return (line if line<=overflow else line-lines)&255

def predict_palette_wait(phase,pre_palette_tstates,skip,compensation):
 cpu,line,line_master,lines,overflow,interlaced,reg1,hardware=phase
 assert hardware in [0x20,0x21]
 assert not interlaced and not reg1&4 and 0<=line<lines
 assert (lines,overflow) in [(262,0xda),(313,0xf2)]
 if skip:return dict(taken=0,exits=0)
 delta=((cpu-line_master+0x80000000)&0xffffffff)-0x80000000
 raster=line*3420+delta
 prefix=13+4+7+10+13+4+(12 if compensation else 7+4)
 #GPG adds the complete IN instruction's11T before reading the SMS VCounter.
 sample=raster+(pre_palette_tstates+prefix+11)*15;threshold=0xe0 if compensation else 0xf0
 for taken in range(8192):
  value=vertical_counter(sample,lines,overflow)
  if value>=threshold:return dict(taken=taken,exits=1,first_sample_master=raster+(pre_palette_tstates+prefix+11)*15,exit_sample_master=sample,exit_counter=value,threshold=threshold)
  sample+=(11+4+12)*15
 raise ValueError('Palette polling exceeds a frame-scale bound')
