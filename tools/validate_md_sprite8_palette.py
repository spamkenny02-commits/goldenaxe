"""Independent MD palette swatches for sprite RGB comparisons."""
import hashlib,json,os,re,subprocess
from pathlib import Path
from PIL import Image
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 folder=ROOT/'validation/md-sprite8-palette';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
 baseline=json.loads((ROOT/'analysis/md_z80_psg_class0_refresh_native_prep_report.json').read_bytes());ref=baseline['results'][0];region=ref['region'];cram=(ROOT/('validation/md-z80-psg-class0-refresh-native-prep/'+region+'-plain')/f"cram_{ref['frame']:05d}.bin")
 # Reference binaries were losslessly archived; read their verified payload.
 if cram.exists():raw=cram.read_bytes()
 else:
  import gzip
  archive=ROOT/'analysis/md-psg-native-prep-v0203';m=json.loads((archive/'manifest.json').read_bytes());item=m['compressed'][cram.relative_to(ROOT).as_posix()];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256']
 packed=[int.from_bytes(raw[n*2:n*2+2],'little') for n in range(16,32)]
 palette=[((v&0x1c0)<<3)|((v&0x38)<<2)|((v&7)<<1) for v in packed]
 main='#include <genesis.h>\nstatic const u16 colors[]={'+','.join(map(str,palette))+'};\n'+r'''
static u32 patterns[128];volatile u16 gaw_done;
int main(bool reset) {
 u16 n,row;(void)reset;SYS_disableInts();VDP_setEnable(FALSE);VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setPlaneSize(64,32,TRUE);
 for(n=0;n<16;n++) for(row=0;row<8;row++) patterns[n*8+row]=(u32)n*0x11111111UL;
 VDP_loadTileData(patterns,16,16,CPU);PAL_setColors(16,colors,16,CPU);
 for(n=0;n<16;n++) VDP_setTileMapXY(BG_A,0x2000|(16+n),n,2);
 VDP_setEnable(TRUE);gaw_done=1;while(TRUE) __asm__ volatile("nop");return 0;
}
'''
 (src/'main.c').write_text(main);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];temp=folder/'compiler-tmp';temp.mkdir(exist_ok=True)
 for key in ['TMPDIR','TMP','TEMP']:env[key]=temp.as_posix()
 path=sdk.as_posix();unix='/'+path[0].lower()+path[2:];built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-1500:]
 symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+) \w (.+)',line))};rows=[]
 for region in ['ntsc','pal']:
  run(folder/'out/release/rom.bin',100,folder/region,{100},[],skip_intro=False,core_options={'genesis_plus_gx_region_detect':region})
  v=(folder/region/'vram_00100.bin').read_bytes();v=bytes(v[n^1] for n in range(65536));regs=(folder/region/'vdp_regs_00100.bin').read_bytes();base=(regs[2]&0x38)<<10;cram=(folder/region/'cram_00100.bin').read_bytes();image=Image.open(folder/region/'frame_00100.png').convert('RGB')
  assert not regs[12]&9 and regs[1]&64
  assert [int.from_bytes(cram[n*2:n*2+2],'little') for n in range(16,32)]==packed
  for n in range(16):
   assert v[(16+n)*32:(17+n)*32]==(n*0x11111111).to_bytes(4,'big')*8
   assert int.from_bytes(v[base+(2*64+n)*2:base+(2*64+n)*2+2],'big')==(0x2000|(16+n))
  ram=(folder/region/'ram_00100.bin').read_bytes();address=symbols['gaw_done']&65535;assert bytes(ram[(address+n)^1] for n in range(2))==b'\0\1'
  rows.append(dict(region=region,palette_packed=packed,colors=[image.getpixel((n*8+4,20)) for n in range(16)],image_sha256=sha((folder/region/'frame_00100.png').read_bytes())))
 report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),source_sha256=sha((src/'main.c').read_bytes()),results=rows,limits=['Independent calibration ROM with native-computed solid nibble tiles and exact same packed PAL1 colors. Main sprite fixture legend is excluded from RGB proof because its prototype generator used decimal digits for nibble10..15; future generator is fixed. This calibrates physical RGB only, not sprite geometry or gameplay.'])
 (ROOT/'analysis/md_sprite8_palette_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Independent PAL1 colors validated in PAL/NTSC.')
if __name__=='__main__':main()
