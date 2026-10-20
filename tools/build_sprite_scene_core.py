"""Read-only instruction boundary snapshots of original0938, standalone DLL."""
import hashlib,json,subprocess,sys
from actor_reference import ROOT
OBSERVER=r'''
typedef struct {unsigned pc,lo,raster,refresh,iff,tag;unsigned char ram[584];} GawSpritePoint;
static GawSpritePoint gaw_sprite_points[8192];
static unsigned gaw_sprite_size,gaw_sprite_active,gaw_sprite_sp,gaw_sprite_error;
__declspec(dllexport) unsigned gaw_sprite_count(void) {return gaw_sprite_size;}
__declspec(dllexport) unsigned gaw_sprite_errors(void) {return gaw_sprite_error;}
__declspec(dllexport) const void *gaw_sprite_data(void) {return gaw_sprite_points;}
__declspec(dllexport) void gaw_sprite_reset(unsigned drain) {
 gaw_sprite_size=gaw_sprite_error=0;
 if(!drain) {gaw_sprite_active=0;gaw_timing_reset();}
}
static void gaw_sprite_save(unsigned pc) {
 GawSpritePoint *p;unsigned n;unsigned char *to;long long raster;
 if(gaw_sprite_size==8192) {gaw_sprite_error=1;return;}
 p=gaw_sprite_points+gaw_sprite_size++;p->pc=pc;
 p->lo=(unsigned)gaw_elapsed;
 raster=(long long)v_counter*3420+(int)(Z80.cycles-mcycles_vdp);
 while(raster<0) raster+=(long long)lines_per_frame*3420;
 p->raster=(unsigned)(raster%((long long)lines_per_frame*3420));
 p->refresh=(R&127)|(R2&128);p->iff=IFF1;
 p->tag=work_ram[0]|((unsigned)work_ram[1]<<8);to=p->ram;
 memcpy(to,work_ram+0x24,4);to+=4;*to++=work_ram[0x303];
 memcpy(to,work_ram+0x1100,128);to+=128;
 for(n=0;n<32;n++) {memcpy(to,work_ram+0x300+n*48+0x1b,2);to+=2;}
 memcpy(to,work_ram+0x1d40,192);to+=192;
 memcpy(to,work_ram+0x1f00,192);to+=192;
 memset(to,0,3);
}
static void gaw_sprite_observe(unsigned pc) {
 if(pc==0x0938) {gaw_sprite_active=1;gaw_sprite_sp=SP;}
 if(gaw_sprite_active && pc>=0x0938 && pc<=0x0a71) gaw_sprite_save(pc);
}
static void gaw_sprite_after(void) {
 if(gaw_sprite_active && SP==((gaw_sprite_sp+2)&65535) && (PCD<0x0938 || PCD>0x0a71)) {
  gaw_sprite_save(65535);gaw_sprite_active=0;
 }
}
'''
def main():
 folder=ROOT/'validation/sprite-scene-observer';folder.mkdir(parents=True,exist_ok=True)
 path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c';original=path.read_bytes();source=original.decode()
 anchor='void z80_run(unsigned int cycles)';assert source.count(anchor)==1
 source=source.replace(anchor,OBSERVER+'\n'+anchor)
 anchor='gaw_timing_observe(pc);EXEC_INLINE(op,ROP());';assert source.count(anchor)==1
 source=source.replace(anchor,'gaw_sprite_observe(pc);'+anchor)
 anchor='if(gaw_irq_active && SP==gaw_irq_sp[gaw_irq_active-1]) gaw_irq_active--;';assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'gaw_sprite_after();')
 modified=source.encode();(folder/'z80-sprite-observer.txt').write_bytes(modified)
 try:
  path.write_bytes(modified);result=subprocess.run([sys.executable,str(ROOT/'tools/build_timing_core.py'),'--target','genesis_plus_gx_spritescene_libretro.dll'],cwd=ROOT,capture_output=True,text=True)
  (folder/'build.log').write_text(result.stdout+result.stderr);assert not result.returncode,result.stdout+result.stderr
 finally:path.write_bytes(original)
 assert path.read_bytes()==original
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_spritescene_libretro.dll'
 report=dict(original_source_sha256=hashlib.sha256(original).hexdigest(),observer_source_sha256=hashlib.sha256(modified).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),source_restored=True,record_bytes=608)
 (folder/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
