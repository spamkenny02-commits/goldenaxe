"""Compare phase-to-VCounter mapping against actual local GPG counter function."""
import ctypes as c,hashlib,json
from actor_reference import ROOT
from irq_raster_phase import vertical_counter

def main():
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_vcounteroracle_libretro.dll';dll=c.CDLL(str(core));dll.gaw_test_vcounter.argtypes=[c.c_uint]*4;dll.gaw_test_vcounter.restype=c.c_uint
 deltas=sorted(set(range(0,3766,15))|{1,14,16,3419,3421,3434,3436,3764});rows=[]
 for lines,overflow in [(262,0xda),(313,0xf2)]:
  result=bytearray()
  for line in range(lines):
   for delta in deltas:
    actual=dll.gaw_test_vcounter(line,delta,lines,overflow);predicted=vertical_counter(line*3420+delta,lines,overflow)
    assert actual==predicted,(lines,line,delta,actual,predicted);result.append(actual)
  rows.append(dict(lines=lines,overflow=overflow,cases=len(result),results_sha256=hashlib.sha256(result).hexdigest()));print(lines,len(result),'counter mappings exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Calls unchanged local GPG vdp_hvc_r through isolated wrapper with controlled VC,linecycles,frame length/overflow,noninterlaced mode4. Globals saved/restored. HCounter latch forced only to avoid reading an uninitialized HCounter table;vertical counter remains running. No emulated ROM instruction changed.','All262/313 scanlines,every15-master-cycle phase through3765 plusselected1-clock boundary neighbors. Includes one-line instruction overrun,frame wrap andVC discontinuities.','This verifies the local emulator counter model,not physical SMS hardware or every possible master-cycle phase/VDP mode.'])
 (ROOT/'analysis/vcounter_phase_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
