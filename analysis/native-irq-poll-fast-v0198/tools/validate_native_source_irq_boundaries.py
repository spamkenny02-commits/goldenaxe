"""Native IRQ rejection contracts and instruction-audited reset handoff."""
import ctypes as c
import hashlib
import json
from actor_reference import ROOT
from validate_native_source_irq import compile_helper,Input,Output
from validate_native_audio_prefix import Work


def main():
    folder,dll,function=compile_helper();rows=[]
    base=bytearray(336);base[0x2e]=1;base[0x33]=1;base[0x34:0x36]=bytes([0,0xdd])
    definitions=[('lines',Input(0,263,0,0,16,0),{},Work(500,50)),
                 ('raster',Input(262*3420,262,0,0,16,0),{},Work(500,50)),
                 ('joy',Input(0,262,0,64,16,0),{},Work(500,50)),
                 ('reset-mask',Input(0,262,0,0,1,0),{},Work(500,50)),
                 ('tile-zero',Input(0,262,0,0,16,0),{0x42:4},Work(500,50)),
                 ('tile-large',Input(0,262,257,0,16,0),{0x42:4},Work(500,50)),
                 ('tile-bank',Input(0,262,1,0,16,0),{0x42:16},Work(500,50)),
                 ('tile-RAM',Input(0,262,1,0,16,0),{0x42:4,0x44:0xc0},Work(500,50)),
                 ('queue-pointer',Input(0,262,0,0,16,0),{0x34:0x50,0x35:0xc0},Work(500,50)),
                 ('queue-extent',Input(0,262,0,0,16,0),{0x34:255,**{80+i:1 for i in range(256)}},Work(500,50)),
                 ('reader-T-overflow',Input(0,262,0,0,16,0),{},Work(0xffffffff,50)),
                 ('reader-M1-overflow',Input(0,262,0,0,16,0),{},Work(500,0xffffffff))]
    for kind,entry,patches,reader in definitions:
        before=bytearray(base)
        for offset,value in patches.items():before[offset]=value
        state=(c.c_uint8*336).from_buffer_copy(before);output=Output()
        assert not function(state,c.byref(entry),c.byref(reader),c.byref(output)),kind
        assert bytes(state)==before and not output.whole.tstates and not output.whole.fetches,kind
        assert not output.palette_taken and not output.reset_requested and all(not s.tstates and not s.fetches for s in output.stages)
        rows.append(dict(kind=kind,rejected=True,all336_bytes_preserved=True))
    resets=[]
    for delay in [0,1,255]:
        before=bytearray(base);before[0x30]=delay;before[0x1c]=2;before[0x2f]=255
        reader=Work(500,50);normal=Output();state=(c.c_uint8*336).from_buffer_copy(before);entry=Input(0,262,0,17,16,0)
        assert function(state,c.byref(entry),c.byref(reader),c.byref(normal))
        output=Output();state=(c.c_uint8*336).from_buffer_copy(before);entry.reset_mask=0
        assert function(state,c.byref(entry),c.byref(reader),c.byref(output)) and output.reset_requested
        assert state[0x30]==delay and state[0x2e]==1 and state[0x2f]==255 and state[0x1c]==1 and state[0x20]==17
        # Original01CC JP009A occurs before17T delay load/test, its branch,
        # 48T counter/gate/POP tail and10T RET. Reset target itself excluded.
        assert output.whole.tstates==normal.whole.tstates-(99 if delay else 87)
        assert output.whole.fetches==normal.whole.fetches-(11 if delay else 9)
        resets.append(dict(delay=delay,reset_handoff=True,whole_T=output.whole.tstates,whole_M1=output.whole.fetches))
    report=dict(rejections=rows,resets=resets,irq_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_irq.c').read_bytes()).hexdigest(),
                limits=['Host C rollback contracts and opcode-audited JP009A handoff. Reset branch not directly exercised in source captures; reset target execution not translated here.'])
    (ROOT/'analysis/native_source_irq_boundaries_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'rejections and',len(resets),'instruction-audited reset handoffs passed')


if __name__=='__main__':main()
