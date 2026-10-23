"""Export ROM-only assets for both 6AFB/6C2E full-screen magic levels."""
import json,hashlib
from pathlib import Path
from extract_title import rle_planes
ROOT=Path(__file__).resolve().parents[1]
def main():
    rom=(ROOT/'input/original.sms').read_bytes();arrays={}
    for level,start in [(1,0x1633b),(2,0x16d48)]:
        buf=bytearray(16384);end,size=rle_planes(rom,start,buf,0,4)
        arrays[f'screen_spell_patterns{level}']=buf[:size]
    arrays['screen_spell_offsets']=bytes((((v-256 if v&128 else v)*2*amplitude)>>8)&255 for amplitude in range(16,25) for v in rom[0x8000:0x8100])
    arrays.update(screen_spell_bank12=rom[0x30000:0x34000],screen_spell_grid=rom[0x6bf6:0x6c22],screen_spell_cells1=rom[0x16293:0x1633b],screen_spell_blocks=rom[0x6cf0:0x6d2c],screen_spell_cells2=rom[0x16800:0x16d48],screen_spell_hero_bitmap=rom[0x12241:0x122d2])
    from full_irq_cost import full_irq_cost
    fixed=[]
    for lines_count in [262,313]:
        state=bytearray(336);state[0x2e]=1;state[0x35]=0xdd
        for comp in [False,True]:
            sat64=sum([27,10,10,3*(16+12),7,13,4,11,7,11,7,10,17,64*16,10])
            sat128=sum([4,11,4,11,17,128*16,10]);before=sat64+sat128+45+70
            prefix=sum([13,4,7,10,13,4,12 if comp else 11]);sample=193*3420+(72+before+prefix+11)*15
            target=(230 if comp else 246)*3420 if lines_count==262 else (224 if comp else 240)*3420
            guard=max(0,(target-sample+404)//405)
            fixed.append(full_irq_cost(rom,state,guard,1,0,16,comp,0)['whole_IRQ_tstates'])
    from screen_spell_cost import multiply_cost
    multiply=[multiply_cost(0,a) for a in range(16,25)]
    lines=['static const u16 screen_spell_multiply_tstates[] = {'+','.join(str(x) for x in multiply)+'};']
    lines+=['static const u16 screen_spell_irq_empty_fixed[] = {'+','.join(str(x) for x in fixed)+'};']
    lines+=['/* Original 30A7/6AFB/6C2E assets; no captured states. */']
    for name,data in arrays.items():
        lines+=['static const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%x for x in data[n:n+16])+',' for n in range(0,len(data),16)]+['};']
    for stage in range(10):
        b=arrays['screen_spell_blocks'][stage*6:stage*6+6];address=int.from_bytes(b[:2],'little');source=int.from_bytes(b[2:4],'little')-0xa800
        assert 0<=source and source+b[4]*b[5]*2<=len(arrays['screen_spell_cells2'])
        for strip in range(4):
            for row in range(b[4]):
                offset=address+strip*16-0xd600+row*64
                if 0<=offset<1280:assert offset+b[5]*2<=1280
        for offset in range(source,source+b[4]*b[5]*2,2):assert int.from_bytes(arrays['screen_spell_cells2'][offset:offset+2],'little')&~0x3ff==0
    words=[int.from_bytes(arrays['screen_spell_cells2'][i:i+2],'little') for i in range(0,len(arrays['screen_spell_cells2']),2)]
    lines+=['static const u16 screen_spell_cells2_md[] = {']+['    '+','.join('0x%04x'%(16+(w&511)+((w&512)<<2)) for w in words[n:n+12])+',' for n in range(0,len(words),12)]+['};']
    raw=('\r\n'.join(lines)+'\r\n').encode();path=ROOT/'megadrive/src/screen_spell_assets.inc'
    if not path.exists() or path.read_bytes()!=raw:path.write_bytes(raw)
    (ROOT/'analysis/screen_spell_assets.json').write_bytes((json.dumps(dict(source_sha256=hashlib.sha256(rom).hexdigest(),arrays={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in arrays.items()},captured_states_used=False,irq_empty_fixed_tstates=fixed,multiply_tstates=multiply),indent=2)+'\n').encode())
    print('Both source full-screen spell assets exported.')
if __name__=='__main__':main()
