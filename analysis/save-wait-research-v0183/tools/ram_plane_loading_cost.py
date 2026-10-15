"""Instruction-count model for original0C00 RAM plane decoder, not VDP RLE032A."""
def ram_plane_cost(rom,source,destination,planes):
 start=source;total=4;ends=[]
 for plane in range(planes):
  address=destination+plane;total+=11+11
  while True:
   command=rom[source];source+=1;total+=7+4
   if not command:total+=12;break
   total+=7+10;literal=bool(command&128);count=(command&127) or 256
   total+=7+4 if literal else 4+6
   for n in range(count):
    if literal:total+=6
    total+=7+7+4+4+4+(12 if (address&255)+planes<256 else 7+4)+(13 if n+1<count else 8)
    address+=planes
    if literal:source+=1
   if not literal:source+=1
   total+=6+12
  ends.append(address);total+=10+10+6+6+(13 if plane+1<planes else 8)
 return dict(tstates=total+10,source_start=start,source_end=source,destination=destination,planes=planes,decoded_bytes=ends[-1]+1-planes-destination)
