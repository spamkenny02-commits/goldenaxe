"""Read-only gatedIRQ M1/R stage/entry-raster snapshots alongside original records."""
import subprocess,sys
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/full-irq-refresh-v0183';folder.mkdir(exist_ok=True);path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes()
 source=(ROOT/'analysis/full-irq-v0183/z80-full-irq.txt').read_text();anchor='#define R Z80.r';assert source.count(anchor)==1
 source=source.replace(anchor,'static unsigned long long gaw_M1_fetches;\n'+anchor);assert source.count('R++;')==5;source=source.replace('R++;','R++;gaw_M1_fetches++;')
 anchor='R += (cycles / cyclesum) * opcodes;';assert source.count(anchor)==1;source=source.replace(anchor,anchor+'gaw_M1_fetches += (cycles / cyclesum) * opcodes;')
 anchor='static unsigned gaw_full_count,gaw_full_active,gaw_full_nested;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'''
struct gaw_full_M1_record { unsigned long long points[10];unsigned refresh[10],phase[8]; };
static struct gaw_full_M1_record gaw_full_M1[8192];
__declspec(dllexport) const unsigned char *gaw_full_irq_m1_events(void) { return (const unsigned char *)gaw_full_M1; }
''')
 anchor='struct gaw_full_record *e=gaw_full_records+gaw_full_count;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\n struct gaw_full_M1_record *m=gaw_full_M1+gaw_full_count;')
 anchor='memset(e,0,sizeof(*e));gaw_full_active=1;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'''
  memset(m,0,sizeof(*m));m->points[0]=gaw_M1_fetches;m->refresh[0]=(R&127)|R2;
  m->phase[0]=Z80.cycles;m->phase[1]=v_counter;m->phase[2]=mcycles_vdp;m->phase[3]=lines_per_frame;
  m->phase[4]=vc_max;m->phase[5]=interlaced;m->phase[6]=reg[1];m->phase[7]=system_hw;
''')
 for slot,pc in enumerate([0x164,0x16d,0x170,0x173,0x199,0x19c,0x1a2,0x1a5],1):
  anchor=f'case 0x{pc:04x}:';assert source.count(anchor)==1;source=source.replace(anchor,anchor+f'm->points[{slot}]=gaw_M1_fetches;m->refresh[{slot}]=(R&127)|R2;')
 anchor='case 0x01e2:';assert source.count(anchor)==1;source=source.replace(anchor,anchor+'m->points[9]=gaw_M1_fetches;m->refresh[9]=(R&127)|R2;')
 modified=source.encode();target=folder/'z80-full-irq-refresh.txt'
 if target.exists():assert target.read_bytes()==modified
 else:target.write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_fullirqrefresh_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (ROOT/'validation/full-irq-refresh-core-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 print('FullIRQ M1/R/stage observer built;original source restored.')
if __name__=='__main__':main()
