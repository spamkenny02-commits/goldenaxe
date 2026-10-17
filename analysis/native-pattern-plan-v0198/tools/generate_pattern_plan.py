"""Compile immutable032A ROM bytes and audited command work into native assets."""
import hashlib,json
from actor_reference import ROOT
from validate_native_patterns import Trace
from graphics_prefix_phase import pattern_rle

def generate():
 rom=(ROOT/'input/original.sms').read_bytes();offset=0x3c010;lines=['#ifndef GAW_PATTERN_PLAN_GENERATED_H','#define GAW_PATTERN_PLAN_GENERATED_H','#include "source_pattern_clock.h"'];rows=[]
 for plane in range(4):
  start=offset;cursor=0x4000+plane;ticks=fetches=0;decoded=bytearray();boundaries=[[0,0,0,0]]
  while rom[offset]:
   command_start=offset;command=rom[offset];offset+=1;count=command&127 or 256;literal=command&128;carry=((cursor&255)+count*4)>>8
   ticks+=44+count*(135 if literal else 134)-carry-5+(16 if literal else 29)
   fetches+=9+count*(19 if literal else 18)+carry+(2 if literal else 4)
   for n in range(count):
    decoded.append(rom[offset]);offset+=bool(literal)
   if not literal:offset+=1
   isolated=Trace(rom[command_start:offset]+bytes(4));empty=Trace(bytes(4))
   pattern_rle(isolated,0,cursor);pattern_rle(empty,0,cursor)
   assert isolated.foreground_tstates-empty.foreground_tstates==ticks-boundaries[-1][0]
   assert isolated.fetches-empty.fetches==fetches-boundaries[-1][1]
   cursor=(cursor+count*4)&65535;boundaries.append([ticks,fetches,offset-start,len(decoded)])
  offset+=1
  lines.append('static const SourcePatternBoundary gaw_pattern_bounds'+str(plane)+'[]={'+','.join('{'+','.join(str(v)+'UL' if n<2 else str(v) for n,v in enumerate(b))+'}' for b in boundaries)+'};')
  lines.append('static const u8 gaw_pattern_decoded'+str(plane)+'[]={'+','.join(map(str,decoded))+'};')
  rows.append(dict(commands=len(boundaries)-1,decoded=len(decoded),packed=offset-start,tstates=ticks,m1=fetches,decoded_sha256=hashlib.sha256(decoded).hexdigest()))
 lines.append('static const SourcePatternPlan gaw_class0_pattern_plan={{'+','.join('{gaw_pattern_bounds'+str(n)+',gaw_pattern_decoded'+str(n)+','+str(rows[n]['commands'])+'}' for n in range(4))+'}};')
 lines.append('#endif');header=ROOT/'megadrive/src/source_pattern_plan_generated.h';content='\n'.join(lines)+'\n'
 if not header.exists() or header.read_text()!=content:header.write_text(content)
 report=dict(individual_commands_checked_against_instruction_model=sum(r['commands'] for r in rows),source_sha256=hashlib.sha256(rom).hexdigest(),offset=0x3c010,packed=offset-0x3c010,planes=rows,header_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),limits=['ROM-derived decoded assets and exact032A command-boundary T/M1 prefix sums only; no captured phases or runtime delays.','No plane setup,terminator or plane-end costs in command prefix sums; those remain in native execution.'])
 (ROOT/'analysis/pattern_plan_assets_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Generated',sum(r['commands'] for r in rows),'command boundaries and',sum(r['decoded'] for r in rows),'decoded bytes.')
 return report
if __name__=='__main__':generate()
