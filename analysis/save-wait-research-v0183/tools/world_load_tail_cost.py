"""Original5B20,class0 1CAF and24ED tail costs; hero2C63 is separate."""
def room_script_setup_cost(actor_count):
 total=sum([10,16,16,16,20,20,13,13,7,13,16,11,10,11,7,6,7,20,13,4])
 total+=7+7+13 if actor_count&128 else 12
 return total+10

def world_music_setup_cost(rom,room,previous):
 table=rom[0x1d02:0x1d0d]
 position=next((n+1 for n,value in enumerate(table) if value==room),None)
 total=sum([13,7,7,7,10,10,13])+21*(position or 11)-5+7
 if position is None:total+=12;command=0x82
 else:total+=7+7+12;command=0x84
 total+=10+7+7
 total+=11 if command==previous else 5+13+10
 return dict(foreground_tstates=total,command=command,scope='Original1CAF,class0 world dispatch and1CF8 unchanged-command suppression; other classes excluded.')

def load_return_cost():
 return 7+13+10+10
