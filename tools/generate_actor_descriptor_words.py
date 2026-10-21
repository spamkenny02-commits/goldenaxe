"""Predecode every overlapping little-endian word of the immutable actor bank."""
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def descriptor_bytes():
    raw=(ROOT/'input/original.sms').read_bytes()[0x30000:0x320ea]
    text=(ROOT/'megadrive/src/actor_data.c').read_text().split('const u8 actor_descriptors[] = {',1)[1].split('};',1)[0]
    exported=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',text));assert exported==raw
    return raw

def main():
    raw=descriptor_bytes();words=[int.from_bytes(raw[n:n+2],'little') for n in range(len(raw)-1)]
    lines=['/* Generated from SMS bank12. Includes odd-byte word addresses. */',f'#define ACTOR_DESCRIPTOR_WORD_COUNT {len(words)}','static const u16 actor_descriptor_words[ACTOR_DESCRIPTOR_WORD_COUNT] = {']
    lines+=['    '+','.join(f'0x{w:04x}' for w in words[n:n+12])+',' for n in range(0,len(words),12)];lines+=['};']
    path=ROOT/'megadrive/src/actor_descriptor_words.inc';data=('\r\n'.join(lines)+'\r\n').encode('ascii')
    if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
    print(len(words),'source descriptor words predecoded, including odd offsets.')

if __name__=='__main__':main()
