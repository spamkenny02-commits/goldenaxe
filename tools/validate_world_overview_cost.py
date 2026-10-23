"""Check overview foreground costs against unchanged SMS and compiled C counters."""
import ctypes as c,gzip,json,os,re,subprocess
from run_core import ROOT
from archive_lossless_evidence import sha
from world_overview_cost import room_decode_cost,projection_cost,room_projection_cost,room_loop_tail

def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/world-overview-pacing-v0271';m=json.loads((archive/'manifest.json').read_bytes());i=m['compressed'][path.relative_to(ROOT).as_posix()];encoded=(archive/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'];return raw

def main():
 folder=ROOT/'validation/overview-cost-host';folder.mkdir(exist_ok=True);source=(ROOT/'megadrive/src/world_overview.inc').read_text();begin=source.index('        for(row=0;row<5;row++) for(col=0;col<8;col++)',source.index('for(room_id=0x10'))
 end=source.index('        /* Cumulative source instruction work',begin);body=source[begin:end]
 wrapper='''#include <stdint.h>
#include <string.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
#include "world_overview_assets.inc"
static u8 scratch[2304],sms_vram[5120];
static u8 overview_cell_color(u8 cell) {u8 pair=overview_colors[cell>>1];return (cell&1)?pair&15:pair>>4;}
u32 cost(u16 room_id,u16 flag,u16 ice,const u8 *cells) {u16 row,col,plane;u32 work=11+17+overview_decode_tstates[room_id*4+ice*2+flag]+7+5*(7+4+4+7+12)-5;memcpy(scratch+0x800,cells,160);memset(sms_vram,0,sizeof(sms_vram));
'''+body+'return work;}\n'
 src=folder/'cost.c';src.write_bytes(wrapper.encode());dllpath=folder/'cost.dll';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(ROOT/'megadrive/src'),str(src),'-o',str(dllpath)],env=env,check=True);lib=c.CDLL(str(dllpath));lib.cost.argtypes=[c.c_uint16,c.c_uint16,c.c_uint16,c.POINTER(c.c_uint8)];lib.cost.restype=c.c_uint32
 rom=(ROOT/'input/original.sms').read_bytes();colors=rom[0x84de:0x855e];cases=[];kinds=set()
 for tag,flag,ice in [('base',0,0),('all',1,0),('ice',0,1),('all-ice',1,1),('base-pal',0,0)]:
  path=ROOT/f'validation/overview-source-{tag}';events=json.loads(read(path/'events.json'));snap=read(path/'scenes.bin');pending_room=pending_pixel=None;rooms=pixels=0;total=33;start=stop=None
  for e in events:
   pc=e[1]
   if pc==0x3217:start=e
   if pc==0x3250:stop=e
   if pc==0x3220:pending_room=e
   if pc==0x3223 and pending_room:
    room=pending_room[4];idx=((room>>4)-1)*15+(room&15);raw=snap[idx*8192:(idx+1)*8192];cells=raw[0x1c00:0x1ca0];kinds.add(raw[0x70]);expected,modeled=room_decode_cost(rom,room,flag,ice);observed=((e[2]-pending_room[2])-(e[3]-pending_room[3]))//15;assert observed==17+expected and cells==modeled,(tag,room,observed,expected)
    predicted=11+17+expected+room_projection_cost(cells,colors)+room_loop_tail(room);native=lib.cost(room,flag,ice,(c.c_uint8*160).from_buffer_copy(cells));assert native==predicted,(tag,room,native,predicted);total+=predicted;rooms+=1
   if pc==0x322c:pending_pixel=e
   if pc==0x322f and pending_pixel:
    room=pending_pixel[4];idx=((room>>4)-1)*15+(room&15);cells=snap[idx*8192+0x1c00:idx*8192+0x1ca0];row=pending_pixel[8]&255;col=pending_pixel[8]>>8;observed=((e[2]-pending_pixel[2])-(e[3]-pending_pixel[3]))//15;assert observed==17+projection_cost(cells,colors,row,col),(tag,room,row,col,observed);pixels+=1
  observed=((stop[2]-start[2])-(stop[3]-start[3]))//15;assert observed==total and rooms==225 and pixels==9000,(tag,total,observed,rooms,pixels)
  cases.append(dict(case=tag,room_costs_exact=rooms,pixel_costs_exact=pixels,whole_foreground_tstates=total,first_room_frame=start[0],finished_frame=stop[0],snapshots_sha256=sha(snap)))
 r=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(rom),passed=True,cases=cases,room_cost_cases=1125,pixel_cost_cases=45000,native_C_room_counter_cases=1125,metadata_kinds_observed=sorted(kinds),native_body_sha256=sha(body.encode()),full_game_verified=False,limits=['Read-only observer on unchanged SMS; foreground deltas subtract actual IRQ work. Four all-zero/all-one quest and ice combinations plus PAL baseline.','C counter body is extracted from the production overview; cost tables are generated from original instructions/RLE/metadata, never capture tables.','No proof of source terrain-context5 or global boot/raster/refresh alignment. Runtime IRQ debit uses live native semantic audio work and whole frame quantization.'])
 (ROOT/'analysis/world_overview_cost_report.json').write_bytes((json.dumps(r,indent=2)+'\n').encode());print(dict(rooms=1125,pixels=45000,native_counter_cases=1125,cases=cases,metadata_kinds=sorted(kinds)))
if __name__=='__main__':main()
