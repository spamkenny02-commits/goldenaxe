"""First page of opening text, using the proportional ROM font (0524..07EE)."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def first_page(rom,name):
    text=rom[0xeb68:rom.index(0,0xeb68)].replace(b'%',name)
    charset=rom[0xc8d6:0xc995]; widths=rom[0xc995:0xca54]
    bitmap=bytearray(0x410); x=0; y=0; lines=[]; line=b''
    def index(value):
        n=charset.rfind(bytes([value])); assert n>=0
        if 0x88<=n<0xbf: n-=0x37
        return n
    for word in text.split(b' '):
        word_width=sum(widths[index(value)]+1 for value in word)
        if x+word_width>=208:
            lines.append(line); line=b''; x=0; y+=10
            if y>=40: break
        for value in word:
            n=index(value)
            for row in range(10):
                bits=rom[0xc000+n*10+row]
                for column in range(8):
                    if bits&(128>>column):
                        xx=x+column
                        if xx<208: bitmap[(xx//8)*40+y+row]|=128>>(xx&7)
            x+=widths[n]+1
        line+=word+b' '; x+=6
    (ROOT/'analysis/dialogue_first_page.bitmap.bin').write_bytes(bitmap)
    return bitmap,lines+[line]

if __name__=='__main__':
    rom=(ROOT/'input/original.sms').read_bytes(); bitmap,lines=first_page(rom,b'A')
    source=(ROOT/'validation/sms-dialogue/ram_02000.bin').read_bytes()[0x1100:0x1510]
    differences=sum(a!=b for a,b in zip(bitmap,source))
    print('first page lines:',lines,'bitmap byte differences:',differences)
    assert differences==0
