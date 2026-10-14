"""Read-only cycle/events hook for the research GX build, not for the native cartridge."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c'
s=p.read_text();marker='/* GAW_RESEARCH_TIMING */'
if marker not in s:
 (ROOT.parents[1]/'work/z80-before-timing.txt').write_text(s)
 hook=r"""
/* GAW_RESEARCH_TIMING */
static unsigned long long gaw_elapsed, gaw_irq_elapsed;
static unsigned gaw_irq_active, gaw_event_count;
static unsigned gaw_irq_sp[32];
static unsigned long long gaw_events[32768][8];
__declspec(dllexport) const unsigned long long *gaw_timing_events(void) { return &gaw_events[0][0]; }
__declspec(dllexport) unsigned gaw_timing_count(void) { return gaw_event_count; }
__declspec(dllexport) void gaw_timing_reset(void) { gaw_elapsed=gaw_irq_elapsed=0;gaw_event_count=gaw_irq_active=0; }
static void gaw_timing_observe(unsigned pc)
{
  if(pc==0x24c5 || pc==0x1780 || pc==0x18ac || pc==0x032a || pc==0x1d0d || pc==0x18e1 || pc==0x18b7 || pc==0x24ed || pc==0x24f2 || pc==0x20d3 || pc==0x0c98 || pc==0x0b56 || pc==0x1473 || pc==0x1487 || pc==0x148d || pc==0x1493 || pc==0x1499 || pc==0x14cf || pc==0x14d2 || pc==0x14d5 || pc==0x14da || pc==0x0bd3 || pc==0x0bfe || pc==0x0c9b || pc==0x0caa || pc==0x0cbd || pc==0x0cc9 || pc==0x0cd5 || pc==0x0cdd || pc==0x0ce0 || pc==0x0cfc || pc==0x0cff || pc==0x0e4a || pc==0x0e54 || pc==0x0e57 || pc==0x0e5d || pc==0x0e60 || pc==0x0e66 || pc==0x0e72 || pc==0x0e83 || pc==0x0ea0 || pc==0x0ea4)
  {
    unsigned long long *e;
    if(gaw_event_count>=32768) return;
    e=gaw_events[gaw_event_count++];e[0]=pc;e[1]=gaw_elapsed;e[2]=gaw_irq_elapsed;
    e[3]=work_ram[0xb9]|(work_ram[0xba]<<8);e[4]=work_ram[0x2f];e[5]=HLD;e[6]=DED;e[7]=BCD;
  }
}
"""
 s=s.replace('void z80_run(unsigned int cycles)',hook+'\nvoid z80_run(unsigned int cycles)',1)
 s=s.replace('      take_interrupt();','      unsigned before_irq=Z80.cycles, before_sp=SP;\n      take_interrupt();\n      gaw_elapsed+=Z80.cycles-before_irq;gaw_irq_elapsed+=Z80.cycles-before_irq;if(SP!=before_sp && gaw_irq_active<32) gaw_irq_sp[gaw_irq_active++]=before_sp;',1)
 s=s.replace('    gaw_observe_instruction(PCD);\n    EXEC_INLINE(op,ROP());','    gaw_observe_instruction(PCD);\n    { unsigned before=Z80.cycles,pc=PCD;\n      gaw_timing_observe(pc);EXEC_INLINE(op,ROP());\n      gaw_elapsed+=Z80.cycles-before;if(gaw_irq_active) gaw_irq_elapsed+=Z80.cycles-before;\n      if(gaw_irq_active && SP==gaw_irq_sp[gaw_irq_active-1]) gaw_irq_active--;\n    }',1)
 p.write_text(s)
print(p)
