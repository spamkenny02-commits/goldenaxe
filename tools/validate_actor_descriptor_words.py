"""Exact old/new C word reads, plus every native table word in the playable ROM."""
import ctypes,json,os,re,subprocess
from run_core import ROOT
from archive_lossless_evidence import sha
from generate_actor_descriptor_words import descriptor_bytes

def main():
    raw=descriptor_bytes();rom=(ROOT/'input/original.sms').read_bytes();current=(ROOT/'megadrive/src/actors.c').read_text();old=subprocess.check_output(['git','show','b8bacbe:megadrive/src/actors.c'],cwd=ROOT).decode().replace('\r\n','\n')
    def function(text):
        marker='static __attribute__((noinline,cold)) u16 descriptor_word_fallback' if 'descriptor_word_fallback' in text else 'static u16 descriptor_word(u16 address)\n{'
        a=text.index(marker);return text[a:text.index('\n/* 09EE',a)]
    version=next(e['version'] for e in json.loads((ROOT/'versions/index.json').read_bytes()) if e['sha256']==sha((ROOT/'gaw-megadrive.bin').read_bytes()))
    folder=ROOT/f'validation/actor-descriptor-v{version:04d}';folder.mkdir(exist_ok=True)
    padded=raw+bytes((n*73+19)&255 for n in range(0x4001-len(raw)))
    def array(name,data):return 'static const u8 '+name+'[] = {'+','.join(str(v) for v in data)+'};\n'
    code='#include <stdint.h>\ntypedef uint8_t u8;typedef uint16_t u16;\n#include "actor_descriptor_words.inc"\n'+array('actor_descriptors',padded)+array('gem_descriptor_data',rom[0x2acd:0x2add])+array('world_axe_descriptors',rom[0x3d8d:0x3da5])
    code+=function(old).replace('descriptor_word','reference_word')+function(current)
    code+='\nunsigned check(void) {unsigned a;for(a=0;a<65536;a++)if(reference_word(a)!=descriptor_word(a))return a+1;return 0;}\n'
    source=folder/'words.c';source.write_text(code);env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-I',str(ROOT/'megadrive/src'),str(source),'-o',str(folder/'words.dll')],env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=ctypes.CDLL(str(folder/'words.dll'));assert dll.check()==0
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    expected=b''.join(int.from_bytes(raw[n:n+2],'little').to_bytes(2,'big') for n in range(len(raw)-1));production=(ROOT/'gaw-megadrive.bin').read_bytes();a=sy['actor_descriptor_words'];assert production[a:a+len(expected)]==expected
    result=dict(md_sha256=sha(production),passed=True,reference_commit='b8bacbe',compiled_c_addresses_exact=65536,native_rom_words_verified=len(raw)-1,native_rom_table_bytes=len(expected),source_files={name:sha((ROOT/name).read_bytes()) for name in ['megadrive/src/actors.c','megadrive/src/actor_descriptor_words.inc','tools/generate_actor_descriptor_words.py','build.ps1']},scope='Exact old/new C helpers compiled on host for every16-bit address. Padding beyond the exported bank gives defined test-only fallback reads; it does not make invalid production addresses valid. Every overlapping word of the real8426-byte source bank, including odd offsets, is verified in native68000 byte order in the playable ROM. Special gem/axe paths are included. Actual scene execution is checked separately.')
    (ROOT/f'analysis/actor_descriptor_words_v{version:04d}_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
