"""Compile native C RNG for host and68000; verify recurrence and refresh arithmetic."""
import ctypes as c,hashlib,json,os,subprocess
from actor_reference import ROOT
from source_rng_reference import source_rng
from source_rng_refresh import advance_refresh

def main():
 folder=ROOT/'validation/native-source-rng';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve();source=ROOT/'megadrive/src/source_rng.c';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];logs=[]
 commands=[['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),str(source),'-o',str(folder/'source_rng.dll')]]
 for suffix,mode in [('o','-c'),('s','-S')]:commands.append([str(sdk/'bin/gcc.exe'),'-B'+str(sdk/'bin')+'/', '-m68000','-O3','-Wall','-Wextra','-Werror','-I',str(sdk/'inc'),mode,str(source),'-o',str(folder/f'source_rng.{suffix}')])
 for args in commands:
  result=subprocess.run(args,env=env,capture_output=True,text=True);logs.append(result.stdout+result.stderr);assert result.returncode==0,(args,result.stderr)
 (folder/'compile.log').write_text('\n'.join(logs));dll=c.CDLL(str(folder/'source_rng.dll'))
 dll.source_rng_next_seed.argtypes=[c.c_uint16];dll.source_rng_next_seed.restype=c.c_uint16
 dll.source_rng_value.argtypes=[c.c_uint16,c.c_uint8];dll.source_rng_value.restype=c.c_uint8
 dll.source_refresh_advance.argtypes=[c.c_uint8,c.c_uint32];dll.source_refresh_advance.restype=c.c_uint8
 for seed in range(65536):assert dll.source_rng_next_seed(seed)==source_rng(seed,0)['seed'],seed
 output_cases=0
 for high in [0,0x8000,0xff00]:
  for low in range(256):
   for refresh in range(256):assert dll.source_rng_value(high|low,refresh)==refresh^low;output_cases+=1
 counts=list(range(256))+[256,65535,65536,0x80000000,0xffffffff]
 for refresh in range(256):
  for fetches in counts:assert dll.source_refresh_advance(refresh,fetches)==advance_refresh(refresh,fetches),(refresh,fetches)
 report=dict(seed_cases=65536,output_cases=output_cases,refresh_cases=256*len(counts),compiled_68000=True,executed_68000=False,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),object_sha256=hashlib.sha256((folder/'source_rng.o').read_bytes()).hexdigest(),production_ROM_changed=False,production_RNG_replaced=False,limits=['Native helper C tested on host andcross-compiled with SGDK68000 compiler. Clock integration is deliberately absent:sampled R must come from verified instruction timing,not MD frame/random approximation.'])
 (ROOT/'analysis/native_source_rng_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Native RNG C:',65536,'seeds,',output_cases,'outputs,',256*len(counts),'refresh cases exact;68000 compilation passed')
if __name__=='__main__':main()
