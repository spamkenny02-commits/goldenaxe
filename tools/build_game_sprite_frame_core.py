"""Read-only full frame checkpoints, actual SAT OUTI and PSG port dates."""
import hashlib,json,subprocess,sys
from actor_reference import ROOT
OBSERVER=r'''
typedef struct {unsigned pc,master,raster,refresh,iff,tag,de;unsigned char ram[932];} GawFramePoint;
static GawFramePoint gaw_frame_points[1024];static unsigned gaw_frame_size,gaw_frame_active,gaw_frame_sp,gaw_frame_error,gaw_frame_instruction_start;
static unsigned gaw_frame_ports[8192][5],gaw_frame_port_size;
__declspec(dllexport) unsigned gaw_frame_count(void) {return gaw_frame_size;}
__declspec(dllexport) unsigned gaw_frame_errors(void) {return gaw_frame_error;}
__declspec(dllexport) const void *gaw_frame_data(void) {return gaw_frame_points;}
__declspec(dllexport) unsigned gaw_frame_port_count(void) {return gaw_frame_port_size;}
__declspec(dllexport) const void *gaw_frame_port_data(void) {return gaw_frame_ports;}
__declspec(dllexport) void gaw_frame_reset(unsigned drain) {gaw_frame_size=gaw_frame_port_size=gaw_frame_error=0;if(!drain) {gaw_frame_active=0;gaw_timing_reset();}}
void gaw_frame_port(unsigned cycles,unsigned value,unsigned kind) {
 unsigned *p,pc=Z80.pc.w.l;
 if(!gaw_frame_active || (kind==2 && (work_ram[0x1fff]!=4 || pc<0x8002 || pc>0x8100))) return;
 if(gaw_frame_port_size==8192) {gaw_frame_error=1;return;}
 p=gaw_frame_ports[gaw_frame_port_size++];p[0]=kind;p[1]=(unsigned)gaw_elapsed+(cycles-gaw_frame_instruction_start);p[2]=value;p[3]=pc;p[4]=work_ram[0]|((unsigned)work_ram[1]<<8);
}
static void gaw_frame_observe(unsigned pc) {
 GawFramePoint *p;unsigned n;unsigned char *to;long long raster;
 gaw_frame_instruction_start=Z80.cycles;
 if(pc==0x938) {gaw_frame_active=1;gaw_frame_sp=SP;}
 if(!gaw_frame_active) return;
 if(pc>=0xc100 && pc<0xc300 && SP==((gaw_frame_sp+2)&65535) && z80_readmap[pc>>10][pc&1023]==0xf3) {pc=65535;gaw_frame_active=0;}
 else if(pc!=0x938 && pc!=0xb95 && pc!=0xbb3 && pc!=0x137) return;
 if(gaw_frame_size==1024) {gaw_frame_error=1;return;}
 p=gaw_frame_points+gaw_frame_size++;p->pc=pc;p->master=(unsigned)gaw_elapsed;
 raster=(long long)v_counter*3420+(int)(Z80.cycles-mcycles_vdp);while(raster<0) raster+=(long long)lines_per_frame*3420;
 p->raster=raster%((long long)lines_per_frame*3420);p->refresh=(R&127)|(R2&128);p->iff=IFF1;p->tag=work_ram[0]|((unsigned)work_ram[1]<<8);p->de=DED;to=p->ram;
 memcpy(to,work_ram,80);to+=80;*to++=work_ram[0x303];memcpy(to,work_ram+0x1100,128);to+=128;
 for(n=0;n<32;n++) {memcpy(to,work_ram+0x300+n*48+0x1b,2);to+=2;}
 memcpy(to,work_ram+0x1d00,256);to+=256;memcpy(to,work_ram+0x1e00,400);to+=400;*to++=work_ram[0x1fff];memset(to,0,2);
}
'''
def main():
 folder=ROOT/'validation/game-sprite-frame-observer';folder.mkdir(parents=True,exist_ok=True);engine=ROOT.parents[1]/'work/genesis-plus-gx';paths=[engine/'core/z80/z80.c',engine/'core/memz80.c'];original=[p.read_bytes() for p in paths];z80=original[0].decode();mem=original[1].decode()
 anchor='void z80_run(unsigned int cycles)';assert z80.count(anchor)==1;z80=z80.replace(anchor,OBSERVER+'\n'+anchor);anchor='gaw_timing_observe(pc);EXEC_INLINE(op,ROP());';assert z80.count(anchor)==1;z80=z80.replace(anchor,'gaw_frame_observe(pc);'+anchor)
 for call,kind in [('psg_write(Z80.cycles, data);',1),('vdp_z80_data_w(data);',2)]:
  assert mem.count(call)==5;mem=mem.replace(call,'gaw_frame_port(Z80.cycles,data,'+str(kind)+');'+call)
 mem='void gaw_frame_port(unsigned,unsigned,unsigned);\n'+mem;modified=[z80.encode(),mem.encode()]
 try:
  for p,raw in zip(paths,modified):(folder/(p.name+'.snapshot')).write_bytes(raw);p.write_bytes(raw)
  result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_game_sprite_frame_libretro.dll'],cwd=ROOT,capture_output=True,text=True);(folder/'build.log').write_text(result.stdout+result.stderr);assert not result.returncode,result.stdout+result.stderr
 finally:
  for p,raw in zip(paths,original):p.write_bytes(raw)
 assert all(p.read_bytes()==raw for p,raw in zip(paths,original));core=engine/'genesis_plus_gx_game_sprite_frame_libretro.dll'
 report=dict(original_sha256={p.name:hashlib.sha256(b).hexdigest() for p,b in zip(paths,original)},modified_sha256={p.name:hashlib.sha256(b).hexdigest() for p,b in zip(paths,modified)},core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),restored=True,point_bytes=960,port_bytes=20);(folder/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
