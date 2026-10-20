"""Review native descriptor preparation and optionally rebuild the legacy control."""
import argparse,gzip,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-grant-native-prep','class0-refresh-native-prep','class0-refresh-native-prep-proof']
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 archive=ROOT/'analysis/md-psg-native-prep-v0203';manifest=None
 def read(path):
  nonlocal manifest
  if path.exists():return path.read_bytes()
  if manifest is None:manifest=json.loads((archive/'manifest.json').read_bytes())
  name=path.relative_to(ROOT).as_posix();item=manifest['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
  raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes'];return raw
 parser=argparse.ArgumentParser();parser.add_argument('--build-control',action='store_true');args=parser.parse_args()
 control=ROOT/'validation/md-psg-native-prep-control'
 if args.build_control:
  assert not control.exists();control.mkdir();shutil.copytree(ROOT/'validation/md-z80-psg-class0-refresh-native-prep/src',control/'src')
  p=control/'src/md_z80_psg.c';b=p.read_bytes();assert b.count(b'#define MD_PSG_NATIVE_PREP 1')==1;p.write_bytes(b.replace(b'#define MD_PSG_NATIVE_PREP 1',b'#define MD_PSG_NATIVE_PREP 0'))
  sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];temp=control/'compiler-tmp';temp.mkdir()
  for key in ['TMPDIR','TMP','TEMP']:env[key]=temp.as_posix()
  path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
  built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=control,env=env,capture_output=True,text=True)
  (control/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
 legacy=json.loads((ROOT/'analysis/md_z80_psg_class0_hidden_production_report.json').read_bytes());control_sha=sha(read(control/'out/release/rom.bin'));assert control_sha==legacy['kernel_sha256'],(control_sha,legacy['kernel_sha256'])
 rows=[]
 for variant in VARIANTS:
  folder=ROOT/('validation/md-z80-psg-'+variant);r=json.loads((ROOT/('analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json')).read_bytes())
  kernel=read(folder/'out/release/rom.bin');assert sha(kernel)==r['kernel_sha256']
  binary=folder/'out/release/rom.out';restored=not binary.exists()
  if restored:
   raw=read(binary);binary=folder/'recovered-codegen.out';assert not binary.exists();binary.write_bytes(raw)
  s=subprocess.check_output([str(ROOT.parents[1]/'work/sgdk/bin/objdump.exe'),'-d',str(binary)],text=True)
  if restored:
   assert sha(binary.read_bytes())==sha(raw);binary.unlink()
  s=s.replace(str(binary),str(folder/'out/release/rom.out'))
  (folder/'reviewed-disassembly.txt').write_text(s)
  a=s.index('<cooperative_packet>:');end=s.find('\n\n',a);part=s[a:end];assert '<__mulsi3>' not in part
  lines=part.splitlines();copies=[];verified=0
  for line in lines:
   match=re.match(r'\s*([0-9a-f]+):\t([0-9a-f ]+)\t',line)
   if match:
    address=int(match[1],16);code=bytes.fromhex(match[2]);assert kernel[address:address+len(code)]==code;verified+=1
  assert verified>500
  for i in range(len(lines)-3):
   group=[re.search(r'movel %(fp|a[0-7])@\((\d+)\),%sp@\((\d+)\)',line) for line in lines[i:i+4]]
   if all(group) and len(set(m[1] for m in group))==1 and [int(m[2]) for m in group]==[12,16,20,24]:
    destinations=[int(m[3]) for m in group]
    assert destinations==list(range(destinations[0],destinations[0]+16,4)) and destinations[0]%2==0
    copies.append(lines[i:i+4])
  assert len(copies)==2 and re.search(r'muluw %d[0-7],%d[0-7]',part)
  rows.append(dict(variant=variant,kernel_sha256=r['kernel_sha256'],disassembly_sha256=sha(s.encode()),packet_instruction_records_bound_to_rom=verified,packet_mulsi3_calls=0,payload_long_copy_paths=copies,word_aligned_destination=True))
 output=dict(legacy_control_kernel_sha256=control_sha,legacy_reference_kernel_sha256=legacy['kernel_sha256'],legacy_control_identical=True,source_sha256=sha((ROOT/'megadrive/src/md_z80_psg.c').read_bytes()),results=rows,limits=['Compiled native preparation uses four long copies and hardware16x16 multiply; unchanged legacy control reproduces the archived kernel byte-for-byte. This is code-generation evidence, not whole-game CPU speed or a hard publication-deadline guarantee.'])
 (ROOT/'analysis/md_psg_native_prep_codegen_report.json').write_text(json.dumps(output,indent=2)+'\n');print('Legacy control identical; all three optimized kernels use four long copies and no general multiply helper in the publisher.')
if __name__=='__main__':main()
