"""Original1FA7 VRAM clear,0AA4 preparation andpostwait instruction timing plans."""
from foreground_phase import ForegroundPhase
from wait_raster_prediction import predict_save_wait

def rst28(cpu,reg=None,value=0):
 for t,e in [(11,None),(4,'DI'),(4,None),(11,None),(4,None)]:cpu.execute(t,e)
 cpu.execute(11)
 if reg==1:cpu.reg1_write(value)
 elif reg==0:cpu.reg0_write(value)
 cpu.execute(4,'EI');cpu.execute(10)

def clear_prefix(cpu):
 for t in [10,10,10,17]:cpu.execute(t)
 rst28(cpu)
 for t in [4,4,12]:cpu.execute(t)
 for chunk in range(3):
  for word in range(256):
   for t in [4,11,11,10,4,11,4,12 if word<255 else 7]:cpu.execute(t)
  cpu.execute(13 if chunk<2 else 8)
 cpu.execute(10);cpu.execute(17);cpu.checkpoint()

def prepare_prefix(cpu):
 for t in [10,10,10]+[21]*31+[16,17,10,10,10,7]+[21]*30+[16,10,13,4,7]:cpu.execute(t)
 cpu.execute(8,'M1_2') #SET 5,E; unlike an 8T terminal DJNZ.
 rst28(cpu,1,cpu.ram[0x11]|32)
 cpu.execute(11,'status');cpu.execute(17);cpu.checkpoint()

def restore_and_enable(cpu):
 for t in [10,13,14,14,10,10,10,10,4,4,10,10,10,10,10]:cpu.execute(t)
 cpu.checkpoint();restored=cpu.result()
 #AC0: E was saved by0B95 afterSET5 from the prior shadow register.
 value=cpu.ram[0x11]|32|64;cpu.execute(8,'M1_2');rst28(cpu,1,value);cpu.execute(4);cpu.execute(13);cpu.ram[0x11]=value
 for t in [13,4,7]:cpu.execute(t)
 rst28(cpu,0,cpu.ram[0x10]);cpu.checkpoint();return restored

def predict_reveal(rom,phase,ram,sound):
 cpu=ForegroundPhase(rom,phase,ram,sound);clear_prefix(cpu);clear=cpu.result();prepare_prefix(cpu);before_wait=cpu.result()
 wait=predict_save_wait(rom,cpu.phase(),cpu.ram,cpu.sound)
 following=ForegroundPhase(rom,wait['phase'],wait['ram'],wait['sound']);restored=restore_and_enable(following)
 return dict(clear=clear,before_wait=before_wait,wait=wait,restored=restored,after=following.result(),wall_master_cycles=before_wait['wall_master_cycles']+wait['wall_master_cycles']+following.time-following.started)
