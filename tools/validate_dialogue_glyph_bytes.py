"""Exhaustive glyph-row bytes versus the previous production pixel renderer."""
import ctypes as c,json,os,re,subprocess
from run_core import ROOT
from archive_lossless_evidence import sha

def function(text):
    start=text.index('static void draw_dialog_glyph(u16 x,u16 y,u16 index)\n{')
    return text[start:text.index('\n/* 7447',start)]

def main():
    folder=ROOT/'validation/dialogue-glyph-v0222';folder.mkdir(exist_ok=True)
    previous=subprocess.check_output(['git','show','9737d07:megadrive/src/main.c'],cwd=ROOT).decode().replace('\r\n','\n')
    old=function(previous);new=function((ROOT/'megadrive/src/main.c').read_text())
    code='''#include <string.h>
typedef unsigned char u8;typedef unsigned short u16;
static u8 memory[1072],*scratch=memory+16,dialog_font[10];
'''+old.replace('draw_dialog_glyph','reference')+new+'''
unsigned glyph_cases,glyph_failures,glyph_bad_x,glyph_bad_y,glyph_bad_bits;
unsigned check(void) {
 u8 initial[1072],expected[1072];unsigned bits,x,y,n;
 glyph_cases=glyph_failures=0;
 for(n=0;n<1072;n++) initial[n]=(n*79+(n>>2)*13)^0x55;
 for(bits=0;bits<256;bits++) {
  memset(dialog_font,bits,10);
  for(x=0;x<216;x++) for(y=0;y<=30;y++) {
   memcpy(memory,initial,1072);reference(x,y,0);memcpy(expected,memory,1072);
   memcpy(memory,initial,1072);draw_dialog_glyph(x,y,0);glyph_cases++;
   if(memcmp(expected,memory,1072)) {glyph_failures++;glyph_bad_x=x;glyph_bad_y=y;glyph_bad_bits=bits;return 0;}
  }
 }
 return 1;
}
'''
    source=folder/'glyph.c';source.write_text(code)
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    command=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',str(source),'-o',str(folder/'glyph.dll')]
    built=subprocess.run(command,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'glyph.dll'));assert dll.check(),[c.c_uint.in_dll(dll,n).value for n in ['glyph_bad_x','glyph_bad_y','glyph_bad_bits']]
    count=c.c_uint.in_dll(dll,'glyph_cases').value;assert count==256*216*31
    result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),passed=True,cases=count,reference_commit='9737d07',reference_function_sha256=sha(old.encode()),optimized_function_sha256=sha(new.encode()),compared_bytes_per_case=1072,scope='Host compilation of exact old/new production glyph functions. All256 row-byte values at216 X and31 Y positions, over existing nonzero bitmap pixels and16-byte guards. Includes right-edge spill clipping. All ten rows have the same chosen byte; source-ROM glyph selection and actual68000 integration are separate production-ROM checks.')
    (ROOT/'analysis/dialogue_glyph_bytes_v0222_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
