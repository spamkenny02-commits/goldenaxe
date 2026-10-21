"""Read-only completed native VRAM write observer for sprite publication."""
import json,subprocess,sys
from game_sprite_frame_fixture import ROOT
from validate_sprite_scene_timed import sha
OBSERVER=r'''
static unsigned gaw_sprite_writes[32768][8],gaw_sprite_count,gaw_sprite_enabled,gaw_sprite_errors;
__declspec(dllexport) void gaw_sprite_reset(unsigned enabled) {gaw_sprite_count=gaw_sprite_errors=0;gaw_sprite_enabled=enabled;}
__declspec(dllexport) unsigned gaw_sprite_size(void) {return gaw_sprite_count;}
__declspec(dllexport) unsigned gaw_sprite_error(void) {return gaw_sprite_errors;}
__declspec(dllexport) const unsigned *gaw_sprite_data(void) {return &gaw_sprite_writes[0][0];}
static void gaw_sprite_write(unsigned value) {
 unsigned *p;if(!gaw_sprite_enabled || (code&15)!=1) return;
 if(gaw_sprite_count==32768) {gaw_sprite_errors++;return;}
 p=gaw_sprite_writes[gaw_sprite_count++];p[0]=m68k.cycles;p[1]=addr;p[2]=value;p[3]=m68k_get_reg(M68K_REG_PC);p[4]=v_counter;p[5]=code;p[6]=reg[1];p[7]=m68k.cycles-mcycles_vdp;
}

static void gaw_sprite_dma(unsigned cycles,unsigned words) {
 unsigned before=gaw_sprite_count;
 if(!words || dma_type>=2 || addr<0xf400 || addr>=0xf600) return;
 gaw_sprite_write(0x80000000|words);
 if(gaw_sprite_count!=before) {gaw_sprite_writes[before][0]=cycles;gaw_sprite_writes[before][7]=dma_endCycles;gaw_sprite_writes[before][6]=(v_counter+(dma_endCycles-mcycles_vdp)/3420)%lines_per_frame;}
}

'''
def main():
 folder=ROOT/'validation/md-sprite-publish-observer';folder.mkdir(exist_ok=True);engine=ROOT.parents[1]/'work/genesis-plus-gx';path=engine/'core/vdp_ctrl.c';original=path.read_bytes();s=original.decode().replace('\r\n','\n');anchor='void vdp_dma_update(unsigned int cycles)';assert s.count(anchor)==1;s=s.replace(anchor,OBSERVER+'\n'+anchor,1)
 s=s.replace('  dma_endCycles = cycles + dma_cycles;', '  dma_endCycles = cycles + dma_cycles;\n  gaw_sprite_dma(cycles,dma_bytes);',1)
 start=s.index('static void vdp_68k_data_w_m5(unsigned int data)\n{');before=s[:start];tail=s[start:];needle='  /* Write data */\n  vdp_bus_w(data);';assert needle in tail;tail=tail.replace(needle,'  gaw_sprite_write(data);\n'+needle,1);modified=(before+tail).encode()
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_sprite_publish_libretro.dll'],cwd=ROOT,capture_output=True,text=True);(folder/'build.log').write_text(result.stdout+result.stderr);assert not result.returncode,result.stdout+result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original;(folder/'original.snapshot').write_bytes(original);(folder/'modified.snapshot').write_bytes(modified);dll=engine/'genesis_plus_gx_sprite_publish_libretro.dll';(folder/'observer.dll').write_bytes(dll.read_bytes());(folder/'build.json').write_text(json.dumps(dict(original_sha256=sha(original),modified_sha256=sha(modified),dll_sha256=sha(dll.read_bytes()),restored=True),indent=2)+'\n');print('Native VRAM publication observer built; original restored.')
if __name__=='__main__':main()
