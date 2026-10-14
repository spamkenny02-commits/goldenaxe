"""Direct, unconditional door prefixes from bank2 room-script table B762.

Stops at the first instruction outside LD BC / LD E / CALL 6594. This does
not extract later doors through a quest gate or interpret Z80 at runtime.
"""
import json,sys
from actor_reference import ROOT
sys.path.insert(0,str(ROOT.parents[1]/'work/z80dis'))
from z80dis import z80
def main():
 r=(ROOT/'input/original.sms').read_bytes();doors=[];exits=[];dungeon_doors=[];dungeon_exits=[]
 for room in range(256):
  entry=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little');pos=entry
  if room>=16 and room&15!=15:
   while r[pos:pos+1]==b'\x01' and r[pos+3:pos+4]==b'\x1e' and r[pos+5:pos+8]==bytes.fromhex('cd9465'):
    coord=int.from_bytes(r[pos+1:pos+3],'little');x=((coord&63)+6)*4;y=(coord>>6)*8;target=r[pos+4]
    assert x<=240 and y<=160 and not (x|y)&7
    assert target<16 or target&15==15
    doors.append(dict(room=room,x=x,y=y,target=target,script_entry=entry,rom_stub_offset=pos,source_coordinate=coord));pos+=8
   pos=entry
   while r[pos:pos+1]==b'\x01' and r[pos+3:pos+4]==b'\x1e' and r[pos+5:pos+8]==bytes.fromhex('cd6065'):
    coord=int.from_bytes(r[pos+1:pos+3],'little');x=((coord&63)+6)*4;y=(coord>>6)*8;index=r[pos+4]
    assert 0<index<=10 and x<=240 and y<=160 and not (x|y)&7
    target=0x100|r[0x6589+index]
    dungeon_doors.append(dict(room=room,x=x,y=y,index=index,target=target,script_entry=entry,rom_stub_offset=pos,source_coordinate=coord));pos+=8
  elif entry==0x65d0:exits.append(room)
  elif 0xac27<=entry<0xb762:
   # Inspect the fall-through path only, up to its return/jump, on instruction boundaries.
   for _ in range(100):
    if r[pos:pos+3]==bytes.fromhex('cdd065'):exits.append(room);break
    if r[pos] in (0xc9,0xc3,0x18,0xe9):break
    ins=z80.decode(r[pos:pos+8],pos);pos+=ins.len or 1
 lines=['#include <genesis.h>','const u8 world_door_records[][4] = {']
 for d in doors:lines.append('    {0x%02x,%d,%d,0x%02x},'%(d['room'],d['x'],d['y'],d['target']))
 lines+=['};','const u16 world_door_count = %d;'%len(doors),'const u8 world_standard_house_exit[256] = {']
 for start in range(0,256,16):lines.append('    '+','.join(str(int(n in exits)) for n in range(start,start+16))+',')
 for room in range(256,512):
  entry=int.from_bytes(r[0xb762+room*2:0xb764+room*2],'little')
  if entry==0x654d:dungeon_exits.append(room)
 assert len(dungeon_doors)==10 and len(dungeon_exits)==10
 assert {d['target'] for d in dungeon_doors}==set(dungeon_exits)
 lines+=['};','const u16 world_dungeon_door_records[][5] = {']
 for d in dungeon_doors:lines.append('    {0x%02x,%d,%d,0x%03x,%d},'%(d['room'],d['x'],d['y'],d['target'],d['index']))
 lines+=['};','const u16 world_dungeon_door_count = %d;'%len(dungeon_doors),'const u8 world_standard_dungeon_exit[256] = {']
 for start in range(0,256,16):lines.append('    '+','.join(str(int(256+n in dungeon_exits)) for n in range(start,start+16))+',')
 lines+=['};'];(ROOT/'megadrive/src/doors_data.c').write_text('\n'.join(lines)+'\n')
 (ROOT/'analysis/doors_reference.json').write_text(json.dumps(dict(source_room_script_table=0xb762,direct_unconditional_doors=doors,standard_house_exits=exits,direct_unconditional_dungeon_doors=dungeon_doors,standard_dungeon_exits=dungeon_exits,conditional_and_later_script_suffixes_ported=False),indent=2)+'\n')
 print('Direct doors',len(doors),'rooms',len({d['room'] for d in doors}),'standard exits',len(exits))
if __name__=='__main__':main()
