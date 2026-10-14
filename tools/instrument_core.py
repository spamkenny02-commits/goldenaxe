"""Install a read-only ROM instruction coverage hook in the local GX source checkout.
The instrumented emulator stays in work/; it is never linked into the native port.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c'
source=path.read_text()
marker='/* GAW_RESEARCH_COVERAGE: local modification, instruction-start observations. */'
assert marker not in source, 'Already instrumented'
hook=r'''
/* GAW_RESEARCH_COVERAGE: local modification, instruction-start observations. */
static uint32 gaw_counts[0x40000];
static uint8 gaw_windows[0x40000];
static uint32 gaw_states[256];
__declspec(dllexport) const uint32 *gaw_trace_counts(void) { return gaw_counts; }
__declspec(dllexport) const uint8 *gaw_trace_windows(void) { return gaw_windows; }
__declspec(dllexport) const uint32 *gaw_trace_states(void) { return gaw_states; }
__declspec(dllexport) void gaw_trace_reset(void)
{
  memset(gaw_counts,0,sizeof(gaw_counts));
  memset(gaw_windows,0,sizeof(gaw_windows));
  memset(gaw_states,0,sizeof(gaw_states));
}
static void gaw_observe_instruction(unsigned pc)
{
  uintptr_t fetch=(uintptr_t)(z80_readmap[pc>>10]+(pc&0x3ff));
  uintptr_t base=(uintptr_t)cart.rom;
  if(fetch>=base && fetch<base+0x40000)
  {
    unsigned offset=(unsigned)(fetch-base);
    if(gaw_counts[offset]!=0xffffffff) gaw_counts[offset]++;
    gaw_windows[offset]|=(1<<(pc>>14));
    if(pc==0x00d2 && offset==0x00d2) gaw_states[work_ram[0x1d]]++;
  }
}
'''
source=source.replace('void z80_run(unsigned int cycles)',hook+'\nvoid z80_run(unsigned int cycles)',1)
source=source.replace('    EXEC_INLINE(op,ROP());','    gaw_observe_instruction(PCD);\n    EXEC_INLINE(op,ROP());',1)
path.write_text(source)
print(path)
